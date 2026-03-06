"""
main.py - Entry Point Aplikasi SmartERM

Analogi: Ini seperti LOBI UTAMA gedung.
Semua orang masuk lewat sini, lalu diarahkan ke lantai/bagian yang tepat.

Yang ada di file ini:
1. Inisialisasi aplikasi FastAPI
2. Buat tabel database (kalau belum ada)
3. Daftarkan semua router (admin, dokter, medical)
4. Endpoint "/" sebagai health check

Cara jalankan server:
  uvicorn main:app --reload
  
  Lalu buka browser: http://localhost:8000/docs
  (Dokumentasi API otomatis dari FastAPI)
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import models
from database import engine, get_db
from schemas import Token
from auth import verify_password, create_access_token, get_password_hash
from schemas import RegisterAdminSchema

# Import semua router dari folder routers/
from routers import admin, dokter, medical

# =============================================================================
# INISIALISASI
# =============================================================================

# Buat semua tabel di database (jika belum ada)
# Ini membaca semua class di models.py dan membuat tabelnya
# Aman dijalankan berkali-kali (tidak menghapus data yang sudah ada)
models.Base.metadata.create_all(bind=engine)

# Buat aplikasi FastAPI
app = FastAPI(
    title="SmartERM RSIA Al Hasanah",
    description="Sistem Rekam Medis Elektronik berbasis AI (Whisper + Llama 3)",
    version="2.0.0"
)

# =============================================================================
# DAFTARKAN SEMUA ROUTER
# =============================================================================

# Router Auth & Admin → semua endpoint di admin.py
# prefix="/admin" → URL jadi: /admin/login, /admin/register-admin, dst
# KECUALI login yang kita daftarkan tanpa prefix di bawah

# LOGIN — taruh di root, bukan di /admin
@app.post("/login", response_model=Token, tags=["Auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Username atau Password salah")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Akun belum diaktifkan Admin")
    token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "role": user.role}

# REGISTER ADMIN — juga taruh di root atau prefix /auth
@app.post("/register-admin", tags=["Auth"])
def register_admin(data: RegisterAdminSchema, db: Session = Depends(get_db)):
    ...

app.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin & Auth"]
)

# Router Dokter → semua endpoint di dokter.py
# prefix="/dokter" → URL jadi: /dokter/pasien, /dokter/cari-pasien, dst
app.include_router(
    dokter.router,
    prefix="/dokter",
    tags=["Manajemen Pasien"]
)

# Router Medical/AI → semua endpoint di medical.py
# prefix="/medical" → URL jadi: /medical/transcribe, /medical/simpan-rm, dst
app.include_router(
    medical.router,
    prefix="/medical",
    tags=["AI & Rekam Medis"]
)

# =============================================================================
# ENDPOINT DASAR
# =============================================================================

@app.get("/", tags=["Info"])
def home():
    """
    Health check endpoint.
    Kalau server nyala, return status aktif.
    Berguna untuk monitoring server.
    """
    return {
        "status": "✅ Server SmartERM Aktif!",
        "versi": "2.0.0",
        "docs": "Buka /docs untuk dokumentasi API lengkap"
    }

# =============================================================================
# CATATAN UNTUK DEVELOPER
# =============================================================================
# 
# STRUKTUR URL LENGKAP:
# 
# AUTH:
#   POST /admin/login              → Login semua user
#   POST /admin/register-admin     → Daftar admin baru
#
# ADMIN:
#   POST /admin/create-dokter      → Buat akun dokter (butuh token admin)
#   PUT  /admin/activate/{id}      → Aktifkan akun user (butuh token admin)
#   GET  /admin/list-dokter        → Lihat semua dokter (butuh token admin)
#
# DOKTER:
#   POST /dokter/pasien            → Daftar pasien baru (butuh login)
#   GET  /dokter/pasien/{no_rm}    → Lihat data pasien (butuh login)
#   GET  /dokter/cari-pasien?nama= → Cari pasien (butuh login)
#
# MEDICAL/AI:
#   POST /medical/transcribe       → Upload audio → JSON medis (butuh login)
#   POST /medical/simpan-rm        → Simpan rekam medis (butuh login)
#   GET  /medical/rekam-medis/{id} → Lihat detail rekam medis (butuh login)