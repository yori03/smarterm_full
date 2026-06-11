"""
routers/admin.py — Endpoint khusus Admin
Prefix dari main.py: "/admin"

Daftar URL:
    POST /admin/create-dokter              → buat akun dokter baru (langsung aktif)
    PUT  /admin/activate/{user_id}         → aktifkan akun pending
    GET  /admin/list-dokter                → daftar semua dokter
    PUT  /admin/edit-dokter/{user_id}      → edit data dokter
    DELETE /admin/hapus-dokter/{user_id}   → hapus atau nonaktifkan dokter

    GET  /admin/list-admin                 → daftar semua admin
    POST /admin/create-admin               → buat akun admin baru (langsung aktif)
    PUT  /admin/edit-admin/{user_id}       → edit data admin
    DELETE /admin/hapus-admin/{user_id}    → hapus admin (permanen)

    GET  /admin/pending-aktivasi           → daftar akun belum aktif
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from auth import get_password_hash
from database import get_db
from dependencies import get_current_admin
from schemas import (
    CreateAdminSchema,
    CreateDokterSchema,
    EditAdminSchema,
    EditDokterSchema,
)

router = APIRouter()


# =============================================================================
# DOKTER
# =============================================================================

@router.post("/create-dokter")
def create_dokter(
    data: CreateDokterSchema,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    """Buat akun dokter baru. Langsung aktif tanpa perlu aktivasi."""
    if db.query(models.User).filter(models.User.username == data.username).first():
        raise HTTPException(
            status_code=400,
            detail=f"Username '{data.username}' sudah dipakai. Gunakan username lain.",
        )

    dokter_baru = models.User(
        username=data.username,
        password=get_password_hash(data.password),
        nama_lengkap=data.nama_lengkap,
        role="dokter",
        spesialisasi=data.spesialisasi,
        no_str=data.no_str,
        is_active=True,
    )
    db.add(dokter_baru)
    db.commit()
    db.refresh(dokter_baru)

    print(f"[ADMIN] {admin.nama_lengkap} membuat akun dokter: {data.nama_lengkap}")

    return {
        "msg":         f"Akun dokter '{data.nama_lengkap}' berhasil dibuat.",
        "id_user":      dokter_baru.id_user,
        "username":     dokter_baru.username,
        "spesialisasi": dokter_baru.spesialisasi,
        "dibuat_oleh":  admin.nama_lengkap,
    }


@router.get("/list-dokter")
def list_dokter(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    """Daftar semua akun dengan role dokter."""
    semua_dokter = db.query(models.User).filter(models.User.role == "dokter").all()

    return {
        "total": len(semua_dokter),
        "data": [
            {
                "id":           d.id_user,
                "nama":         d.nama_lengkap,
                "username":     d.username,
                "spesialisasi": d.spesialisasi,
                "no_str":       d.no_str,
                "aktif":        d.is_active,
                "terdaftar":    str(d.created_at),
            }
            for d in semua_dokter
        ],
    }


@router.put("/edit-dokter/{user_id}")
def edit_dokter(
    user_id: int,
    data: EditDokterSchema,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    """Edit data dokter: nama, username, spesialisasi, no_str, status aktif, password (opsional)."""
    dokter = db.query(models.User).filter(
        models.User.id_user == user_id,
        models.User.role == "dokter",
    ).first()

    if not dokter:
        raise HTTPException(
            status_code=404,
            detail=f"Dokter dengan ID {user_id} tidak ditemukan.",
        )

    # Cek username tidak bentrok dengan user lain
    if data.username and data.username != dokter.username:
        sudah_ada = db.query(models.User).filter(
            models.User.username == data.username,
            models.User.id_user != user_id,
        ).first()
        if sudah_ada:
            raise HTTPException(
                status_code=400,
                detail=f"Username '{data.username}' sudah dipakai user lain.",
            )

    # Update field yang dikirim (skip None)
    if data.nama_lengkap is not None:
        dokter.nama_lengkap = data.nama_lengkap
    if data.username is not None:
        dokter.username = data.username
    if data.spesialisasi is not None:
        dokter.spesialisasi = data.spesialisasi
    if data.no_str is not None:
        dokter.no_str = data.no_str
    if data.is_active is not None:
        dokter.is_active = data.is_active
    if data.password:                               # hanya update jika dikirim & tidak kosong
        if len(data.password) < 6:
            raise HTTPException(status_code=400, detail="Password minimal 6 karakter.")
        dokter.password = get_password_hash(data.password)

    db.commit()
    db.refresh(dokter)

    print(f"[ADMIN] {admin.nama_lengkap} mengedit dokter ID {user_id}: {dokter.nama_lengkap}")

    return {
        "msg":      f"Data dokter '{dokter.nama_lengkap}' berhasil diperbarui.",
        "id_user":   dokter.id_user,
        "username":  dokter.username,
        "aktif":     dokter.is_active,
    }


@router.delete("/hapus-dokter/{user_id}")
def hapus_dokter(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    """
    Hapus akun dokter.
    - Jika dokter PUNYA rekam medis → nonaktifkan saja (soft delete), data rekam medis tetap aman.
    - Jika dokter TIDAK PUNYA rekam medis → hapus permanen.
    """
    dokter = db.query(models.User).filter(
        models.User.id_user == user_id,
        models.User.role == "dokter",
    ).first()

    if not dokter:
        raise HTTPException(
            status_code=404,
            detail=f"Dokter dengan ID {user_id} tidak ditemukan.",
        )

    punya_rekam_medis = db.query(models.RekamMedis).filter(
        models.RekamMedis.id_dokter == user_id
    ).first()

    nama_dokter = dokter.nama_lengkap

    if punya_rekam_medis:
        # Soft delete — nonaktifkan agar rekam medis historis tidak yatim
        dokter.is_active = False
        db.commit()
        print(f"[ADMIN] {admin.nama_lengkap} menonaktifkan dokter: {nama_dokter} (punya rekam medis)")
        return {
            "msg":   f"Akun dokter '{nama_dokter}' dinonaktifkan (memiliki data rekam medis).",
            "aksi":  "nonaktif",
        }
    else:
        # Hard delete — aman karena tidak ada rekam medis yang merujuk akun ini
        db.delete(dokter)
        db.commit()
        print(f"[ADMIN] {admin.nama_lengkap} menghapus permanen dokter: {nama_dokter}")
        return {
            "msg":  f"Akun dokter '{nama_dokter}' berhasil dihapus permanen.",
            "aksi": "hapus",
        }


# =============================================================================
# ADMIN
# =============================================================================

@router.get("/list-admin")
def list_admin(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    """Daftar semua akun dengan role admin."""
    semua_admin = db.query(models.User).filter(models.User.role == "admin").all()

    return {
        "total": len(semua_admin),
        "data": [
            {
                "id":        a.id_user,
                "nama":      a.nama_lengkap,
                "username":  a.username,
                "aktif":     a.is_active,
                "terdaftar": str(a.created_at),
            }
            for a in semua_admin
        ],
    }


@router.post("/create-admin")
def create_admin(
    data: CreateAdminSchema,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    """Buat akun admin baru. Langsung aktif (dibuat oleh admin yang sedang login)."""
    if db.query(models.User).filter(models.User.username == data.username).first():
        raise HTTPException(
            status_code=400,
            detail=f"Username '{data.username}' sudah dipakai. Gunakan username lain.",
        )

    admin_baru = models.User(
        username=data.username,
        password=get_password_hash(data.password),
        nama_lengkap=data.nama_lengkap,
        role="admin",
        is_active=True,          # langsung aktif karena dibuat langsung oleh admin
    )
    db.add(admin_baru)
    db.commit()
    db.refresh(admin_baru)

    print(f"[ADMIN] {admin.nama_lengkap} membuat akun admin baru: {data.nama_lengkap}")

    return {
        "msg":        f"Akun admin '{data.nama_lengkap}' berhasil dibuat.",
        "id_user":     admin_baru.id_user,
        "username":    admin_baru.username,
        "dibuat_oleh": admin.nama_lengkap,
    }


@router.put("/edit-admin/{user_id}")
def edit_admin(
    user_id: int,
    data: EditAdminSchema,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    """Edit data admin: nama, username, status aktif, password (opsional)."""
    target = db.query(models.User).filter(
        models.User.id_user == user_id,
        models.User.role == "admin",
    ).first()

    if not target:
        raise HTTPException(
            status_code=404,
            detail=f"Admin dengan ID {user_id} tidak ditemukan.",
        )

    # Cek username tidak bentrok dengan user lain
    if data.username and data.username != target.username:
        sudah_ada = db.query(models.User).filter(
            models.User.username == data.username,
            models.User.id_user != user_id,
        ).first()
        if sudah_ada:
            raise HTTPException(
                status_code=400,
                detail=f"Username '{data.username}' sudah dipakai user lain.",
            )

    if data.nama_lengkap is not None:
        target.nama_lengkap = data.nama_lengkap
    if data.username is not None:
        target.username = data.username
    if data.is_active is not None:
        target.is_active = data.is_active
    if data.password:
        if len(data.password) < 6:
            raise HTTPException(status_code=400, detail="Password minimal 6 karakter.")
        target.password = get_password_hash(data.password)

    db.commit()
    db.refresh(target)

    print(f"[ADMIN] {admin.nama_lengkap} mengedit admin ID {user_id}: {target.nama_lengkap}")

    return {
        "msg":     f"Data admin '{target.nama_lengkap}' berhasil diperbarui.",
        "id_user":  target.id_user,
        "username": target.username,
        "aktif":    target.is_active,
    }


@router.delete("/hapus-admin/{user_id}")
def hapus_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    """
    Hapus akun admin secara permanen.
    Admin tidak bisa menghapus akunnya sendiri.
    """
    if admin.id_user == user_id:
        raise HTTPException(
            status_code=400,
            detail="Tidak bisa menghapus akun Anda sendiri.",
        )

    target = db.query(models.User).filter(
        models.User.id_user == user_id,
        models.User.role == "admin",
    ).first()

    if not target:
        raise HTTPException(
            status_code=404,
            detail=f"Admin dengan ID {user_id} tidak ditemukan.",
        )

    nama_target = target.nama_lengkap
    db.delete(target)
    db.commit()

    print(f"[ADMIN] {admin.nama_lengkap} menghapus admin: {nama_target}")

    return {
        "msg":  f"Akun admin '{nama_target}' berhasil dihapus.",
        "aksi": "hapus",
    }


# =============================================================================
# PENDING AKTIVASI AKUN DOKTER
# =============================================================================

@router.put("/activate/{user_id}")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    """Aktifkan akun yang belum aktif (dari jalur register mandiri)."""
    user = db.query(models.User).filter(models.User.id_user == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User dengan ID {user_id} tidak ditemukan.",
        )

    if user.is_active:
        return {"msg": f"Akun '{user.nama_lengkap}' sudah aktif sebelumnya."}

    user.is_active = True
    db.commit()

    print(f"[ADMIN] {admin.nama_lengkap} mengaktifkan: {user.nama_lengkap} ({user.role})")

    return {
        "msg":             f"Akun '{user.nama_lengkap}' ({user.role}) berhasil diaktifkan.",
        "diaktifkan_oleh": admin.nama_lengkap,
    }


@router.get("/pending-aktivasi")
def pending_aktivasi(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    """Daftar semua akun yang belum aktif (is_active = False)."""
    akun_pending = db.query(models.User).filter(
        models.User.is_active.is_(False)
    ).all()

    return {
        "total_pending": len(akun_pending),
        "data": [
            {
                "id":        u.id_user,
                "nama":      u.nama_lengkap,
                "username":  u.username,
                "role":      u.role,
                "terdaftar": str(u.created_at),
            }
            for u in akun_pending
        ],
    }