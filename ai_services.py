import json
import os
import subprocess

from groq import Groq

from config import GROQ_API_KEY


client = Groq(api_key=GROQ_API_KEY)

MAX_AUDIO_MB = 24

PROMPT_SISTEM_MEDIS = """
Anda adalah Asisten Medis Spesialis Obgyn (Kandungan) RSIA Al Hasanah.

Output HARUS berupa JSON dengan field:
keluhan_utama,
riwayat_penyakit_sekarang,
riwayat_penyakit_keluarga,
hpht,
hpl,
tekanan_darah,
nadi,
suhu,
pemeriksaan_fisik_lengkap,
diagnosa_utama,
rencana_layanan,
resep_obat,
edukasi_pasien

Aturan:
1. Output hanya JSON.
2. Data yang tidak ditemukan isi null.
3. Perbaiki ejaan obat bila perlu.
4. Gunakan interpretasi medis sesuai konteks.'
5. Istilah penting terkait tanggal kehamilan baik terakhir haid mupun kelahiran dicatat di bagian hpht dan hpl
"""


def compress_audio(path_file: str) -> str:

    ukuran_mb = os.path.getsize(path_file) / (1024 * 1024)

    if ukuran_mb <= MAX_AUDIO_MB:
        return path_file

    nama, ext = os.path.splitext(path_file)
    output_file = f"{nama}_compressed{ext}"

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                path_file,
                "-ac",
                "1",
                "-ar",
                "16000",
                "-b:a",
                "32k",
                output_file,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        return output_file

    except subprocess.CalledProcessError:
        return path_file


def transcribe_audio(path_audio: str) -> str:

    with open(path_audio, "rb") as audio_file:

        response = client.audio.transcriptions.create(
            file=(path_audio, audio_file.read()),
            model="whisper-large-v3",
            language="id",
            response_format="json",
        )

    return response.text


def parse_medical_text(teks_transkripsi: str) -> dict:

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": PROMPT_SISTEM_MEDIS,
            },
            {
                "role": "user",
                "content": (
                    "Analisa percakapan medis berikut "
                    "dan ekstrak datanya ke JSON:\n\n"
                    f"{teks_transkripsi}"
                ),
            },
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    return json.loads(
        response.choices[0].message.content
    )