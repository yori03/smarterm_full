"""
dependencies.py - Fungsi Satpam (Dependency Injection)

KENAPA FILE INI ADA?
Di FastAPI, "dependency" adalah fungsi yang dijalankan SEBELUM
fungsi endpoint utama. Seperti satpam yang cek kartu akses
sebelum kamu boleh masuk ruangan.

ALUR KERJA get_current_user():
Request masuk ke endpoint → FastAPI panggil get_current_user() dulu
→ Ambil token dari header Authorization
→ Decode token → dapat username
→ Cari user di DB
→ Cek is_active
→ Return object User → endpoint utama baru jalan

KENAPA DIPISAH KE FILE INI (bukan langsung di router)?
→ Bisa dipakai ulang di semua router tanpa copy-paste
→ Kalau mau ganti sistem auth (misal dari JWT ke session),
  cukup edit 1 file ini, tidak perlu edit semua router

HUBUNGAN DENGAN FILE LAIN:
dependencies.py → dipakai oleh:
  - routers/admin.py    (get_current_admin)
  - routers/dokter.py   (get_current_user)
  - routers/medical.py  (get_current_user)
"""

import os
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from dotenv import load_dotenv

import models
from database import get_db
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "ganti_ini_di_env_ya")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# =============================================================================
# INI YANG MENYEBABKAN BUG KEMARIN!
#
# OAuth2PasswordBearer punya 2 fungsi:
#
# FUNGSI 1 - Saat request datang (runtime):
#   Baca header "Authorization: Bearer <token>" → ambil token-nya
#
# FUNGSI 2 - Saat /docs dibuka (dokumentasi):
#   Kasih tahu Swagger: "Endpoint login ada di URL ini"
#   Swagger pakai info ini untuk form Authorize
#
# tokenUrl="login" → Swagger akan POST ke "/login"
#
# KENAPA BUKAN "admin/login"?
# Karena kita sudah pindahkan endpoint login ke main.py tanpa prefix,
# sehingga URL-nya adalah "/login" (bukan "/admin/login").
#
# ATURAN SEDERHANA:
# tokenUrl harus SAMA PERSIS dengan URL endpoint @app.post("/login")
# Kalau login ada di /login → tokenUrl="login"
# Kalau login ada di /auth/login → tokenUrl="auth/login"
# =============================================================================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """
    SATPAM UMUM: Cek token → return User object.
    
    Dipakai di endpoint yang butuh login (dokter ATAU admin bisa akses).
    
    STEP BY STEP:
    1. oauth2_scheme baca header Authorization → ambil token string
    2. jwt.decode() → buka "amplop" token → dapat isi (payload)
    3. Ambil username dari payload["sub"]
    4. Cari user di database
    5. Cek is_active
    6. Return user object → endpoint utama terima ini sebagai parameter
    
    Kalau salah satu step gagal → raise HTTPException → request berhenti
    """
    try:
        # Decode JWT token
        # jwt.decode() akan error (JWTError) kalau:
        # - Token palsu (bukan dibuat dengan SECRET_KEY kita)
        # - Token sudah expired (kalau kita set expiry)
        # - Token rusak/korup
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Ambil username dari payload
        # .get() = ambil nilai, return None kalau key tidak ada
        username: str = payload.get("sub")

        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Token tidak valid: informasi user tidak ditemukan"
            )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Token tidak valid atau sudah expired. Silakan login ulang."
        )

    # Cari user di database berdasarkan username dari token
    user = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User tidak ditemukan. Token mungkin sudah tidak valid."
        )

    # Cek apakah akun masih aktif
    # (Admin bisa menonaktifkan akun, token lama jadi tidak bisa dipakai)
    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Akun telah dinonaktifkan. Hubungi Admin."
        )

    # Kalau semua cek lolos → return object User
    # Object ini akan jadi nilai parameter "current_user" di endpoint
    return user


def get_current_admin(
    user: models.User = Depends(get_current_user)
) -> models.User:
    """
    SATPAM KHUSUS ADMIN: Di atas get_current_user, tambah cek role.
    
    Ini adalah "dependency chain":
    get_current_admin → memanggil get_current_user → memanggil oauth2_scheme
    
    Kalau user sudah lolos get_current_user tapi role-nya bukan admin
    → tolak dengan 403 Forbidden
    
    403 vs 401:
    - 401 = "Kamu belum login / token tidak valid"
    - 403 = "Kamu sudah login, tapi tidak punya izin"
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=403,  # 403 = Forbidden
            detail="Akses ditolak. Halaman ini khusus Admin."
        )
    return user


def get_current_dokter(
    user: models.User = Depends(get_current_user)
) -> models.User:
    """
    SATPAM KHUSUS DOKTER: Sama seperti admin, tapi cek role dokter.
    
    Saat ini endpoint dokter juga bisa diakses admin (pakai get_current_user).
    Fungsi ini tersedia kalau nanti ada endpoint yang HANYA untuk dokter.
    """
    if user.role != "dokter":
        raise HTTPException(
            status_code=403,
            detail="Akses ditolak. Halaman ini khusus Dokter."
        )
    return user