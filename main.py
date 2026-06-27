from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import models
from auth import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from database import engine, get_db
from routers import admin, dokter, medical
from schemas import RegisterAdminSchema, Token


# =============================================================================
# APP
# =============================================================================

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SmartERM RSIA Al Hasanah",
    description="Sistem Rekam Medis Elektronik berbasis AI",
    version="2.0.0",
)


# =============================================================================
# PATH
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
PAGES_DIR = FRONTEND_DIR / "pages"


# =============================================================================
# MIDDLEWARE
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_FOLDERS = {
    "css": FRONTEND_DIR / "css",
    "js": FRONTEND_DIR / "js",
    "pages": FRONTEND_DIR / "pages",
    "animations": FRONTEND_DIR / "animations",
}

for route_name, directory in STATIC_FOLDERS.items():
    app.mount(
        f"/{route_name}",
        StaticFiles(directory=directory),
        name=route_name,
    )


# =============================================================================
# IMAGE ASSETS
# =============================================================================

@app.get("/logoalhasanah.png")
def logo_alhasanah():
    return FileResponse(PAGES_DIR / "logoalhasanah.png")


@app.get("/logo yayasan hijau.png")
def logo_yayasan():
    return FileResponse(PAGES_DIR / "logo yayasan hijau.png")


@app.get("/rsia-building.png")
def rsia_building():
    return FileResponse(PAGES_DIR / "rsia-building.png")


# =============================================================================
# ROUTERS
# =============================================================================

app.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin"],
)

app.include_router(
    dokter.router,
    prefix="/dokter",
    tags=["Manajemen Pasien"],
)

app.include_router(
    medical.router,
    prefix="/medical",
    tags=["AI & Rekam Medis"],
)


# =============================================================================
# FRONTEND
# =============================================================================

@app.get("/")
def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/index.html")
def serve_index_html():
    return FileResponse(FRONTEND_DIR / "index.html")


# =============================================================================
# AUTH
# =============================================================================

@app.post(
    "/login",
    response_model=Token,
    tags=["Auth"],
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.username == form_data.username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Username atau password salah.",
        )

    if not verify_password(
        form_data.password,
        user.password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Username atau password salah.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Akun belum diaktifkan. Hubungi Admin.",
        )

    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "nama_lengkap": user.nama_lengkap,
    }


@app.post(
    "/register-admin",
    tags=["Auth"],
)
def register_admin(
    data: RegisterAdminSchema,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(models.User)
        .filter(models.User.username == data.username)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail=f"Username '{data.username}' sudah dipakai. Coba username lain.",
        )

    admin_baru = models.User(
        username=data.username,
        password=get_password_hash(data.password),
        nama_lengkap=data.nama_lengkap,
        role="admin",
        is_active=False,
    )

    db.add(admin_baru)
    db.commit()
    db.refresh(admin_baru)

    return {
        "msg": (
            f"Akun admin '{data.nama_lengkap}' "
            f"berhasil didaftarkan. Menunggu aktivasi."
        ),
        "id_user": admin_baru.id_user,
    }


@app.get("/logout")
def logout():
    response = RedirectResponse(
        url="/index.html"
    )

    response.delete_cookie("access_token")
    response.delete_cookie("role")

    return response


# =============================================================================
# SYSTEM
# =============================================================================

@app.get(
    "/health",
    tags=["Info"],
)
def health_check():
    return {
        "status": "✅ Server SmartERM Aktif!",
        "versi": "2.0.0",
        "docs": "/docs",
    }