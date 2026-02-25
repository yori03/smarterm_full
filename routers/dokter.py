"""
routers/dokter.py - Endpoint Khusus Dokter (Manajemen Pasien)

Endpoint di sini untuk:
- Daftar pasien baru
- Cari pasien
- Lihat profil pasien + riwayat berobatnya

Prefix dari mainbaru.py: "/dokter"
URL lengkap: /dokter/pasien, /dokter/pasien/RM001, dll.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

import models
from database import get_db
from schemas import CreatePasienSchema
from dependencies import get_current_user  # Dokter dan admin bisa akses

router = APIRouter()


# =============================================================================
# DAFTAR PASIEN BARU
# =============================================================================

@router.post("/pasien")
def daftar_pasien_baru(
    data: CreatePasienSchema,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)  # Login apa saja
):
    """
    Mendaftarkan pasien baru ke sistem.
    
    No Rekam Medis harus unik (tidak boleh sama antar pasien).
    Biasanya format: RM + tahun + nomor urut (contoh: RM2024001)
    """
    # Cek No RM sudah dipakai
    if db.query(models.Pasien).filter(models.Pasien.no_rekam_medis == data.no_rekam_medis).first():
        raise HTTPException(status_code=400, detail=f"No Rekam Medis '{data.no_rekam_medis}' sudah terdaftar")

    # Cek NIK sudah dipakai (jika diisi)
    if data.nik and db.query(models.Pasien).filter(models.Pasien.nik == data.nik).first():
        raise HTTPException(status_code=400, detail=f"NIK '{data.nik}' sudah terdaftar untuk pasien lain")

    # Parse tanggal lahir
    try:
        tgl_lahir = datetime.strptime(data.tanggal_lahir, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Format tanggal_lahir harus YYYY-MM-DD (contoh: 1990-05-25)")

    new_pasien = models.Pasien(
        no_rekam_medis=data.no_rekam_medis,
        nik=data.nik,
        nama_pasien=data.nama_pasien,
        tanggal_lahir=tgl_lahir,
        jenis_kelamin=data.jenis_kelamin,
        alamat=data.alamat,
        no_telepon=data.no_telepon
    )
    db.add(new_pasien)
    db.commit()
    db.refresh(new_pasien)

    return {
        "msg": f"Pasien '{data.nama_pasien}' berhasil didaftarkan.",
        "id_pasien": new_pasien.id_pasien,
        "no_rekam_medis": new_pasien.no_rekam_medis
    }


# =============================================================================
# CARI PASIEN BERDASARKAN NO REKAM MEDIS
# =============================================================================

@router.get("/pasien/{no_rekam_medis}")
def get_pasien(
    no_rekam_medis: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Ambil data pasien + riwayat berobatnya berdasarkan No RM.
    
    Path parameter: no_rekam_medis
    Contoh URL: GET /dokter/pasien/RM2024001
    """
    pasien = db.query(models.Pasien).filter(models.Pasien.no_rekam_medis == no_rekam_medis).first()
    if not pasien:
        raise HTTPException(status_code=404, detail=f"Pasien dengan No RM '{no_rekam_medis}' tidak ditemukan")

    # Ambil riwayat berobat (rekam medis sebelumnya)
    riwayat = db.query(models.RekamMedis).filter(
        models.RekamMedis.id_pasien == pasien.id_pasien
    ).order_by(models.RekamMedis.waktu_pemeriksaan.desc()).all()

    return {
        "data_pasien": {
            "id_pasien": pasien.id_pasien,
            "no_rekam_medis": pasien.no_rekam_medis,
            "nik": pasien.nik,
            "nama_pasien": pasien.nama_pasien,
            "tanggal_lahir": str(pasien.tanggal_lahir),
            "jenis_kelamin": pasien.jenis_kelamin,
            "alamat": pasien.alamat,
            "no_telepon": pasien.no_telepon
        },
        "total_kunjungan": len(riwayat),
        "riwayat_berobat": [
            {
                "id_record": r.id_record,
                "waktu_pemeriksaan": str(r.waktu_pemeriksaan),
                "diagnosa_utama": r.diagnosa_utama,
                "status_record": r.status_record
            }
            for r in riwayat
        ]
    }


# =============================================================================
# CARI PASIEN BERDASARKAN NAMA (Pencarian)
# =============================================================================

@router.get("/cari-pasien")
def cari_pasien(
    nama: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Cari pasien berdasarkan nama (pencarian parsial).
    
    Query parameter: nama
    Contoh URL: GET /dokter/cari-pasien?nama=Siti
    """
    # ilike = case-insensitive LIKE (cocok untuk pencarian nama)
    hasil = db.query(models.Pasien).filter(
        models.Pasien.nama_pasien.ilike(f"%{nama}%")
    ).limit(20).all()  # Batasi 20 hasil

    if not hasil:
        return {"msg": f"Tidak ada pasien dengan nama yang mengandung '{nama}'", "data": []}

    return {
        "total": len(hasil),
        "data": [
            {
                "no_rekam_medis": p.no_rekam_medis,
                "nama_pasien": p.nama_pasien,
                "tanggal_lahir": str(p.tanggal_lahir),
                "no_telepon": p.no_telepon
            }
            for p in hasil
        ]
    }