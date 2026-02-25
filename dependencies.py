"""
dependencies.py - Fungsi Dependency Injection (Satpam)

Analogi: Ini seperti SATPAM di pintu setiap ruangan.
Setiap endpoint yang butuh login akan "memanggil" satpam ini dulu.
Kalau token valid → boleh masuk.
Kalau token invalid/expired → langsung ditolak (401/403).

Kenapa dipisah ke file ini?
→ Supaya bisa dipakai di semua router tanpa copy-paste.
"""

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import os

import models
from database import get_db
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "ganti_ini_di_env_ya")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Memberitahu FastAPI: "Token ada di header Authorization: Bearer <token>"
# tokenUrl="login" = endpoint untuk dapat token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """
    Satpam Umum: Cek apakah token valid dan user ada di database.
    Dipakai oleh endpoint yang butuh login (dokter ATAU admin).
    
    Proses:
    1. Decode token JWT → ambil username
    2. Cari user di database
    3. Cek apakah akun aktif
    4. Return object User kalau semua lolos
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token tidak valid: username tidak ditemukan")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expired atau rusak")

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User tidak ditemukan di database")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Akun belum diaktifkan Admin")

    return user


def get_current_admin(
    user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Satpam Khusus Admin: Di atas get_current_user, tambah cek role.
    Dipakai di endpoint yang HANYA boleh diakses admin.
    """
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Akses ditolak: Khusus Admin")
    return user


def get_current_dokter(
    user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Satpam Khusus Dokter: Cek role dokter.
    Dipakai di endpoint yang HANYA boleh diakses dokter.
    """
    if user.role != "dokter":
        raise HTTPException(status_code=403, detail="Akses ditolak: Khusus Dokter")
    return user