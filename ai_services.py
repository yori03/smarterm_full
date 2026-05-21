"""
ai_services.py - Layanan AI (Whisper + Llama 3 via Groq)

Berisi semua logika pemrosesan AI:
    compress_audio()     : kompres file audio > 24MB menggunakan FFmpeg
    transcribe_audio()   : kirim audio ke Whisper → teks transkripsi Bahasa Indonesia
    parse_medical_text() : kirim teks ke Llama 3 → JSON data medis terstruktur

Memisahkan logika AI ke file ini memudahkan penggantian provider AI
(misal dari Groq ke OpenAI) tanpa perlu menyentuh kode router sama sekali.
"""

import json
import os
import subprocess
from typing import Optional

from groq import Groq

from config import GROQ_API_KEY

# Koneksi ke Groq — penyedia API Whisper & Llama 3 dengan latensi rendah
klien_groq = Groq(api_key=GROQ_API_KEY)

# Batas ukuran file sebelum dikompres (Whisper API max 25MB, pakai 24MB sebagai buffer)
BATAS_UKURAN_MB = 24

# Instruksi sistem untuk Llama 3 — menentukan cara AI mengekstrak data medis
PROMPT_SISTEM_MEDIS = """
Anda adalah Asisten Medis Spesialis Obgyn (Kandungan) RSIA Al Hasanah.
Tugas: Ekstrak informasi penting dari percakapan dokter-pasien menjadi JSON.

KOLOM YANG WAJIB DIISI:
- keluhan_utama              : Apa yang dirasakan pasien?
- riwayat_penyakit_sekarang  : Detail keluhan dan kronologi.
- riwayat_penyakit_keluarga  : Penyakit turunan (jika disebutkan).
- hpht                       : Hari Pertama Haid Terakhir (YYYY-MM-DD atau null).
- hpl                        : Perkiraan Tanggal Lahir (YYYY-MM-DD atau null).
- tekanan_darah              : Contoh format '120/80'.
- nadi                       : Contoh format '80x/menit'.
- suhu                       : Contoh format '36.5'.
- pemeriksaan_fisik_lengkap  : Narasi pemeriksaan fisik lengkap.
- diagnosa_utama             : Kesimpulan diagnosis medis.
- rencana_layanan            : Tindakan selanjutnya / rencana pengobatan.
- resep_obat                 : Daftar obat yang diresepkan dokter.
- edukasi_pasien             : Nasihat / edukasi dokter kepada pasien.

ATURAN WAJIB:
1. Output HANYA berupa JSON. Tidak ada kata pembuka/penutup sama sekali.
2. Jika data tidak disebutkan dalam percakapan, isi dengan null (bukan string kosong).
3. Perbaiki ejaan nama obat jika terdengar salah dalam transkripsi.
4. Interpretasikan konteks medis dengan benar (contoh: 'tensi' = tekanan_darah).
"""


def compress_audio(path_file: str) -> str:
    """
    Periksa ukuran file audio. Jika melebihi batas, kompres menggunakan FFmpeg.

    Parameter FFmpeg yang digunakan:
        -ac 1      : ubah ke mono (1 channel) — hemat ukuran, cukup untuk rekaman suara
        -ar 16000  : sample rate 16kHz
        -b:a 32k   : bitrate 32kbps

    Returns:
        Path file yang siap dikirim ke Whisper (file asli atau hasil kompresi).
    """
    ukuran_mb = os.path.getsize(path_file) / (1024 * 1024)
    print(f"[AUDIO] Ukuran file: {ukuran_mb:.2f} MB")

    if ukuran_mb <= BATAS_UKURAN_MB:
        print("[AUDIO] Ukuran OK, tidak perlu dikompres.")
        return path_file

    print("[AUDIO] File terlalu besar, mengompres via FFmpeg...")

    nama_dasar, ekstensi = os.path.splitext(path_file)
    path_hasil_kompres   = f"{nama_dasar}_compressed{ekstensi}"

    perintah_ffmpeg = [
        "ffmpeg", "-y",
        "-i", path_file,
        "-ac", "1",
        "-ar", "16000",
        "-b:a", "32k",
        path_hasil_kompres,
    ]

    try:
        subprocess.run(
            perintah_ffmpeg,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ukuran_baru = os.path.getsize(path_hasil_kompres) / (1024 * 1024)
        print(f"[AUDIO] Kompresi berhasil: {ukuran_baru:.2f} MB")
        return path_hasil_kompres

    except subprocess.CalledProcessError as e:
        print(f"[AUDIO] Kompresi gagal: {e}. Menggunakan file asli.")
        return path_file

def transcribe_audio(path_audio: str) -> str:
    """
    Kirim file audio ke Whisper AI dan dapatkan teks transkripsinya.

    Menggunakan model whisper-large-v3 via Groq, dipaksa menggunakan Bahasa Indonesia.

    Returns:
        Teks hasil transkripsi dalam Bahasa Indonesia.
    """
    print("[AI] Mengirim audio ke Whisper...")

    with open(path_audio, "rb") as f:
        hasil = klien_groq.audio.transcriptions.create(
            file=(path_audio, f.read()),
            model="whisper-large-v3",
            language="id",
            response_format="json",
        )

    teks = hasil.text
    print(f"[AI] Transkripsi selesai: '{teks[:80]}...'")
    return teks

def parse_medical_text(teks_transkripsi: str) -> dict:
    """
    Kirim teks transkripsi ke Llama 3 dan dapatkan data medis dalam format JSON.

    Menggunakan temperature=0.1 agar output konsisten dan tidak terlalu "kreatif".
    Response dipaksa dalam format JSON object yang valid.

    Returns:
        Dictionary berisi data medis terstruktur sesuai format SOAP.
    """
    print("[AI] Menganalisis teks dengan Llama 3...")

    respons = klien_groq.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": PROMPT_SISTEM_MEDIS},
            {"role": "user",   "content": f"Analisa percakapan medis ini dan ekstrak datanya: '{teks_transkripsi}'"},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    data_medis = json.loads(respons.choices[0].message.content)
    print("[AI] Analisis Llama 3 selesai.")
    return data_medis