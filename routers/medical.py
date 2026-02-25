"""
routers/medical.py - Endpoint AI (Transkripsi) & Rekam Medis

Ini adalah JANTUNG aplikasi SmartERM:
1. /medical/transcribe  → Audio → Teks → JSON Medis (via AI)
2. /medical/simpan-rm   → Simpan data medis yang sudah diedit dokter ke DB

Prefix dari mainbaru.py: "/medical"
"""

import os
import shutil
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import SimpanRMSchema
from dependencies import get_current_user
from ai_services import compress_audio, transcribe_audio, parse_medical_text

router = APIRouter()

# Folder sementara untuk file audio yang diupload
os.makedirs("temp_files", exist_ok=True)


# =============================================================================
# ENDPOINT UTAMA AI: TRANSCRIBE + PARSING MEDIS
# =============================================================================

@router.post("/transcribe")
async def transcribe_dan_analisis(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user)  # Wajib login
):
    """
    Pipeline lengkap AI SmartERM:
    
    STEP 1: Terima file audio dari HP dokter → simpan sementara
    STEP 2: Cek ukuran file → kompres kalau > 24MB (via FFmpeg)
    STEP 3: Kirim ke Whisper AI → dapat teks transkripsi Bahasa Indonesia
    STEP 4: Kirim teks ke Llama 3 → dapat JSON data medis terstruktur
    STEP 5: Hapus file temp → kembalikan hasil ke dokter
    
    Dokter kemudian mengedit hasilnya di HP, lalu tekan Simpan
    yang akan memanggil endpoint /medical/simpan-rm.
    """
    
    # ------------------------------------------------------------------
    # STEP 1: Simpan file audio yang diupload ke folder temp
    # ------------------------------------------------------------------
    # Beri nama unik berdasarkan timestamp + nama asli file
    # Contoh: "temp_files/20241215_143022_rekaman.m4a"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_filename = f"temp_files/{timestamp}_{file.filename}"

    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    print(f"[UPLOAD] File tersimpan sementara: {temp_filename}")

    # Track path file yang mungkin berubah setelah kompresi
    final_path = temp_filename

    try:
        # ------------------------------------------------------------------
        # STEP 2: Kompresi audio (jika perlu)
        # ------------------------------------------------------------------
        final_path = compress_audio(temp_filename)

        # ------------------------------------------------------------------
        # STEP 3: Transkripsi audio → teks (Whisper AI)
        # ------------------------------------------------------------------
        teks_transkripsi = transcribe_audio(final_path)

        # ------------------------------------------------------------------
        # STEP 4: Parsing teks → JSON medis (Llama 3)
        # ------------------------------------------------------------------
        data_medis = parse_medical_text(teks_transkripsi)

        # ------------------------------------------------------------------
        # STEP 5: Bersihkan file temp
        # ------------------------------------------------------------------
        _hapus_file_temp(temp_filename, final_path)

        # Kembalikan hasil ke dokter untuk direview & diedit
        return {
            "status": "success",
            "dokter": current_user.nama_lengkap,
            "transkrip_asli": teks_transkripsi,   # Teks mentah dari Whisper
            "data_medis": data_medis               # JSON terstruktur dari Llama 3
        }

    except Exception as e:
        # Pastikan file temp selalu dihapus meskipun terjadi error
        _hapus_file_temp(temp_filename, final_path)
        print(f"[ERROR] Gagal proses AI: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Gagal memproses AI: {str(e)}"
        )


# =============================================================================
# ENDPOINT SIMPAN REKAM MEDIS
# =============================================================================

