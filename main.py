from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import json
from dotenv import load_dotenv

# Import library Groq
from groq import Groq

# Import file lokal
import models
from database import engine, get_db

# --- KONFIGURASI ---
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "rahasia_super_aman") # Default kalau env belum ada
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Backend Rekam Medis AI")
client = Groq() # Pastikan API KEY sudah ada di Environment Variable

# --- SCHEMA / BENTUK DATA ---
class UserRegister(BaseModel):
    username: str
    password: str
    nama_lengkap: str 
    role: str = "dokter"

class UserLogin(BaseModel):
    username: str
    password: str

# --- FUNGSI KEAMANAN ---
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- JALUR API (ROUTES) ---

@app.get("/")
def home():
    return {"message": "Server Medis Siap - Database Terhubung!"}

# 1. REGISTER
@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(user: UserRegister, db: Session = Depends(get_db)):
    # Cek apakah email/username sudah ada (disini kita pakai username sbg email)
    cek_user = db.query(models.User).filter(models.User.email == user.username).first()
    if cek_user:
        raise HTTPException(status_code=400, detail="Email/Username sudah terdaftar")
    
    user_baru = models.User(
        email=user.username, # Mapping username form ke email database
        nama_lengkap=user.nama_lengkap,
        role=user.role,
        password=get_password_hash(user.password)
    )
    db.add(user_baru)
    db.commit()
    db.refresh(user_baru)
    
    return {"message": f"Dokter {user.nama_lengkap} berhasil didaftarkan!"}

# 2. LOGIN
@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    # Cari berdasarkan email
    db_user = db.query(models.User).filter(models.User.email == user.username).first()
    
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login Gagal")
    
    access_token = create_access_token(data={"sub": db_user.email, "role": db_user.role})
    return {"access_token": access_token, "token_type": "bearer"}

# 3. AI TRANSCRIBE & EXTRACT (Disesuaikan Database)
@app.post("/transcribe")
async def rekam_medis_ai(file: UploadFile = File(...)):
    # TAHAP 1: Audio ke Teks (Whisper)
    try:
        file_content = await file.read()
        transkripsi = client.audio.transcriptions.create(
            file=(file.filename, file_content),
            model="whisper-large-v3", 
            response_format="json",
            language="id",
            temperature=0.0
        )
        teks_mentah = transkripsi.text
        print(f"DEBUG TRANSKRIP: {teks_mentah}") 
    except Exception as e:
        return {"status": "error", "pesan": f"Gagal transkripsi: {str(e)}"}

    # TAHAP 2: Teks ke JSON (LLaMA 3)
    try:
        # Prompt KITA UPDATE agar sesuai Kolom Database
        system_prompt = """
        Anda adalah Asisten Medis AI Spesialis Kandungan (Obgyn). Tugas Anda mengekstrak data percakapan menjadi JSON.
        
        DATA YANG HARUS DIEKSTRAK (Sesuaikan kunci JSON dengan kolom ini):
        1. nama_pasien: String (Nama Ibu)
        2. keluhan_utama: String
        3. riwayat_penyakit_sekarang: String
        4. riwayat_penyakit_keluarga: String
        5. hpht: String (Format YYYY-MM-DD, jika disebut tanggalnya. Jika tidak null)
        6. hpl: String (Format YYYY-MM-DD, jika disebut/dihitung. Jika tidak null)
        7. tekanan_darah: String (Contoh '120/80')
        8. nadi: String (Contoh '80x/menit')
        9. suhu: String (Contoh '36.5 C')
        10. pernapasan: String (Contoh '20x/menit')
        11. pemeriksaan_fisik_lengkap: String (Rangkuman pemeriksaan fisik kepala, leher, perut, kaki, dll)
        12. diagnosa_utama: String (Assessment dokter)
        13. rencana_layanan: String (Planning dokter)
        14. resep_obat: String (Daftar obat yang diberikan)
        15. edukasi_pasien: String (Saran dokter ke pasien)

        ATURAN PENTING:
        - Jika tanggal disebutkan (misal: "20 September 2024"), ubah format jadi "2024-09-20".
        - Jika data tidak ada dalam percakapan, isi dengan null.
        - Output HANYA JSON murni.
        """

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Ekstrak data ini: '{teks_mentah}'"}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        hasil_json = json.loads(completion.choices[0].message.content)
        
        return {
            "status": "sukses",
            "teks_asli": teks_mentah,
            "data_medis": hasil_json
        }

    except Exception as e:
        print(f"ERROR AI: {str(e)}")
        return {"status": "error", "pesan": f"Gagal analisa AI: {str(e)}"}

# 4. SIMPAN KE DATABASE (Mapping Lengkap)
@app.post("/simpan-rm")
def simpan_rekam_medis(payload: dict, db: Session = Depends(get_db)):
    try:
        # Ambil bungkusan dalam
        data_isi = payload.get("data_medis") 
        
        if not data_isi:
            return {"error": "Gagal: Data medis kosong."}

        # Mapping JSON AI -> Kolom Database
        # Pastikan nama kiri (DB) sesuai models.py, nama kanan (get) sesuai prompt AI
        rm_baru = models.RekamMedis(
            # Header
            nama_pasien = data_isi.get("nama_pasien"),
            
            # Subjective
            keluhan_utama = data_isi.get("keluhan_utama"),
            riwayat_penyakit_sekarang = data_isi.get("riwayat_penyakit_sekarang"),
            riwayat_penyakit_keluarga = data_isi.get("riwayat_penyakit_keluarga"),
            
            # Kandungan (PENTING: Pastikan format tanggal YYYY-MM-DD dari AI)
            hpht = data_isi.get("hpht"),
            hpl = data_isi.get("hpl"),
            
            # Objective / Vital Sign
            tekanan_darah = data_isi.get("tekanan_darah"),
            nadi = data_isi.get("nadi"),
            suhu = data_isi.get("suhu"),
            pernapasan = data_isi.get("pernapasan"),
            pemeriksaan_fisik_lengkap = data_isi.get("pemeriksaan_fisik_lengkap"),
            
            # Assessment
            diagnosa_utama = data_isi.get("diagnosa_utama"),
            
            # Planning
            rencana_layanan = data_isi.get("rencana_layanan"),
            resep_obat = data_isi.get("resep_obat"),
            edukasi_pasien = data_isi.get("edukasi_pasien"),
            
            # Default Status
            status_record = 'final'
        )

        db.add(rm_baru)
        db.commit()
        db.refresh(rm_baru)

        return {
            "status": "Berhasil disimpan",
            "id_tersimpan": rm_baru.id_record
        }

    except Exception as e:
        print(f"ERROR DATABASE: {str(e)}")
        return {"error": f"Gagal menyimpan: {str(e)}"}