from typing import Optional
from pydantic import BaseModel


class BaseAccountSchema(BaseModel):
    username: str
    nama_lengkap: str


class BaseEditAccountSchema(BaseModel):
    nama_lengkap: Optional[str] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    nama_lengkap: str


class RegisterAdminSchema(BaseAccountSchema):
    password: str


class CreateDokterSchema(BaseAccountSchema):
    password: str
    spesialisasi: str
    no_str: str


class EditDokterSchema(BaseEditAccountSchema):
    spesialisasi: Optional[str] = None
    no_str: Optional[str] = None


class CreateAdminSchema(BaseAccountSchema):
    password: str


class EditAdminSchema(BaseEditAccountSchema):
    pass


class CreatePasienSchema(BaseModel):
    no_rekam_medis: str
    nama_pasien: str
    tanggal_lahir: str
    jenis_kelamin: str

    nik: Optional[str] = None
    alamat: Optional[str] = None
    no_telepon: Optional[str] = None


class SimpanRMSchema(BaseModel):
    no_rekam_medis: str

    tekanan_darah: Optional[str] = None
    nadi: Optional[str] = None
    suhu: Optional[str] = None

    keluhan_utama: Optional[str] = None
    riwayat_penyakit_sekarang: Optional[str] = None
    riwayat_penyakit_keluarga: Optional[str] = None

    hpht: Optional[str] = None
    hpl: Optional[str] = None

    pemeriksaan_fisik_lengkap: Optional[str] = None

    diagnosa_utama: Optional[str] = None

    rencana_layanan: Optional[str] = None
    resep_obat: Optional[str] = None
    edukasi_pasien: Optional[str] = None