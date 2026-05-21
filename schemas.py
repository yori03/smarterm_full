from typing import Optional

from pydantic import BaseModel

"""
schemas.py - Skema Data API (Pydantic Models)

Setiap class mendefinisikan struktur data yang diterima atau dikirim oleh API.
FastAPI menggunakan file ini untuk validasi input otomatis dan dokumentasi /docs.

Perbedaan dengan models.py:
    models.py  → blueprint tabel database (SQLAlchemy)
    schemas.py → blueprint format data API (Pydantic)
"""
# =============================================================================
# Auth
# =============================================================================

class Token(BaseModel):
    """Response setelah login berhasil. Frontend menyimpan access_token untuk request berikutnya."""
    access_token: str
    token_type:   str   # Selalu "bearer"
    role:         str   # "admin" atau "dokter" — dipakai frontend untuk menentukan halaman
    nama_lengkap: str


class RegisterAdminSchema(BaseModel):
    """Data yang dibutuhkan untuk mendaftarkan akun admin baru."""
    username:     str
    password:     str
    nama_lengkap: str


# =============================================================================
# Admin
# =============================================================================

class CreateDokterSchema(BaseModel):
    """Data yang dibutuhkan admin untuk membuat akun dokter baru."""
    username:     str
    password:     str
    nama_lengkap: str
    spesialisasi: str   
    no_str:       str   


# =============================================================================
# Pasien
# =============================================================================

class CreatePasienSchema(BaseModel):
    """Data yang dibutuhkan untuk mendaftarkan pasien baru."""
    no_rekam_medis: str
    nama_pasien:    str
    tanggal_lahir:  str                    # Format: YYYY-MM-DD
    jenis_kelamin:  str                    # "L" atau "P"
    nik:            Optional[str] = None   # NIK KTP (boleh kosong)
    alamat:         Optional[str] = None
    no_telepon:     Optional[str] = None


# =============================================================================
# Rekam Medis
# =============================================================================

class SimpanRMSchema(BaseModel):
    """
    Data rekam medis yang dikirim dokter setelah mengedit hasil AI.

    Semua field medis bersifat opsional karena:
    - Dokter bisa saja menghapus data yang salah dari hasil transkripsi
    - Tidak semua data selalu tersedia di setiap kunjungan
    """
    no_rekam_medis: str  

    # Tanda vital
    tekanan_darah: Optional[str] = None   
    nadi:          Optional[str] = None   
    suhu:          Optional[str] = None   
    pernapasan:    Optional[str] = None   

    # S — Subjektif (keluhan pasien)
    keluhan_utama:             Optional[str] = None
    riwayat_penyakit_sekarang: Optional[str] = None
    riwayat_penyakit_keluarga: Optional[str] = None

    # Data kebidanan (khusus RSIA)
    hpht: Optional[str] = None   
    hpl:  Optional[str] = None   

    # O, A, P — Pemeriksaan, Diagnosis, Rencana
    pemeriksaan_fisik_lengkap: Optional[str] = None
    diagnosa_utama:            Optional[str] = None
    rencana_layanan:           Optional[str] = None
    resep_obat:                Optional[str] = None
    edukasi_pasien:            Optional[str] = None
# =============================================================================
# Auth
# =============================================================================

class Token(BaseModel):
    """Response setelah login berhasil. Frontend menyimpan access_token untuk request berikutnya."""
    access_token: str
    token_type:   str   # Selalu "bearer"
    role:         str   # "admin" atau "dokter" — dipakai frontend untuk menentukan halaman
    nama_lengkap: str


class RegisterAdminSchema(BaseModel):
    """Data yang dibutuhkan untuk mendaftarkan akun admin baru."""
    username:     str
    password:     str
    nama_lengkap: str


# =============================================================================
# Admin
# =============================================================================

class CreateDokterSchema(BaseModel):
    """Data yang dibutuhkan admin untuk membuat akun dokter baru."""
    username:     str
    password:     str
    nama_lengkap: str
    spesialisasi: str   # Contoh: "Obstetri & Ginekologi"
    no_str:       str   # Nomor Surat Tanda Registrasi dokter (wajib secara hukum)


# =============================================================================
# Pasien
# =============================================================================

class CreatePasienSchema(BaseModel):
    """Data yang dibutuhkan untuk mendaftarkan pasien baru."""
    no_rekam_medis: str
    nama_pasien:    str
    tanggal_lahir:  str                    # Format: YYYY-MM-DD
    jenis_kelamin:  str                    # "L" atau "P"
    nik:            Optional[str] = None   # NIK KTP (boleh kosong)
    alamat:         Optional[str] = None
    no_telepon:     Optional[str] = None


# =============================================================================
# Rekam Medis
# =============================================================================

class SimpanRMSchema(BaseModel):
    """
    Data rekam medis yang dikirim dokter setelah mengedit hasil AI.

    Semua field medis bersifat opsional karena:
    - Dokter bisa saja menghapus data yang salah dari hasil transkripsi
    - Tidak semua data selalu tersedia di setiap kunjungan
    """
    no_rekam_medis: str   # Wajib — untuk menentukan pasien yang tepat

    # Tanda vital
    tekanan_darah: Optional[str] = None   # Contoh: "120/80"
    nadi:          Optional[str] = None   # Contoh: "80x/menit"
    suhu:          Optional[str] = None   # Contoh: "36.5"
    pernapasan:    Optional[str] = None   # Contoh: "20x/menit"

    # S — Subjektif (keluhan pasien)
    keluhan_utama:             Optional[str] = None
    riwayat_penyakit_sekarang: Optional[str] = None
    riwayat_penyakit_keluarga: Optional[str] = None

    # Data kebidanan (khusus RSIA)
    hpht: Optional[str] = None    
    hpl:  Optional[str] = None   

    # O, A, P — Pemeriksaan, Diagnosis, Rencana
    pemeriksaan_fisik_lengkap: Optional[str] = None
    diagnosa_utama:            Optional[str] = None
    rencana_layanan:           Optional[str] = None
    resep_obat:                Optional[str] = None
    edukasi_pasien:            Optional[str] = None