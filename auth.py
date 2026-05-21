"""
auth.py - Kriptografi Password & Pembuatan JWT Token

Fungsi:
    get_password_hash()   : ubah password biasa → hash bcrypt (tidak bisa dikembalikan)
    verify_password()     : cocokkan password input dengan hash di database
    create_access_token() : buat JWT token yang dikirim ke client setelah login
"""

from jose import jwt
from passlib.context import CryptContext

from config import ALGORITHM, SECRET_KEY

# Mesin enkripsi password — bcrypt adalah algoritma paling aman untuk password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Ubah password biasa menjadi hash bcrypt untuk disimpan di database."""
    return pwd_context.hash(password)


def verify_password(password_biasa: str, password_hash: str) -> bool:
    """Cocokkan password yang diketik user dengan hash yang tersimpan di database."""
    return pwd_context.verify(password_biasa, password_hash)


def create_access_token(data: dict) -> str:
    """
    Buat JWT token dari data payload (berisi username + role).
    Token ini dikirim ke client dan dipakai sebagai bukti login di setiap request.

    Catatan: token tidak memiliki masa berlaku (tidak expired).
    Tambahkan key 'exp' ke payload jika ingin membatasi masa aktif token.
    """
    return jwt.encode(data.copy(), SECRET_KEY, algorithm=ALGORITHM)