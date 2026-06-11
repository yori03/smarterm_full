from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db
from dependencies import get_current_user
from schemas import CreatePasienSchema, SimpanRMSchema

router = APIRouter()


@router.post("/pasien")
def daftar_pasien_baru(
    data: CreatePasienSchema,
    db: Session = Depends(get_db),
    pengguna: models.User = Depends(get_current_user),
):
    if db.query(models.Pasien).filter(models.Pasien.no_rekam_medis == data.no_rekam_medis).first():
        raise HTTPException(
            status_code=400,
            detail=f"No Rekam Medis '{data.no_rekam_medis}' sudah terdaftar.",
        )

    if data.nik and db.query(models.Pasien).filter(models.Pasien.nik == data.nik).first():
        raise HTTPException(
            status_code=400,
            detail=f"NIK '{data.nik}' sudah terdaftar untuk pasien lain.",
        )

    try:
        tanggal_lahir = datetime.strptime(data.tanggal_lahir, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Format tanggal_lahir harus YYYY-MM-DD (contoh: 1990-05-25).",
        )

    pasien_baru = models.Pasien(
        no_rekam_medis=data.no_rekam_medis,
        nik=data.nik,
        nama_pasien=data.nama_pasien,
        tanggal_lahir=tanggal_lahir,
        jenis_kelamin=data.jenis_kelamin,
        alamat=data.alamat,
        no_telepon=data.no_telepon,
    )

    db.add(pasien_baru)
    db.commit()
    db.refresh(pasien_baru)

    return {
        "msg":            f"Pasien '{data.nama_pasien}' berhasil didaftarkan.",
        "id_pasien":       pasien_baru.id_pasien,
        "no_rekam_medis":  pasien_baru.no_rekam_medis,
    }


@router.get("/pasien/{no_rekam_medis}")
def get_pasien(
    no_rekam_medis: str,
    db: Session = Depends(get_db),
    pengguna: models.User = Depends(get_current_user),
):
    pasien = db.query(models.Pasien).filter(
        models.Pasien.no_rekam_medis == no_rekam_medis
    ).first()

    if not pasien:
        raise HTTPException(
            status_code=404,
            detail=f"Pasien dengan No RM '{no_rekam_medis}' tidak ditemukan.",
        )

    riwayat = (
        db.query(models.RekamMedis)
        .filter(models.RekamMedis.id_pasien == pasien.id_pasien)
        .order_by(models.RekamMedis.waktu_pemeriksaan.desc())
        .all()
    )

    return {
        "data_pasien": {
            "id_pasien":      pasien.id_pasien,
            "no_rekam_medis": pasien.no_rekam_medis,
            "nik":            pasien.nik,
            "nama_pasien":    pasien.nama_pasien,
            "tanggal_lahir":  str(pasien.tanggal_lahir),
            "jenis_kelamin":  pasien.jenis_kelamin,
            "alamat":         pasien.alamat,
            "no_telepon":     pasien.no_telepon,
        },
        "total_kunjungan": len(riwayat),
        "riwayat_berobat": [
            {
                "id_record":         r.id_record,
                "waktu_pemeriksaan": str(r.waktu_pemeriksaan),
                "diagnosa_utama":    r.diagnosa_utama,
                "status_record":     r.status_record,
            }
            for r in riwayat
        ],
    }


@router.get("/cari-pasien")
def cari_pasien(
    nama: str,
    db: Session = Depends(get_db),
    pengguna: models.User = Depends(get_current_user),
):
    """
    Cari pasien berdasarkan nama (pencarian parsial, tidak case-sensitive).
    Hasil dibatasi maksimal 20 data.
    Contoh: GET /dokter/cari-pasien?nama=Siti
    """
    hasil = (
        db.query(models.Pasien)
        .filter(models.Pasien.nama_pasien.ilike(f"%{nama}%"))
        .limit(20)
        .all()
    )

    if not hasil:
        return {"msg": f"Tidak ada pasien dengan nama yang mengandung '{nama}'.", "data": []}

    return {
        "total": len(hasil),
        "data": [
            {
                "no_rekam_medis": p.no_rekam_medis,
                "nama_pasien":    p.nama_pasien,
                "tanggal_lahir":  str(p.tanggal_lahir),
                "no_telepon":     p.no_telepon,
            }
            for p in hasil
        ],
    }


@router.post("/rekam-medis")
def simpan_rekam_medis(
    data: SimpanRMSchema,
    db: Session = Depends(get_db),
    pengguna: models.User = Depends(get_current_user),
):
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
        tekanan_darah=data.tekanan_darah,
        nadi=data.nadi,
        suhu=data.suhu,
        keluhan_utama=data.keluhan_utama,
        riwayat_penyakit_sekarang=data.riwayat_penyakit_sekarang,
        riwayat_penyakit_keluarga=data.riwayat_penyakit_keluarga,
        hpht=_parse_tanggal(data.hpht),
        hpl=_parse_tanggal(data.hpl),
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
        "pasien":            rm.pasien.nama_pasien      if rm.pasien else None,
        "no_rekam_medis":    rm.pasien.no_rekam_medis   if rm.pasien else None,
        # ── dua field baru: diambil langsung dari relasi pasien ──
        "tanggal_lahir":     str(rm.pasien.tanggal_lahir) if rm.pasien and rm.pasien.tanggal_lahir else None,
        "alamat":            rm.pasien.alamat            if rm.pasien else None,
        # ────────────────────────────────────────────────────────
        "dokter":            rm.dokter.nama_lengkap      if rm.dokter else None,
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
            "hpl":                       str(rm.hpl)  if rm.hpl  else None,
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
    Mengembalikan None jika string kosong atau formatnya tidak sesuai.
    """
    if not teks_tanggal:
        return None
    try:
        return datetime.strptime(teks_tanggal, "%Y-%m-%d").date()
    except ValueError:
        return None