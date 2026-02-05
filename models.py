from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
import datetime

# 1. Tabel Users (Admin & Dokter)
class User(Base):
    __tablename__ = "users" # Harus sama dengan nama tabel di SQL
    
    # Kolom-kolomnya (Sesuai SQL)
    id_user = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    nama_lengkap = Column(String(100), nullable=False)
    role = Column(Enum('admin', 'dokter'), nullable=False)
    
    # Data tambahan dokter
    spesialisasi = Column(String(100), nullable=True)
    no_str = Column(String(50), nullable=True)
    
    # Fitur Kunci: Status Aktif
    is_active = Column(Boolean, default=False) 
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# 2. Tabel Patients (Data Pasien) - INI YANG KEMARIN HILANG
class Pasien(Base):
    __tablename__ = "patients"
    
    id_pasien = Column(Integer, primary_key=True, index=True)
    no_rekam_medis = Column(String(20), unique=True, nullable=False)
    nik = Column(String(16), unique=True, nullable=True)
    nama_pasien = Column(String(100), nullable=False)
    tanggal_lahir = Column(Date, nullable=False)
    jenis_kelamin = Column(Enum('L', 'P'), nullable=False)
    alamat = Column(Text, nullable=True)
    no_telepon = Column(String(15), nullable=True)
    
    # Relasi: 1 Pasien punya banyak record
    riwayat_berobat = relationship("RekamMedis", back_populates="pasien")

# 3. Tabel Medical Records (Transaksi)
class RekamMedis(Base):
    __tablename__ = "medical_records"

    id_record = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys (Menunjuk ke tabel lain)
    id_pasien = Column(Integer, ForeignKey("patients.id_pasien"))
    id_dokter = Column(Integer, ForeignKey("users.id_user"))
    
    waktu_pemeriksaan = Column(DateTime, default=datetime.datetime.utcnow)
    status_record = Column(Enum('draft', 'final'), default='draft')
    audio_path = Column(String(255), nullable=True)

    # SOAP Fields
    keluhan_utama = Column(Text)
    riwayat_penyakit_sekarang = Column(Text)
    riwayat_penyakit_keluarga = Column(Text)
    hpht = Column(Date, nullable=True)
    hpl = Column(Date, nullable=True)
    tekanan_darah = Column(String(20))
    nadi = Column(String(20))
    suhu = Column(String(20))
    pemeriksaan_fisik_lengkap = Column(Text)
    diagnosa_utama = Column(Text)
    rencana_layanan = Column(Text)
    resep_obat = Column(Text)
    edukasi_pasien = Column(Text)

    # Relasi Balik (Agar bisa dipanggil di Python)
    pasien = relationship("Pasien", back_populates="riwayat_berobat")
    dokter = relationship("User")