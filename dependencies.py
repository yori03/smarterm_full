"""
dependencies.py - Dependency Injection untuk Autentikasi

Fungsi-fungsi di sini berjalan SEBELUM endpoint utama dieksekusi —
seperti satpam yang memeriksa kartu akses sebelum memberi izin masuk.

Alur get_current_user():
    Request masuk
    → baca header "Authorization: Bearer <token>"
    → decode token → ambil username
    → cari user di database → cek is_active
    → kembalikan object User ke endpoint

Hirarki dependency:
    oauth2_scheme
        └── get_current_user          (semua user yang sudah login)
                ├── get_current_admin  (hanya role="admin")
                └── get_current_dokter (hanya role="dokter")
"""

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

import models
from config import ALGORITHM, SECRET_KEY
from database import get_db

# tokenUrl harus sama persis dengan URL endpoint POST /login di main.py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    Validasi JWT token dan kembalikan user yang sedang login.
    Dipakai di endpoint yang bisa diakses oleh dokter maupun admin.

    Raises:
        401 - token tidak valid, sudah expired, atau user tidak ditemukan
        400 - akun telah dinonaktifkan oleh admin
    """
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=401,
                detail="Token tidak valid: informasi user tidak ditemukan.",
            )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Token tidak valid atau sudah kadaluarsa. Silakan login ulang.",
        )

    user = db.query(models.User).filter(models.User.username == username).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User tidak ditemukan. Token mungkin sudah tidak berlaku.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Akun Anda telah dinonaktifkan. Hubungi Admin.",
        )

    return user


def get_current_admin(
    user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Pastikan user yang login adalah admin.
    Dipakai di endpoint yang hanya boleh diakses admin.

    Raises:
        403 - user sudah login tapi bukan admin
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Akses ditolak. Halaman ini khusus Admin.",
        )
    return user


def get_current_dokter(
    user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Pastikan user yang login adalah dokter.
    Tersedia untuk endpoint yang kelak hanya boleh diakses dokter.

    Raises:
        403 - user sudah login tapi bukan dokter
    """
    if user.role != "dokter":
        raise HTTPException(
            status_code=403,
            detail="Akses ditolak. Halaman ini khusus Dokter.",
        )
    return user