@router.post("/simpan-rm")
def simpan_rekam_medis(
    data: SimpanRMSchema,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)  # Wajib login
):
    """
    Simpan data rekam medis yang sudah diedit dokter ke database.
    
    Alur penggunaan:
    1. Dokter rekam audio konsultasi
    2. Upload ke /medical/transcribe → dapat draft JSON
    3. Dokter edit draft di HP (koreksi yang salah)
    4. Tekan "Simpan" → POST ke /medical/simpan-rm dengan data final
    
    Endpoint ini menerima No RM pasien (bukan ID) karena lebih mudah
    diingat dan diinput oleh dokter.
    """

    # ------------------------------------------------------------------
    # 1. Cari pasien berdasarkan No Rekam Medis
    # ------------------------------------------------------------------
    pasien = db.query(models.Pasien).filter(
        models.Pasien.no_rekam_medis == data.no_rekam_medis
    ).first()

    if not pasien:
        raise HTTPException(
            status_code=404,
            detail=f"Pasien dengan No RM '{data.no_rekam_medis}' tidak ditemukan. "
                   f"Pastikan pasien sudah didaftarkan terlebih dahulu di /dokter/pasien"
        )

    # ------------------------------------------------------------------
    # 2. Simpan rekam medis baru
    # ------------------------------------------------------------------
    rm_baru = models.RekamMedis(
        id_pasien=pasien.id_pasien,
        id_dokter=current_user.id_user,   # Otomatis ambil dari token login
        status_record="final",            # Sudah diedit dokter = final

        # Data Vital
        tekanan_darah=data.tekanan_darah,
        nadi=data.nadi,
        suhu=data.suhu,

        # Data Subjektif
        keluhan_utama=data.keluhan_utama,
        riwayat_penyakit_sekarang=data.riwayat_penyakit_sekarang,
        riwayat_penyakit_keluarga=data.riwayat_penyakit_keluarga,

        # Data Kebidanan
        hpht=_parse_date(data.hpht),
        hpl=_parse_date(data.hpl),

        # Pemeriksaan & Diagnosis
        pemeriksaan_fisik_lengkap=data.pemeriksaan_fisik_lengkap,
        diagnosa_utama=data.diagnosa_utama,
        rencana_layanan=data.rencana_layanan,
        resep_obat=data.resep_obat,
        edukasi_pasien=data.edukasi_pasien
    )

    db.add(rm_baru)
    db.commit()
    db.refresh(rm_baru)

    return {
        "msg": "Rekam Medis berhasil disimpan!",
        "id_record": rm_baru.id_record,
        "pasien": pasien.nama_pasien,
        "dokter": current_user.nama_lengkap,
        "waktu": str(rm_baru.waktu_pemeriksaan)
    }


# =============================================================================
# LIHAT DETAIL REKAM MEDIS
# =============================================================================

@router.get("/rekam-medis/{id_record}")
def get_rekam_medis(
    id_record: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Ambil detail satu rekam medis berdasarkan ID record.
    Berguna untuk review atau cetak rekam medis.
    """
    rm = db.query(models.RekamMedis).filter(models.RekamMedis.id_record == id_record).first()
    if not rm:
        raise HTTPException(status_code=404, detail=f"Rekam medis ID {id_record} tidak ditemukan")

    return {
        "id_record": rm.id_record,
        "pasien": rm.pasien.nama_pasien if rm.pasien else None,
        "no_rekam_medis": rm.pasien.no_rekam_medis if rm.pasien else None,
        "dokter": rm.dokter.nama_lengkap if rm.dokter else None,
        "waktu_pemeriksaan": str(rm.waktu_pemeriksaan),
        "status": rm.status_record,
        "data_medis": {
            "tekanan_darah": rm.tekanan_darah,
            "nadi": rm.nadi,
            "suhu": rm.suhu,
            "keluhan_utama": rm.keluhan_utama,
            "riwayat_penyakit_sekarang": rm.riwayat_penyakit_sekarang,
            "riwayat_penyakit_keluarga": rm.riwayat_penyakit_keluarga,
            "hpht": str(rm.hpht) if rm.hpht else None,
            "hpl": str(rm.hpl) if rm.hpl else None,
            "pemeriksaan_fisik_lengkap": rm.pemeriksaan_fisik_lengkap,
            "diagnosa_utama": rm.diagnosa_utama,
            "rencana_layanan": rm.rencana_layanan,
            "resep_obat": rm.resep_obat,
            "edukasi_pasien": rm.edukasi_pasien
        }
    }


# =============================================================================
# HELPER FUNCTIONS (Fungsi Bantuan Internal)
# =============================================================================

def _parse_date(date_str):
    """
    Konversi string tanggal format YYYY-MM-DD ke object date Python.
    Return None jika string kosong atau format salah.
    Prefiks _ artinya ini fungsi "private" (hanya untuk dipakai di file ini).
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None  # Jangan error, biarkan null daripada crash


def _hapus_file_temp(original_path: str, compressed_path: str):
    """
    Hapus file audio sementara setelah selesai diproses.
    Penting untuk menjaga storage server tetap bersih.
    """
    if os.path.exists(original_path):
        os.remove(original_path)
        print(f"[CLEANUP] File dihapus: {original_path}")

    # Hapus file hasil kompresi juga (kalau berbeda dari file asli)
    if compressed_path != original_path and os.path.exists(compressed_path):
        os.remove(compressed_path)
        print(f"[CLEANUP] File compressed dihapus: {compressed_path}")