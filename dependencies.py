from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

import models
from config import ALGORITHM, SECRET_KEY
from database import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

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

    user = (
        db.query(models.User)
        .filter(models.User.username == username)
        .first()
    )

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

    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Akses ditolak. Halaman ini khusus Admin.",
        )

    return user


def get_current_dokter(
    user: models.User = Depends(get_current_user),
) -> models.User:

    if user.role != "dokter":
        raise HTTPException(
            status_code=403,
            detail="Akses ditolak. Halaman ini khusus Dokter.",
        )

    return user