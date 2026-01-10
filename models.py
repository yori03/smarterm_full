from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id_dokter = Column(Integer, primary_key=True, index=True)
    nama_lengkap = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), default="dokter")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class RekamMedis(Base):
    __tablename__ = "medical_records"

    id_record = Column(Integer, primary_key=True, index=True)
    id_dokter = Column(Integer, ForeignKey("users.id_dokter"))
    
    # DATA PASIEN
    no_rekam_medis = Column(String(50), nullable=True)
    nama_pasien = Column(String(100))
    tanggal_lahir = Column(Date, nullable=True)
    alamat = Column(Text, nullable=True)
    waktu_pemeriksaan = Column(DateTime, default=datetime.datetime.utcnow)

    # SUBJECTIVE
    keluhan_utama = Column(Text)
    riwayat_penyakit_sekarang = Column(Text)
    riwayat_penyakit_dahulu = Column(Text)
    riwayat_penyakit_keluarga = Column(Text)

    # DATA OBGYN (Kandungan)
    hpht = Column(Date, nullable=True)
    hpl = Column(Date, nullable=True)
    riwayat_haid_teks = Column(Text)

    # OBJECTIVE (Vital Sign)
    tekanan_darah = Column(String(20))
    nadi = Column(String(20))
    suhu = Column(String(20))
    pernapasan = Column(String(20))
    
    # Fisik Umum
    pemeriksaan_fisik_lengkap = Column(Text)

    # ASSESSMENT
    diagnosa_utama = Column(Text)

    # PLANNING
    rencana_layanan = Column(Text)
    edukasi_pasien = Column(Text)
    resep_obat = Column(Text)

    # TEKNIS
    audio_path = Column(String(255), nullable=True)
    status_record = Column(Enum('draft', 'final'), default='draft')

    # Relasi
    dokter = relationship("User")