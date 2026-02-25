"""
schemas.py - Semua Format Data (Pydantic Models)

Analogi: Ini seperti FORMULIR RESMI.
Setiap formulir (schema) mendefinisikan:
- Field apa yang ada
- Tipe datanya (string, int, date, dll)
- Boleh kosong atau tidak (Optional)

FastAPI pakai ini untuk:
1. Validasi data yang masuk (request body)
2. Dokumentasi otomatis di /docs

Kenapa dipisah dari models.py?
→ models.py = blueprint TABEL DATABASE (SQLAlchemy)
→ schemas.py = blueprint FORMAT API (Pydantic)
   Keduanya berbeda! models untuk DB, schemas untuk API.
"""

from pydantic import BaseModel
from typing import Optional


# =============================================================================
# SCHEMAS AUTH (Untuk Login & Register)
# =============================================================================

class Token(BaseModel):
    """
    Format response setelah login berhasil.
    Frontend akan simpan access_token ini untuk request selanjutnya.
    """
    access_token: str
    token_type: str   # Selalu "bearer"
    role: str         # "admin" atau "dokter" → untuk routing di frontend


class RegisterAdminSchema(BaseModel):
    """
    Format data untuk register admin baru.
    Admin baru statusnya is_active=False, harus diaktifkan admin lain.
    """
    username: str
    password: str
    nama_lengkap: str


# =============================================================================
# SCHEMAS ADMIN (Untuk Endpoint Admin)
# =============================================================================

class CreateDokterSchema(BaseModel):
    """
    Format data untuk admin membuat akun dokter baru.
    Dokter yang dibuat admin langsung is_active=True.
    """
    username: str
    password: str
    nama_lengkap: str
    spesialisasi: str   # Contoh: "Obstetri & Ginekologi"
    no_str: str         # Nomor Surat Tanda Registrasi dokter (wajib secara hukum)


# =============================================================================
# SCHEMAS PASIEN (Untuk Endpoint Dokter)
# =============================================================================

class CreatePasienSchema(BaseModel):
    """
    Format data untuk mendaftarkan pasien baru.
    Dokter yang input ini saat pertama kali pasien datang.
    """
    no_rekam_medis: str         # Nomor RM unik, biasanya dibuat manual/otomatis RS
    nik: Optional[str] = None   # NIK KTP (boleh kosong)
    nama_pasien: str
    tanggal_lahir: str          # Format YYYY-MM-DD
    jenis_kelamin: str          # "L" atau "P"
    alamat: Optional[str] = None
    no_telepon: Optional[str] = None


# =============================================================================
# SCHEMAS REKAM MEDIS (Untuk Endpoint Medical/AI)
# =============================================================================

class SimpanRMSchema(BaseModel):
    """
    Format data untuk menyimpan rekam medis setelah dokter edit hasil AI.
    
    Semua field medis Optional karena:
    - Dokter mungkin menghapus data yang salah
    - Tidak semua data selalu tersedia di setiap kunjungan
    """
    no_rekam_medis: str   # Wajib! Untuk mencari pasien yang tepat di DB

    # Data Vital (Tanda-tanda kehidupan)
    tekanan_darah: Optional[str] = None    # Contoh: "120/80"
    nadi: Optional[str] = None             # Contoh: "80x/menit"
    suhu: Optional[str] = None             # Contoh: "36.5"
    pernapasan: Optional[str] = None       # Contoh: "20x/menit"

    # Data Subjektif (Keluhan dari pasien)
    keluhan_utama: Optional[str] = None
    riwayat_penyakit_sekarang: Optional[str] = None
    riwayat_penyakit_keluarga: Optional[str] = None

    # Data Kebidanan (Khusus pasien kandungan)
    hpht: Optional[str] = None   # Hari Pertama Haid Terakhir, format YYYY-MM-DD
    hpl: Optional[str] = None    # Hari Perkiraan Lahir, format YYYY-MM-DD

    # Data Objektif (Hasil pemeriksaan dokter)
    pemeriksaan_fisik_lengkap: Optional[str] = None

    # Assessment & Plan
    diagnosa_utama: Optional[str] = None
    rencana_layanan: Optional[str] = None
    resep_obat: Optional[str] = None
    edukasi_pasien: Optional[str] = None