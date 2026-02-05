from pydantic import BaseModel
from typing import Optional
from datetime import date

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class RegisterAdminSchema(BaseModel):
    username: str
    password: str
    nama_lengkap: str

class CreateDokterSchema(BaseModel):
    username: str
    password: str
    nama_lengkap: str
    spesialisasi: str
    no_str: str

class SimpanRMSchema(BaseModel):
    no_rekam_medis: str 
    keluhan_utama: Optional[str] = None
    riwayat_penyakit_sekarang: Optional[str] = None
    riwayat_penyakit_keluarga: Optional[str] = None
    hpht: Optional[str] = None # Format YYYY-MM-DD
    hpl: Optional[str] = None
    tekanan_darah: Optional[str] = None
    nadi: Optional[str] = None
    suhu: Optional[str] = None
    pernapasan: Optional[str] = None
    pemeriksaan_fisik_lengkap: Optional[str] = None
    diagnosa_utama: Optional[str] = None
    rencana_layanan: Optional[str] = None
    resep_obat: Optional[str] = None
    edukasi_pasien: Optional[str] = None