"""
routers/admin.py - Endpoint Khusus Admin

KENAPA FILE INI ADA?
Memisahkan logika admin dari main.py supaya kode lebih rapi.
Semua endpoint di sini hanya bisa diakses oleh user dengan role="admin".

PERUBAHAN DARI VERSI SEBELUMNYA:
- Endpoint /login DIHAPUS dari sini → sudah dipindah ke main.py
- Endpoint /register-admin DIHAPUS dari sini → sudah dipindah ke main.py
- Alasan: login & register adalah aksi publik, bukan fitur khusus admin

PREFIX dari main.py: "/admin"
Jadi URL lengkapnya:
  POST /admin/create-dokter
  PUT  /admin/activate/{user_id}
  GET  /admin/list-dokter

HUBUNGAN DENGAN FILE LAIN:
admin.py → import dari:
  - database.py      (get_db → koneksi database)
  - models.py        (User → query database)
  - schemas.py       (CreateDokterSchema → validasi input)
  - auth.py          (get_password_hash → enkripsi password)
  - dependencies.py  (get_current_admin → satpam admin)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas import CreateDokterSchema
from auth import get_password_hash
from dependencies import get_current_admin

# APIRouter = versi mini FastAPI
# Kumpulan endpoint yang nanti digabung ke app utama di main.py
router = APIRouter()


# =============================================================================
# ENDPOINT 1: BUAT AKUN DOKTER
# URL: POST /admin/create-dokter
# Siapa yang bisa akses: Admin (butuh token admin yang valid)
# =============================================================================
@router.post("/create-dokter")
def create_dokter(
    data: CreateDokterSchema,
    db: Session = Depends(get_db),
    # get_current_admin akan:
    # 1. Ambil token dari header
    # 2. Decode → dapat username
    # 3. Cek role == "admin"
    # 4. Kalau bukan admin → tolak 403
    admin: models.User = Depends(get_current_admin)
):
    """
    Admin membuat akun dokter baru.
    
    Kenapa dokter tidak register sendiri?
    → Dokter adalah tenaga medis profesional yang harus diverifikasi RS
    → Admin yang membuatkan akun setelah verifikasi STR (Surat Tanda Registrasi)
    
    Berbeda dengan admin (yang bisa self-register tapi harus diaktifkan),
    dokter langsung aktif setelah admin membuatnya (is_active=True).
    """
    # Cek username sudah dipakai belum
    if db.query(models.User).filter(models.User.username == data.username).first():
        raise HTTPException(
            status_code=400,
            detail=f"Username '{data.username}' sudah dipakai. Gunakan username lain."
        )

    new_dokter = models.User(
        username=data.username,
        password=get_password_hash(data.password),  # WAJIB di-hash!
        nama_lengkap=data.nama_lengkap,
        role="dokter",
        spesialisasi=data.spesialisasi,
        no_str=data.no_str,
        is_active=True  # Dokter langsung aktif (sudah diverifikasi admin)
    )
    db.add(new_dokter)
    db.commit()
    db.refresh(new_dokter)

    # Log: siapa admin yang membuat akun dokter ini
    print(f"[ADMIN] {admin.nama_lengkap} membuat akun dokter: {data.nama_lengkap}")

    return {
        "msg": f"Akun dokter '{data.nama_lengkap}' berhasil dibuat dan langsung aktif.",
        "id_user": new_dokter.id_user,
        "username": new_dokter.username,
        "spesialisasi": new_dokter.spesialisasi,
        "dibuat_oleh": admin.nama_lengkap
    }


# =============================================================================
# ENDPOINT 2: AKTIVASI AKUN USER
# URL: PUT /admin/activate/{user_id}
# Siapa yang bisa akses: Admin
#
# Kapan dipakai?
# → Setelah admin baru register via POST /register-admin
# → Admin yang sudah aktif login → aktifkan admin baru
# =============================================================================
@router.put("/activate/{user_id}")
def activate_user(
    user_id: int,        # Diambil dari URL path, contoh: /admin/activate/5
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """
    Aktifkan akun user berdasarkan ID.
    
    {user_id} adalah path parameter → diambil langsung dari URL.
    Contoh: PUT /admin/activate/5 → user_id = 5
    """
    # Cari user berdasarkan ID
    user = db.query(models.User).filter(
        models.User.id_user == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User dengan ID {user_id} tidak ditemukan."
        )

    # Cek kalau sudah aktif (hindari double aktivasi)
    if user.is_active:
        return {"msg": f"Akun '{user.nama_lengkap}' sudah aktif sebelumnya."}

    user.is_active = True
    db.commit()

    print(f"[ADMIN] {admin.nama_lengkap} mengaktifkan akun: {user.nama_lengkap} ({user.role})")

    return {
        "msg": f"Akun '{user.nama_lengkap}' ({user.role}) berhasil diaktifkan.",
        "diaktifkan_oleh": admin.nama_lengkap
    }


# =============================================================================
# ENDPOINT 3: LIHAT SEMUA DOKTER
# URL: GET /admin/list-dokter
# Siapa yang bisa akses: Admin
# =============================================================================
@router.get("/list-dokter")
def list_dokter(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """
    Tampilkan semua akun dokter yang terdaftar.
    Berguna untuk dashboard admin.
    """
    dokter_list = db.query(models.User).filter(
        models.User.role == "dokter"
    ).all()

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


# =============================================================================
# ENDPOINT 4: LIHAT SEMUA USER YANG MENUNGGU AKTIVASI
# URL: GET /admin/pending-aktivasi
# Siapa yang bisa akses: Admin
# =============================================================================
@router.get("/pending-aktivasi")
def pending_aktivasi(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin)
):
    """
    Tampilkan semua user yang belum diaktifkan (is_active=False).
    Berguna agar admin tahu siapa saja yang menunggu persetujuan.
    """
    pending = db.query(models.User).filter(
        models.User.is_active == False
    ).all()

    return {
        "total_pending": len(pending),
        "data": [
            {
                "id": u.id_user,
                "nama": u.nama_lengkap,
                "username": u.username,
                "role": u.role,
                "terdaftar": str(u.created_at)
            }
            for u in pending
        ]
    }