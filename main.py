import os
import shutil
import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from dotenv import load_dotenv
from groq import Groq

import models
from database import engine, get_db

# --- 1. KONFIGURASI SISTEM ---
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "rahasia_super_aman_banget") # Ganti di .env nanti
ALGORITHM = "HS256"
GROQ_API_KEY = os.getenv("GROQ_API_KEY") # Pastikan ada di .env

# Buat folder temp untuk simpan audio sementara
os.makedirs("temp_files", exist_ok=True)

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Smarterm AI System V1.0")
client = Groq(api_key=GROQ_API_KEY)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# --- 2. SCHEMAS (Format Data) ---
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

class RegisterAdminSchema(BaseModel):
    username: str
    password: str
    nama_lengkap: str

class CreateDokterSchema(BaseModel):
    username: str
    password: str
    nama_lengkap: str
    spesialisasi: str
    no_str: str

# --- 3. HELPER FUNCTIONS (Fungsi Bantuan) ---
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Fungsi Kompresi Audio Otomatis (FFmpeg)
# Fungsi Kompresi Audio Otomatis (FFmpeg Direct)
def compress_audio_if_needed(file_path):
    """
    Cek ukuran file. Jika > 25MB, kompres jadi mono 32kbps pakai FFmpeg langsung.
    """
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"[SYSTEM] Ukuran file asli: {file_size_mb:.2f} MB")

    if file_size_mb > 24: # Batas aman 24MB
        print("[SYSTEM] File terlalu besar! Mengompres audio via FFmpeg...")
        
        # Nama file output
        compressed_path = file_path.replace(".", "_compressed.")
        
        # Perintah FFmpeg manual (Lebih stabil)
        # Artinya: ubah jadi mp3, 1 channel (mono), 16000Hz, bitrate 32k
        command = [
            "ffmpeg", "-y", "-i", file_path,
            "-ac", "1", "-ar", "16000", "-b:a", "32k",
            compressed_path
        ]
        
        try:
            # Python menyuruh Terminal menjalankan perintah di atas
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Cek ukuran baru
            new_size = os.path.getsize(compressed_path) / (1024 * 1024)
            print(f"[SYSTEM] Berhasil dikompres jadi: {new_size:.2f} MB")
            return compressed_path
            
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Gagal kompresi FFmpeg: {e}")
            return file_path # Kembalikan file asli kalau gagal
            
    return file_path
# --- 4. DEPENDENCY (Satpam Login) ---
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None: raise HTTPException(401, "Token invalid")
    except JWTError:
        raise HTTPException(401, "Token expired")
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user: raise HTTPException(401, "User not found")
    if not user.is_active: raise HTTPException(400, "Akun belum aktif")
    return user

def get_current_admin(user: models.User = Depends(get_current_user)):
    if user.role != "admin": raise HTTPException(403, "Khusus Admin")
    return user

# --- 5. ENDPOINTS AUTH (Fase 2 Kemarin) ---
@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(401, "Username/Password salah")
    if not user.is_active:
        raise HTTPException(400, "Akun belum diaktifkan Admin")
    
    token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "role": user.role}

@app.post("/auth/register-admin")
def register_admin(data: RegisterAdminSchema, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == data.username).first():
        raise HTTPException(400, "Username sudah dipakai")
    new_user = models.User(username=data.username, password=get_password_hash(data.password), 
                           nama_lengkap=data.nama_lengkap, role="admin", is_active=False)
    db.add(new_user); db.commit()
    return {"msg": "Registrasi sukses. Tunggu aktivasi."}

@app.post("/admin/create-dokter")
def create_dokter(data: CreateDokterSchema, db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)):
    if db.query(models.User).filter(models.User.username == data.username).first():
        raise HTTPException(400, "Username sudah dipakai")
    new_doc = models.User(username=data.username, password=get_password_hash(data.password),
                          nama_lengkap=data.nama_lengkap, role="dokter", spesialisasi=data.spesialisasi, 
                          no_str=data.no_str, is_active=True)
    db.add(new_doc); db.commit()
    return {"msg": "Dokter berhasil dibuat"}

@app.put("/admin/activate/{user_id}")
def activate_user(user_id: int, db: Session = Depends(get_db), admin: models.User = Depends(get_current_admin)):
    user = db.query(models.User).filter(models.User.id_user == user_id).first()
    if not user: raise HTTPException(404, "User not found")
    user.is_active = True; db.commit()
    return {"msg": "User aktif"}

