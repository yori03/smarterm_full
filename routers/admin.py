from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from auth import get_password_hash
from database import get_db
from dependencies import get_current_admin
from schemas import CreateDokterSchema

router = APIRouter()


@router.post("/create-dokter")
def create_dokter(
    data: CreateDokterSchema,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    username_sudah_ada = db.query(models.User).filter(
        models.User.username == data.username
    ).first()

    if username_sudah_ada:
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

@router.put("/activate/{user_id}")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
  
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

    print(f"[ADMIN] {admin.nama_lengkap} mengaktifkan akun: {user.nama_lengkap} ({user.role})")

    return {
        "msg":             f"Akun '{user.nama_lengkap}' ({user.role}) berhasil diaktifkan.",
        "diaktifkan_oleh": admin.nama_lengkap,
    }

@router.get("/list-dokter")
def list_dokter(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    semua_dokter = db.query(models.User).filter(models.User.role == "dokter").all()

    return {
        "total": len(semua_dokter),
        "data": [
            {
                "id":          d.id_user,
                "nama":        d.nama_lengkap,
                "username":    d.username,
                "spesialisasi": d.spesialisasi,
                "no_str":      d.no_str,
                "aktif":       d.is_active,
            }
            for d in semua_dokter
        ],
    }


@router.get("/pending-aktivasi")
def pending_aktivasi(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    
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