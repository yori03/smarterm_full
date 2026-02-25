"""
routers/admin.py - Endpoint Khusus Admin

Endpoint di sini hanya bisa diakses oleh user dengan role='admin'.
Satpam yang dipakai: get_current_admin (dari dependencies.py)

Prefix dari mainbaru.py: "/admin"
Jadi URL lengkapnya: /admin/create-dokter, /admin/activate/1, dll.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import Token, RegisterAdminSchema, CreateDokterSchema
from auth import get_password_hash, verify_password, create_access_token
from dependencies import get_current_admin

# APIRouter = versi mini FastAPI, dikumpulkan nanti di main.py
router = APIRouter()


# =============================================================================
# LOGIN (Tidak butuh prefix /admin karena dipakai semua role)
# Tapi kita taruh di sini karena logikanya auth
# Di mainbaru.py nanti kita include tanpa prefix khusus
# =============================================================================

@router.post("/login", response_model=Token, tags=["Auth"])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login untuk semua user (admin & dokter).
    
    OAuth2PasswordRequestForm = format standar login:
    - username: string
    - password: string
    (Dikirim sebagai form-data, bukan JSON)
    
    Return: JWT Token + role user
    """
    # Cari user di database
    user = db.query(models.User).filter(models.User.username == form_data.username).first()

    # Cek username & password
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Username atau Password salah")

    # Cek status aktif
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Akun belum diaktifkan oleh Admin")

    # Buat token JWT
    # "sub" = subject (standar JWT untuk menyimpan identitas utama)
    token = create_access_token(data={"sub": user.username, "role": user.role})

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role
    }


# =============================================================================
# REGISTER ADMIN BARU
# =============================================================================

@router.post("/register-admin", tags=["Auth"])
def register_admin(
    data: RegisterAdminSchema,
    db: Session = Depends(get_db)
):
    """
    Daftarkan admin baru. Status awal is_active=False.
    Admin hanya bisa login setelah diaktifkan oleh admin lain.
    
    Tidak butuh login untuk registrasi (endpoint publik).
    """
    # Cek username sudah dipakai
    if db.query(models.User).filter(models.User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username sudah dipakai, coba yang lain")

    new_admin = models.User(
        username=data.username,
        password=get_password_hash(data.password),
        nama_lengkap=data.nama_lengkap,
        role="admin",
        is_active=False  # Harus diaktifkan manual oleh admin aktif lainnya
    )
    db.add(new_admin)
    db.commit()

    return {"msg": "Registrasi admin berhasil. Silakan hubungi admin aktif untuk aktivasi akun."}


# =============================================================================
# BUAT AKUN DOKTER (Khusus Admin)
# =============================================================================

@router.post("/create-dokter")
def create_dokter(
    data: CreateDokterSchema,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)  # ← Satpam Admin
):
    """
    Admin membuat akun dokter baru.
    Dokter yang dibuat admin langsung aktif (is_active=True).
    
    Butuh: Token admin yang valid di header Authorization.
    """
    if db.query(models.User).filter(models.User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username dokter sudah dipakai")

    new_dokter = models.User(
        username=data.username,
        password=get_password_hash(data.password),
        nama_lengkap=data.nama_lengkap,
        role="dokter",
        spesialisasi=data.spesialisasi,
        no_str=data.no_str,
        is_active=True  # Dokter langsung aktif, tidak perlu aktivasi
    )
    db.add(new_dokter)
    db.commit()

    return {"msg": f"Akun dokter '{data.nama_lengkap}' berhasil dibuat dan langsung aktif."}


# =============================================================================
# AKTIVASI AKUN USER (Khusus Admin)
# =============================================================================

@router.put("/activate/{user_id}")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)  # ← Satpam Admin
):
    """
    Admin mengaktifkan akun user (biasanya untuk admin baru yang baru register).
    
    Path parameter {user_id} = ID user yang mau diaktifkan.
    Contoh URL: PUT /admin/activate/5
    """
    user = db.query(models.User).filter(models.User.id_user == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User dengan ID {user_id} tidak ditemukan")

    user.is_active = True
    db.commit()

    return {"msg": f"Akun '{user.nama_lengkap}' ({user.role}) berhasil diaktifkan."}


# =============================================================================
# LIHAT SEMUA DOKTER (Khusus Admin)
# =============================================================================

@router.get("/list-dokter")
def list_dokter(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """
    Tampilkan semua akun dokter. Berguna untuk dashboard admin.
    """
    dokter_list = db.query(models.User).filter(models.User.role == "dokter").all()

    return {
        "total": len(dokter_list),
        "data": [
            {
                "id": d.id_user,
                "nama": d.nama_lengkap,
                "username": d.username,
                "spesialisasi": d.spesialisasi,
                "no_str": d.no_str,
                "aktif": d.is_active
            }
            for d in dokter_list
        ]
    }