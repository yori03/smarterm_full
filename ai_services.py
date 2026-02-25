"""
ai_services.py - Semua Logika AI (Whisper + Llama 3)

Analogi: Ini seperti LABORATORIUM AI.
- compress_audio() = mesin kompresi file besar
- transcribe_audio() = mesin penerjemah suara → teks (Whisper)
- parse_medical_text() = dokter AI yang baca teks → JSON medis (Llama 3)

Kenapa dipisah?
→ Kalau mau ganti model AI (misal dari Groq ke OpenAI),
  cukup edit file ini, tidak perlu otak-atik router/endpoint.
"""

import os
import json
import subprocess
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Inisialisasi client Groq (koneksi ke server AI Groq)
# Groq adalah platform yang nyediain Whisper + Llama 3 dengan kecepatan tinggi
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def compress_audio(file_path: str) -> str:
    """
    Cek ukuran file audio. Kalau > 24MB, kompres pakai FFmpeg.
    
    Kenapa 24MB? Karena limit Whisper API adalah 25MB.
    Kita kasih buffer 1MB untuk keamanan.
    
    FFmpeg = software gratis untuk olah audio/video di server.
    Command yang dijalankan:
      ffmpeg -y -i [input] -ac 1 -ar 16000 -b:a 32k [output]
      
      -ac 1     = ubah jadi mono (1 channel, bukan stereo)
      -ar 16000 = sample rate 16kHz (cukup untuk voice/bicara)
      -b:a 32k  = bitrate 32kbps (kualitas rendah tapi cukup untuk transkripsi)
    
    Return: path file yang siap dikirim ke Whisper
    """
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"[AUDIO] Ukuran file: {file_size_mb:.2f} MB")

    if file_size_mb <= 24:
        print("[AUDIO] Ukuran OK, tidak perlu kompres.")
        return file_path

    print("[AUDIO] File terlalu besar! Mengompres via FFmpeg...")

    # Buat nama file output: "rekaman.mp3" → "rekaman_compressed.mp3"
    base, ext = os.path.splitext(file_path)
    compressed_path = f"{base}_compressed{ext}"

    command = [
        "ffmpeg", "-y",           # -y = overwrite kalau file sudah ada
        "-i", file_path,           # input file
        "-ac", "1",                # mono
        "-ar", "16000",            # sample rate 16kHz
        "-b:a", "32k",             # bitrate 32kbps
        compressed_path            # output file
    ]

    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,  # Sembunyikan output FFmpeg
            stderr=subprocess.DEVNULL
        )
        new_size = os.path.getsize(compressed_path) / (1024 * 1024)
        print(f"[AUDIO] Berhasil dikompres: {new_size:.2f} MB")
        return compressed_path

    except subprocess.CalledProcessError as e:
        print(f"[AUDIO] Gagal kompres: {e}. Pakai file asli.")
        return file_path  # Fallback ke file asli kalau FFmpeg error


def transcribe_audio(audio_path: str) -> str:
    """
    Kirim file audio ke Whisper AI → dapat teks transkripsi.
    
    Whisper = Model AI buatan OpenAI, sangat bagus untuk transkripsi bahasa Indonesia.
    Kita pakai versi whisper-large-v3 via Groq (lebih cepat dari OpenAI langsung).
    
    Return: String teks hasil transkripsi
    """
    print("[AI] Mengirim audio ke Whisper...")

    with open(audio_path, "rb") as audio_file:
        transkripsi = client.audio.transcriptions.create(
            file=(audio_path, audio_file.read()),
            model="whisper-large-v3",
            language="id",              # Paksa Bahasa Indonesia
            response_format="json"
        )

    teks = transkripsi.text
    print(f"[AI] Transkripsi selesai: '{teks[:80]}...'")
    return teks


def parse_medical_text(teks_mentah: str) -> dict:
    """
    Kirim teks transkripsi ke Llama 3 → dapat JSON data medis terstruktur.
    
    Llama 3 = Model AI buatan Meta (Facebook), sangat pintar memahami konteks.
    temperature=0.1 = output lebih konsisten/deterministik (tidak kreatif-kreatif)
    response_format json_object = paksa output JSON valid
    
    System prompt dirancang khusus untuk konteks RSIA (Rumah Sakit Ibu & Anak)
    dengan kolom-kolom yang sesuai schema database kita.
    
    Return: Dictionary (dict) berisi data medis terstruktur
    """
    print("[AI] Menganalisis teks dengan Llama 3...")

    system_prompt = """
    Anda adalah Asisten Medis Spesialis Obgyn (Kandungan) RSIA Al Hasanah.
    Tugas: Ekstrak informasi penting dari percakapan dokter-pasien menjadi JSON.
    
    KOLOM YANG WAJIB DIISI:
    - keluhan_utama: Apa yang dirasakan pasien?
    - riwayat_penyakit_sekarang: Detail keluhan dan kronologi.
    - riwayat_penyakit_keluarga: Penyakit turunan (jika disebutkan).
    - hpht: Hari Pertama Haid Terakhir (Format YYYY-MM-DD atau null).
    - hpl: Perkiraan Tanggal Lahir (Format YYYY-MM-DD atau null).
    - tekanan_darah: Contoh format '120/80'.
    - nadi: Contoh format '80x/menit'.
    - suhu: Contoh format '36.5'.
    - pemeriksaan_fisik_lengkap: Narasi pemeriksaan fisik lengkap.
    - diagnosa_utama: Kesimpulan diagnosis medis.
    - rencana_layanan: Tindakan selanjutnya / rencana pengobatan.
    - resep_obat: Daftar obat yang diresepkan dokter.
    - edukasi_pasien: Nasihat / edukasi dokter kepada pasien.

    ATURAN WAJIB:
    1. Output HANYA berupa JSON. Tidak ada kata pembuka/penutup sama sekali.
    2. Jika data tidak disebutkan dalam percakapan, isi dengan null (bukan string kosong).
    3. Perbaiki ejaan nama obat jika terdengar salah dalam transkripsi.
    4. Interpretasikan konteks medis dengan benar (contoh: 'tensi' = tekanan_darah).
    """

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analisa percakapan medis ini dan ekstrak datanya: '{teks_mentah}'"}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}  # Paksa output JSON valid
    )

    hasil_json = json.loads(completion.choices[0].message.content)
    print("[AI] Parsing Llama 3 selesai.")
    return hasil_json