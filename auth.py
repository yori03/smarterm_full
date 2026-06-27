from jose import jwt
from passlib.context import CryptContext

from config import ALGORITHM, SECRET_KEY
from datetime import datetime, timedelta
# Mesin enkripsi password — bcrypt adalah algoritma paling aman untuk password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Ubah password biasa menjadi hash bcrypt untuk disimpan di database."""
    return pwd_context.hash(password)


def verify_password(password_biasa: str, password_hash: str) -> bool:
    """Cocokkan password yang diketik user dengan hash yang tersimpan di database."""
    return pwd_context.verify(password_biasa, password_hash)


def create_access_token(data: dict):
    payload = data.copy()

    payload["exp"] = datetime.utcnow() + timedelta(hours=8)

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )