"""
schemas.py — Pydantic validation schemas untuk semua endpoint SmartERM
"""

from typing import Optional
from pydantic import BaseModel


# =============================================================================
# AUTH
# =============================================================================

class Token(BaseModel):
    access_token: str
    token_type:   str
    role:         str
    nama_lengkap: str


class RegisterAdminSchema(BaseModel):
    """Dipakai di POST /register-admin (pendaftaran mandiri, butuh aktivasi)."""
    username:     str
    password:     str
    nama_lengkap: str


# =============================================================================
# ADMIN — Dokter
# =============================================================================

class CreateDokterSchema(BaseModel):
    """Admin membuat akun dokter baru. Semua field wajib."""
    username:     str
    password:     str
    nama_lengkap: str
    spesialisasi: str
    no_str:       str


class EditDokterSchema(BaseModel):
    """
    Edit data dokter. Semua field opsional —
    hanya field yang dikirim yang akan diupdate (partial update).
    Password hanya diupdate jika dikirim dan tidak kosong.
    """
    nama_lengkap: Optional[str] = None
    username:     Optional[str] = None
    spesialisasi: Optional[str] = None
    no_str:       Optional[str] = None
    is_active:    Optional[bool] = None
    password:     Optional[str] = None   # kosong = tidak diubah


# =============================================================================
# ADMIN — Admin
# =============================================================================

class CreateAdminSchema(BaseModel):
    """Admin membuat akun admin baru. Langsung aktif."""
    username:     str
    password:     str
    nama_lengkap: str


class EditAdminSchema(BaseModel):
    """
    Edit data admin. Semua field opsional.
    Password hanya diupdate jika dikirim dan tidak kosong.
    """
    nama_lengkap: Optional[str] = None
    username:     Optional[str] = None
    is_active:    Optional[bool] = None
    password:     Optional[str] = None   # kosong = tidak diubah


# =============================================================================
# PASIEN
# =============================================================================

class CreatePasienSchema(BaseModel):
    """Data yang dibutuhkan untuk mendaftarkan pasien baru."""
    no_rekam_medis: str
    nama_pasien:    str
    tanggal_lahir:  str                    # Format: YYYY-MM-DD
    jenis_kelamin:  str                    # "L" atau "P"
    nik:            Optional[str] = None
    alamat:         Optional[str] = None
    no_telepon:     Optional[str] = None


# =============================================================================
# REKAM MEDIS
# =============================================================================

class SimpanRMSchema(BaseModel):
    """
    Data rekam medis yang dikirim dokter setelah mengedit hasil AI.
    Semua field medis opsional karena tidak semua data tersedia tiap kunjungan.
    """
    no_rekam_medis: str

    # Tanda vital
    tekanan_darah:  Optional[str] = None
    nadi:           Optional[str] = None
    suhu:           Optional[str] = None

    # S — Subjektif
    keluhan_utama:             Optional[str] = None
    riwayat_penyakit_sekarang: Optional[str] = None
    riwayat_penyakit_keluarga: Optional[str] = None

    # Data kebidanan
    hpht: Optional[str] = None   # Format: YYYY-MM-DD
    hpl:  Optional[str] = None   # Format: YYYY-MM-DD

    # O — Pemeriksaan fisik
    pemeriksaan_fisik_lengkap: Optional[str] = None

    # A — Assessment
    diagnosa_utama: Optional[str] = None

    # P — Plan
    rencana_layanan: Optional[str] = None
    resep_obat:      Optional[str] = None
    edukasi_pasien:  Optional[str] = None