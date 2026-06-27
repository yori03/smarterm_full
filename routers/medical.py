import os
import shutil
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

import models
from ai_services import (
    compress_audio,
    parse_medical_text,
    transcribe_audio,
)
from database import get_db
from dependencies import get_current_user
from schemas import SimpanRMSchema


router = APIRouter()

TEMP_FOLDER = "temp_files"
os.makedirs(TEMP_FOLDER, exist_ok=True)


@router.post("/transcribe")
async def transcribe_dan_analisis(
    file: UploadFile = File(...),
    pengguna: models.User = Depends(get_current_user),
):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    temp_path = (
        f"{TEMP_FOLDER}/"
        f"{timestamp}_{file.filename}"
    )

    compressed_path = temp_path

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        compressed_path = compress_audio(temp_path)

        transkrip = transcribe_audio(compressed_path)

        data_medis = parse_medical_text(
            transkrip
        )

        return {
            "status": "success",
            "dokter": pengguna.nama_lengkap,
            "transkrip_asli": transkrip,
            "data_medis": data_medis,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gagal memproses AI: {e}",
        )

    finally:
        _hapus_file_temp(
            temp_path,
            compressed_path,
        )


@router.post("/simpan-rm")
def simpan_rekam_medis(
    data: SimpanRMSchema,
    db: Session = Depends(get_db),
    pengguna: models.User = Depends(get_current_user),
):
    pasien = (
        db.query(models.Pasien)
        .filter(
            models.Pasien.no_rekam_medis
            == data.no_rekam_medis
        )
        .first()
    )

    if not pasien:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Pasien dengan No RM "
                f"'{data.no_rekam_medis}' "
                f"tidak ditemukan."
            ),
        )

    rekam_medis = models.RekamMedis(
        id_pasien=pasien.id_pasien,
        id_dokter=pengguna.id_user,
        status_record="final",

        tekanan_darah=data.tekanan_darah,
        nadi=data.nadi,
        suhu=data.suhu,

        keluhan_utama=data.keluhan_utama,
        riwayat_penyakit_sekarang=data.riwayat_penyakit_sekarang,
        riwayat_penyakit_keluarga=data.riwayat_penyakit_keluarga,

        hpht=_parse_tanggal(data.hpht),
        hpl=_parse_tanggal(data.hpl),

        pemeriksaan_fisik_lengkap=data.pemeriksaan_fisik_lengkap,

        diagnosa_utama=data.diagnosa_utama,

        rencana_layanan=data.rencana_layanan,
        resep_obat=data.resep_obat,
        edukasi_pasien=data.edukasi_pasien,
    )

    db.add(rekam_medis)
    db.commit()
    db.refresh(rekam_medis)

    return {
        "msg": "Rekam medis berhasil disimpan.",
        "id_record": rekam_medis.id_record,
        "pasien": pasien.nama_pasien,
        "dokter": pengguna.nama_lengkap,
        "waktu": str(
            rekam_medis.waktu_pemeriksaan
        ),
    }


@router.get("/rekam-medis/{id_record}")
def get_rekam_medis(
    id_record: int,
    db: Session = Depends(get_db),
    pengguna: models.User = Depends(get_current_user),
):
    rekam_medis = (
        db.query(models.RekamMedis)
        .filter(
            models.RekamMedis.id_record
            == id_record
        )
        .first()
    )

    if not rekam_medis:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Rekam medis dengan "
                f"ID {id_record} tidak ditemukan."
            ),
        )

    pasien = rekam_medis.pasien
    dokter = rekam_medis.dokter

    return {
        "id_record": rekam_medis.id_record,
        "pasien": pasien.nama_pasien if pasien else None,
        "no_rekam_medis": (
            pasien.no_rekam_medis
            if pasien else None
        ),
        "dokter": (
            dokter.nama_lengkap
            if dokter else None
        ),
        "tanggal_lahir": (
            str(pasien.tanggal_lahir)
            if pasien and pasien.tanggal_lahir
            else None
        ),
        "alamat": (
            pasien.alamat
            if pasien else None
        ),
        "waktu_pemeriksaan": str(
            rekam_medis.waktu_pemeriksaan
        ),
        "status": rekam_medis.status_record,
        "data_medis": {
            "tekanan_darah": rekam_medis.tekanan_darah,
            "nadi": rekam_medis.nadi,
            "suhu": rekam_medis.suhu,
            "keluhan_utama": rekam_medis.keluhan_utama,
            "riwayat_penyakit_sekarang":
                rekam_medis.riwayat_penyakit_sekarang,
            "riwayat_penyakit_keluarga":
                rekam_medis.riwayat_penyakit_keluarga,
            "hpht":
                str(rekam_medis.hpht)
                if rekam_medis.hpht
                else None,
            "hpl":
                str(rekam_medis.hpl)
                if rekam_medis.hpl
                else None,
            "pemeriksaan_fisik_lengkap":
                rekam_medis.pemeriksaan_fisik_lengkap,
            "diagnosa_utama":
                rekam_medis.diagnosa_utama,
            "rencana_layanan":
                rekam_medis.rencana_layanan,
            "resep_obat":
                rekam_medis.resep_obat,
            "edukasi_pasien":
                rekam_medis.edukasi_pasien,
        },
    }


def _parse_tanggal(
    teks_tanggal: Optional[str],
) -> Optional[date]:

    if not teks_tanggal:
        return None

    try:
        return datetime.strptime(
            teks_tanggal,
            "%Y-%m-%d",
        ).date()

    except ValueError:
        return None


def _hapus_file_temp(
    path_asli: str,
    path_kompres: str,
) -> None:

    if os.path.exists(path_asli):
        os.remove(path_asli)

    if (
        path_kompres != path_asli
        and os.path.exists(path_kompres)
    ):
        os.remove(path_kompres)