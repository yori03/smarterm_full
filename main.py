from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import models
from auth import verify_password, create_access_token, get_password_hash
from database import engine, get_db
from routers import admin, dokter, medical
from schemas import RegisterAdminSchema, Token


models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SmartERM RSIA Al Hasanah",
    description="Sistem Rekam Medis Elektronik berbasis AI (Whisper + Llama 3)",
    version="2.0.0",
)

BASE_DIR     = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# STATIC FOLDER ASSET
# ─────────────────────────────────────────────
app.mount("/css",        StaticFiles(directory=FRONTEND_DIR / "css"),        name="css")
app.mount("/js",         StaticFiles(directory=FRONTEND_DIR / "js"),         name="js")
app.mount("/pages",      StaticFiles(directory=FRONTEND_DIR / "pages"),      name="pages")
app.mount("/animations", StaticFiles(directory=FRONTEND_DIR / "animations"), name="animations")


# ─────────────────────────────────────────────
# FILE STATIS GAMBAR — serve dari /pages/ karena
# logo & gambar disimpan di frontend/pages/
# ─────────────────────────────────────────────
@app.get("/logoalhasanah.png")
def serve_logo():
    return FileResponse(FRONTEND_DIR / "pages" / "logoalhasanah.png")

@app.get("/logo yayasan hijau.png")
def serve_logo_yayasan():
    return FileResponse(FRONTEND_DIR / "pages" / "logo yayasan hijau.png")

@app.get("/rsia-building.png")
def serve_building():
    return FileResponse(FRONTEND_DIR / "pages" / "rsia-building.png")


# ─────────────────────────────────────────────
# ROUTER API
# ─────────────────────────────────────────────
app.include_router(admin.router,   prefix="/admin",   tags=["Admin"])
app.include_router(dokter.router,  prefix="/dokter",  tags=["Manajemen Pasien"])
app.include_router(medical.router, prefix="/medical", tags=["AI & Rekam Medis"])


# ─────────────────────────────────────────────
# HALAMAN UTAMA
# ─────────────────────────────────────────────
@app.get("/")
def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/index.html")
def serve_index_html():
    return FileResponse(FRONTEND_DIR / "index.html")


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────
@app.post("/login", response_model=Token, tags=["Auth"])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Username atau password salah.")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Akun belum diaktifkan. Hubungi Admin.")

    token = create_access_token(data={"sub": user.username, "role": user.role})

    return {
        "access_token": token,
        "token_type":   "bearer",
        "role":         user.role,
        "nama_lengkap": user.nama_lengkap,
    }


@app.post("/register-admin", tags=["Auth"])
def register_admin(data: RegisterAdminSchema, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == data.username).first():
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
        "msg":     f"Akun admin '{data.nama_lengkap}' berhasil didaftarkan. Menunggu aktivasi.",
        "id_user": admin_baru.id_user,
    }


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/index.html")
    response.delete_cookie("access_token")
    response.delete_cookie("role")
    return response


@app.get("/health", tags=["Info"])
def health_check():
    return {
        "status": "✅ Server SmartERM Aktif!",
        "versi":  "2.0.0",
        "docs":   "Buka /docs untuk dokumentasi API lengkap",
    }