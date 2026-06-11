"""
routers/medical.py - Endpoint AI dan Rekam Medis

Prefix dari main.py: "/medical"
Daftar URL:
    POST /medical/transcribe            → upload audio → transkripsi + analisis AI
    POST /medical/simpan-rm             → simpan rekam medis final ke database
    GET  /medical/rekam-medis/{id}      → lihat detail satu rekam medis
"""

import os
import shutil
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

import models
from ai_services import compress_audio, parse_medical_text, transcribe_audio
from database import get_db
from dependencies import get_current_user
from schemas import SimpanRMSchema

router = APIRouter()

# Buat folder penyimpanan sementara file audio jika belum ada
FOLDER_TEMP = "temp_files"
os.makedirs(FOLDER_TEMP, exist_ok=True)


@router.post("/transcribe")
async def transcribe_dan_analisis(
    file: UploadFile = File(...),
    pengguna: models.User = Depends(get_current_user),
):
    """
    Pipeline AI lengkap SmartERM — dari audio mentah ke JSON data medis:
        1. Terima file audio dari HP dokter → simpan ke folder sementara
        2. Kompres file jika ukurannya > 24MB (menggunakan FFmpeg)
        3. Kirim ke Whisper AI → dapatkan teks transkripsi Bahasa Indonesia
        4. Kirim teks ke Llama 3 → dapatkan JSON data medis terstruktur
        5. Hapus file sementara → kembalikan hasil ke dokter untuk diedit

    Setelah dokter mengedit hasilnya di HP, data dikirim ke POST /medical/simpan-rm.
    """
    # Beri nama unik berdasarkan timestamp agar tidak bentrok jika ada upload bersamaan
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    path_temp  = f"{FOLDER_TEMP}/{timestamp}_{file.filename}"
    path_final = path_temp   # Mungkin berubah jika file dikompres

    # Simpan file yang diupload ke disk
    with open(path_temp, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"[UPLOAD] File tersimpan sementara: {path_temp}")

    try:
        path_final       = compress_audio(path_temp)
        teks_transkripsi = transcribe_audio(path_final)
        data_medis       = parse_medical_text(teks_transkripsi)

        return {
            "status":         "success",
            "dokter":         pengguna.nama_lengkap,
            "transkrip_asli": teks_transkripsi,
            "data_medis":     data_medis,
        }

    except Exception as e:
        print(f"[ERROR] Gagal memproses AI: {e}")
        raise HTTPException(status_code=500, detail=f"Gagal memproses AI: {e}")

    finally:
        # File sementara selalu dihapus, baik proses berhasil maupun gagal
        _hapus_file_temp(path_temp, path_final)


@router.post("/simpan-rm")
def simpan_rekam_medis(
    data: SimpanRMSchema,
    db: Session = Depends(get_db),
    pengguna: models.User = Depends(get_current_user),
):
    """
    Simpan rekam medis yang sudah diedit dokter ke database.

    Alur penggunaan:
        1. Dokter merekam audio konsultasi
        2. Upload ke POST /medical/transcribe → dapatkan draft JSON dari AI
        3. Dokter mengedit draft di HP (koreksi data yang salah)
        4. Tekan "Simpan" → data dikirim ke endpoint ini sebagai rekam medis final
    """
    pasien = db.query(models.Pasien).filter(
        models.Pasien.no_rekam_medis == data.no_rekam_medis
    ).first()

    if not pasien:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Pasien dengan No RM '{data.no_rekam_medis}' tidak ditemukan. "
                "Pastikan pasien sudah didaftarkan melalui POST /dokter/pasien."
            ),
        )

    rekam_medis_baru = models.RekamMedis(
        id_pasien=pasien.id_pasien,
        id_dokter=pengguna.id_user,
        status_record="final",

        # Tanda vital
        tekanan_darah=data.tekanan_darah,
        nadi=data.nadi,
        suhu=data.suhu,

        # S — Subjektif
        keluhan_utama=data.keluhan_utama,
        riwayat_penyakit_sekarang=data.riwayat_penyakit_sekarang,
        riwayat_penyakit_keluarga=data.riwayat_penyakit_keluarga,

        # Data kebidanan
        hpht=_parse_tanggal(data.hpht),
        hpl=_parse_tanggal(data.hpl),

        # O, A, P
        pemeriksaan_fisik_lengkap=data.pemeriksaan_fisik_lengkap,
        diagnosa_utama=data.diagnosa_utama,
        rencana_layanan=data.rencana_layanan,
        resep_obat=data.resep_obat,
        edukasi_pasien=data.edukasi_pasien,
    )

    db.add(rekam_medis_baru)
    db.commit()
    db.refresh(rekam_medis_baru)

    return {
        "msg":       "Rekam medis berhasil disimpan.",
        "id_record": rekam_medis_baru.id_record,
        "pasien":    pasien.nama_pasien,
        "dokter":    pengguna.nama_lengkap,
        "waktu":     str(rekam_medis_baru.waktu_pemeriksaan),
    }


