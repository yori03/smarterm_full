"""
auth.py - Fungsi Kriptografi & Token JWT

Analogi: Ini seperti bagian SECURITY SISTEM.
- Fungsi hash password = mesin penghancur dokumen (password asli → kode acak)
- Fungsi verify = mesin pencocok sidik jari
- Fungsi create_token = mesin cetak kartu akses (badge)
"""

import os
from passlib.context import CryptContext
from jose import jwt
from dotenv import load_dotenv

load_dotenv()

# Ambil konfigurasi dari .env
SECRET_KEY = os.getenv("SECRET_KEY", "ganti_ini_di_env_ya")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Mesin enkripsi password (bcrypt = algoritma paling aman untuk password)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Ubah password biasa → kode hash.
    Contoh: "password123" → "$2b$12$xyzabc..."
    Password asli TIDAK BISA dikembalikan dari hash ini (one-way).
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Cocokkan password yang diketik user dengan hash di database.
    Return True kalau cocok, False kalau tidak.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Buat JWT Token (kartu akses digital).
    
    Token berisi: username + role → di-encode jadi string panjang.
    Contoh output: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    
    Token ini dikirim ke HP dokter dan dipakai untuk setiap request
    (seperti badge yang di-scan setiap masuk ruangan).
    
    Catatan: Token ini TIDAK expired (sesuai .env lama kamu).
    Kalau mau ditambah expired, tambahkan 'exp' ke payload.
    """
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt