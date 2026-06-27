from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id_user = Column(Integer, primary_key=True, index=True)

    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    nama_lengkap = Column(String(100), nullable=False)
    role = Column(Enum("admin", "dokter"), nullable=False)

    spesialisasi = Column(String(100))
    no_str = Column(String(50))

    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    rekam_medis = relationship(
        "RekamMedis",
        back_populates="dokter",
        foreign_keys="RekamMedis.id_dokter",
    )


class Pasien(Base):
    __tablename__ = "patients"

    id_pasien = Column(Integer, primary_key=True, index=True)

    no_rekam_medis = Column(String(20), unique=True, nullable=False)
    nik = Column(String(16), unique=True)

    nama_pasien = Column(String(100), nullable=False)
    tanggal_lahir = Column(Date, nullable=False)

    jenis_kelamin = Column(Enum("L", "P"), nullable=False)
    alamat = Column(Text)
    no_telepon = Column(String(15))

    riwayat_berobat = relationship(
        "RekamMedis",
        back_populates="pasien",
    )


class RekamMedis(Base):
    __tablename__ = "medical_records"

    id_record = Column(Integer, primary_key=True, index=True)

    id_pasien = Column(
        Integer,
        ForeignKey("patients.id_pasien"),
        nullable=False,
    )

    id_dokter = Column(
        Integer,
        ForeignKey("users.id_user"),
        nullable=False,
    )

    waktu_pemeriksaan = Column(
        DateTime,
        default=datetime.utcnow,
    )

    status_record = Column(
        Enum("draft", "final"),
        default="draft",
    )

    audio_path = Column(String(255))

    # Anamnesis
    keluhan_utama = Column(Text)
    riwayat_penyakit_sekarang = Column(Text)
    riwayat_penyakit_keluarga = Column(Text)

    # Kebidanan
    hpht = Column(Date)
    hpl = Column(Date)

    # Tanda Vital
    tekanan_darah = Column(String(20))
    nadi = Column(String(20))
    suhu = Column(String(20))

    # Pemeriksaan
    pemeriksaan_fisik_lengkap = Column(Text)

    # Diagnosis
    diagnosa_utama = Column(Text)

    # Tatalaksana
    rencana_layanan = Column(Text)
    resep_obat = Column(Text)
    edukasi_pasien = Column(Text)

    pasien = relationship(
        "Pasien",
        back_populates="riwayat_berobat",
    )

    dokter = relationship(
        "User",
        back_populates="rekam_medis",
        foreign_keys=[id_dokter],
    )