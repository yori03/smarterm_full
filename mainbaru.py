from fastapi import FastAPI
import models
from database import engine
from routers import admin, dokter, medical # Import rute

# Buat tabel otomatis
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SmartERM RSIA Al Hasanah")

# PANGGIL SEMUA ROUTER
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(dokter.router, prefix="/dokter", tags=["Dokter"])
app.include_router(medical.router, prefix="/medical", tags=["AI & Records"])

@app.get("/")
def home():
    return {"status": "Server SmartERM Aktif!"}