@router.get("/rekam-medis/{id_record}")
def get_rekam_medis(
    id_record: int,
    db: Session = Depends(get_db),
    pengguna: models.User = Depends(get_current_user),
):
    """Ambil detail satu rekam medis berdasarkan ID. Berguna untuk review atau mencetak."""
    rm = db.query(models.RekamMedis).filter(
        models.RekamMedis.id_record == id_record
    ).first()

    if not rm:
        raise HTTPException(
            status_code=404,
            detail=f"Rekam medis dengan ID {id_record} tidak ditemukan.",
        )

    return {
        "id_record":         rm.id_record,
        "pasien":            rm.pasien.nama_pasien if rm.pasien else None,
        "no_rekam_medis":    rm.pasien.no_rekam_medis if rm.pasien else None,
        "dokter":            rm.dokter.nama_lengkap if rm.dokter else None,
        "tanggal_lahir":     str(rm.pasien.tanggal_lahir) if rm.pasien and rm.pasien.tanggal_lahir else None,  # ← TAMBAH
        "alamat":            rm.pasien.alamat if rm.pasien else None,  
        "waktu_pemeriksaan": str(rm.waktu_pemeriksaan),
        "status":            rm.status_record,
        "data_medis": {
            "tekanan_darah":             rm.tekanan_darah,
            "nadi":                      rm.nadi,
            "suhu":                      rm.suhu,
            "keluhan_utama":             rm.keluhan_utama,
            "riwayat_penyakit_sekarang": rm.riwayat_penyakit_sekarang,
            "riwayat_penyakit_keluarga": rm.riwayat_penyakit_keluarga,
            "hpht":                      str(rm.hpht) if rm.hpht else None,
            "hpl":                       str(rm.hpl) if rm.hpl else None,
            "pemeriksaan_fisik_lengkap": rm.pemeriksaan_fisik_lengkap,
            "diagnosa_utama":            rm.diagnosa_utama,
            "rencana_layanan":           rm.rencana_layanan,
            "resep_obat":                rm.resep_obat,
            "edukasi_pasien":            rm.edukasi_pasien,
        },
    }


# ─────────────────────────────────────────────
# Fungsi pembantu (private — hanya dipakai di file ini)
# ─────────────────────────────────────────────

def _parse_tanggal(teks_tanggal: Optional[str]) -> Optional[date]:
    """
    Konversi string format YYYY-MM-DD menjadi object date Python.
    Mengembalikan None jika string kosong atau formatnya tidak sesuai —
    tidak melempar exception agar proses simpan tidak crash hanya karena
    satu field tanggal salah format.
    """
    if not teks_tanggal:
        return None
    try:
        return datetime.strptime(teks_tanggal, "%Y-%m-%d").date()
    except ValueError:
        return None


def _hapus_file_temp(path_asli: str, path_kompres: str) -> None:
    if os.path.exists(path_asli):
        os.remove(path_asli)
        print(f"[CLEANUP] File dihapus: {path_asli}")

    # Hapus file hasil kompresi hanya jika berbeda dari file asli
    if path_kompres != path_asli and os.path.exists(path_kompres):
        os.remove(path_kompres)
        print(f"[CLEANUP] File kompresi dihapus: {path_kompres}")