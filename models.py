import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


# -----------------------------------------------------------------------------
# Tabel: users
# -----------------------------------------------------------------------------

class User(Base):
    """Akun pengguna sistem — bisa berperan sebagai admin atau dokter."""

    __tablename__ = "users"

    id_user      = Column(Integer, primary_key=True, index=True)
    username     = Column(String(50), unique=True, nullable=False)
    password     = Column(String(255), nullable=False)          # Selalu disimpan dalam bentuk hash
    nama_lengkap = Column(String(100), nullable=False)
    role         = Column(Enum("admin", "dokter"), nullable=False)

    spesialisasi = Column(String(100), nullable=True)           # Khusus dokter
    no_str       = Column(String(50), nullable=True)            # Nomor Surat Tanda Registrasi

    is_active  = Column(Boolean, default=False)                 # False = menunggu aktivasi admin
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    rekam_medis = relationship(
        "RekamMedis",
        back_populates="dokter",
        foreign_keys="RekamMedis.id_dokter",
    )


# -----------------------------------------------------------------------------
# Tabel: patients
# -----------------------------------------------------------------------------

class Pasien(Base):
    """Data identitas pasien. Satu pasien bisa memiliki banyak rekam medis."""

    __tablename__ = "patients"

    id_pasien      = Column(Integer, primary_key=True, index=True)
    no_rekam_medis = Column(String(20), unique=True, nullable=False)
    nik            = Column(String(16), unique=True, nullable=True)
    nama_pasien    = Column(String(100), nullable=False)

    tanggal_lahir  = Column(Date, nullable=False)
    jenis_kelamin  = Column(Enum("L", "P"), nullable=False)
    alamat         = Column(Text, nullable=True)
    no_telepon     = Column(String(15), nullable=True)

    riwayat_berobat = relationship("RekamMedis", back_populates="pasien")


# -----------------------------------------------------------------------------
# Tabel: medical_records
# -----------------------------------------------------------------------------

class RekamMedis(Base):
    """
    Catatan medis per kunjungan pasien, mengikuti format SOAP:
        S (Subjektif) → keluhan yang disampaikan pasien
        O (Objektif)  → hasil pemeriksaan fisik & tanda vital
        A (Assessment)→ diagnosis dokter
        P (Plan)      → rencana pengobatan & resep
    """

    __tablename__ = "medical_records"

    id_record = Column(Integer, primary_key=True, index=True)
    id_pasien = Column(Integer, ForeignKey("patients.id_pasien"))
    id_dokter = Column(Integer, ForeignKey("users.id_user"))

    waktu_pemeriksaan = Column(DateTime, default=datetime.datetime.utcnow)
    status_record     = Column(Enum("draft", "final"), default="draft")
    audio_path        = Column(String(255), nullable=True)

    # S — Subjektif
    keluhan_utama             = Column(Text)
    riwayat_penyakit_sekarang = Column(Text)
    riwayat_penyakit_keluarga = Column(Text)

    # Data kebidanan (khusus RSIA)
    hpht = Column(Date, nullable=True)   # Hari Pertama Haid Terakhir
    hpl  = Column(Date, nullable=True)   # Hari Perkiraan Lahir

    # O — Objektif (tanda vital)
    tekanan_darah = Column(String(20))
    nadi          = Column(String(20))
    suhu          = Column(String(20))

    # O — Pemeriksaan fisik
    pemeriksaan_fisik_lengkap = Column(Text)

    # A — Assessment
    diagnosa_utama = Column(Text)

    # P — Plan
    rencana_layanan = Column(Text)
    resep_obat      = Column(Text)
    edukasi_pasien  = Column(Text)

    pasien = relationship("Pasien", back_populates="riwayat_berobat")
    dokter = relationship("User", back_populates="rekam_medis", foreign_keys=[id_dokter])