# --- 6. ENDPOINT UTAMA AI (Fase 3 - Jantung Aplikasi) ---
@app.post("/transcribe")
async def diagnosa_cerdas(
    file: UploadFile = File(...), 
    current_user: models.User = Depends(get_current_user) # Harus Login dulu!
):
    """
    Menerima Audio -> Cek Ukuran (Kompres jika perlu) -> Whisper AI -> Llama 3 -> JSON
    """
    # 1. Simpan file upload ke folder temp
    temp_filename = f"temp_files/{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    final_path = temp_filename
    
    try:
        # 2. Cek & Kompres Audio (Pakai FFmpeg)
        final_path = compress_audio_if_needed(temp_filename)
        
        # 3. Kirim ke Whisper (Transkrip)
        print("[AI] Mengirim ke Whisper...")
        with open(final_path, "rb") as audio_file:
            transkripsi = client.audio.transcriptions.create(
                file=(final_path, audio_file.read()),
                model="whisper-large-v3",
                language="id", # Fokus Bahasa Indonesia
                response_format="json"
            )
        teks_mentah = transkripsi.text
        print(f"[AI] Transkrip Selesai: {teks_mentah[:50]}...") # Print 50 huruf awal aja

        # 4. Kirim ke Llama 3 (Parsing Medis)
        print("[AI] Mengolah data dengan Llama 3...")
        system_prompt = """
        Anda adalah Asisten Medis Spesialis Obgyn (Kandungan) RSIA Al Hasanah.
        Tugas: Ekstrak informasi penting dari percakapan dokter-pasien menjadi JSON.
        
        KOLOM YANG WAJIB DIISI (Sesuaikan dengan Database):
        - keluhan_utama: Apa yang dirasakan pasien?
        - riwayat_penyakit_sekarang: Detail keluhan.
        - riwayat_penyakit_keluarga: Penyakit turunan (jika ada).
        - hpht: Tanggal Hari Pertama Haid Terakhir (Format YYYY-MM-DD). Jika tidak ada, null.
        - hpl: Tanggal Perkiraan Lahir (Format YYYY-MM-DD). Jika tidak ada, null.
        - tekanan_darah: format '120/80'.
        - nadi: format '80x/menit'.
        - suhu: format '36.5'.
        - pemeriksaan_fisik_lengkap: Narasi pemeriksaan fisik (kepala, perut, kaki).
        - diagnosa_utama: Kesimpulan medis.
        - rencana_layanan: Tindakan selanjutnya / saran.
        - resep_obat: Obat yang disebutkan dokter.
        - edukasi_pasien: Nasihat dokter ke pasien.

        ATURAN:
        1. Output HANYA JSON. Jangan ada kata pengantar.
        2. Jika data tidak disebutkan, isi dengan null.
        3. Perbaiki ejaan obat jika terdengar salah.
        """

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analisa transkrip ini: '{teks_mentah}'"}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        hasil_json = json.loads(completion.choices[0].message.content)
        
        # 5. Bersih-bersih file sampah
        os.remove(temp_filename)
        if final_path != temp_filename: # Kalau tadi dikompres, hapus juga file kompresannya
            os.remove(final_path)

        return {
            "status": "success",
            "transkrip_asli": teks_mentah,
            "data_medis": hasil_json
        }

    except Exception as e:
        # Kalau error, tetap hapus file temp biar gak menuhin server
        if os.path.exists(temp_filename): os.remove(temp_filename)
        if os.path.exists(final_path) and final_path != temp_filename: os.remove(final_path)
        print(f"[ERROR] {str(e)}")
        raise HTTPException(500, f"Gagal memproses AI: {str(e)}")

# Jalankan server dengan: uvicorn main:app --reload
# --- 7. ENDPOINT SIMPAN REKAM MEDIS (Jembatan Terakhir) ---
# Ini dipakai setelah Dokter mengedit hasil AI di HP dan tekan "Simpan"

class SimpanRMSchema(BaseModel):
    # Kita terima ID pasien & dokter biar tau ini punya siapa
    no_rekam_medis: str 
    
    # Data SOAP (Boleh kosong/null kalau dokter hapus)
    keluhan_utama: Optional[str] = None
    riwayat_penyakit_sekarang: Optional[str] = None
    riwayat_penyakit_keluarga: Optional[str] = None
    hpht: Optional[str] = None # Format YYYY-MM-DD
    hpl: Optional[str] = None
    tekanan_darah: Optional[str] = None
    nadi: Optional[str] = None
    suhu: Optional[str] = None
    pernapasan: Optional[str] = None
    pemeriksaan_fisik_lengkap: Optional[str] = None
    diagnosa_utama: Optional[str] = None
    rencana_layanan: Optional[str] = None
    resep_obat: Optional[str] = None
    edukasi_pasien: Optional[str] = None

@app.post("/simpan-rm")
def simpan_rekam_medis(
    data: SimpanRMSchema, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Harus login
):
    # 1. Cari Pasien berdasarkan No RM
    pasien = db.query(models.Pasien).filter(models.Pasien.no_rekam_medis == data.no_rekam_medis).first()
    if not pasien:
        raise HTTPException(404, f"Pasien dengan No RM {data.no_rekam_medis} tidak ditemukan. Input data pasien dulu!")

    # 2. Konversi format tanggal (Jaga-jaga kalau AI kasih format aneh)
    def parse_date(date_str):
        if not date_str: return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            return None # Kalau format salah, biarkan null daripada error

    # 3. Masukkan ke Database
    rm_baru = models.RekamMedis(
        id_pasien = pasien.id_pasien,
        id_dokter = current_user.id_user, # Ambil ID dokter yang sedang login
        status_record = 'final',
        
        # SOAP Data
        keluhan_utama = data.keluhan_utama,
        riwayat_penyakit_sekarang = data.riwayat_penyakit_sekarang,
        riwayat_penyakit_keluarga = data.riwayat_penyakit_keluarga,
        hpht = parse_date(data.hpht),
        hpl = parse_date(data.hpl),
        tekanan_darah = data.tekanan_darah,
        nadi = data.nadi,
        suhu = data.suhu,
        pemeriksaan_fisik_lengkap = data.pemeriksaan_fisik_lengkap,
        diagnosa_utama = data.diagnosa_utama,
        rencana_layanan = data.rencana_layanan,
        resep_obat = data.resep_obat,
        edukasi_pasien = data.edukasi_pasien
    )

    db.add(rm_baru)
    db.commit()
    db.refresh(rm_baru)

    return {"msg": "Rekam Medis Berhasil Disimpan!", "id_record": rm_baru.id_record}