"""
muat_data.py - Baca semua CSV di folder data/ jadi DataFrame yang rapi.
Tidak ada Streamlit di sini; caching dilakukan di app.py.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.geo import kelompok_negara

FOLDER_DATA = Path(__file__).resolve().parent.parent / "data"


def _kolom_teks(kolom: pd.Series) -> bool:
    """True untuk kolom teks. Di pandas 3 teks dibaca sebagai dtype `str`, bukan `object` lagi."""
    return kolom.dtype == object or isinstance(kolom.dtype, pd.StringDtype)


def _baca(nama_file: str) -> pd.DataFrame:
    df = pd.read_csv(FOLDER_DATA / nama_file)
    # kolom teks kosong -> string kosong (bukan NaN) supaya aman dipakai di popup
    for kolom in df.columns:
        if _kolom_teks(df[kolom]):
            df[kolom] = df[kolom].fillna("")
    return df


def muat_markas_tni() -> pd.DataFrame:
    df = _baca("markas_tni.csv")
    _validasi_koordinat(df, "markas_tni.csv")
    return df


def muat_pulau_terluar() -> pd.DataFrame:
    df = _baca("pulau_terluar_perbatasan.csv")
    _validasi_koordinat(df, "pulau_terluar_perbatasan.csv")
    return df


def muat_alki() -> pd.DataFrame:
    return _baca("alki.csv").sort_values(["alki", "urutan"])


def muat_pangkalan_asing() -> pd.DataFrame:
    df = _baca("pangkalan_asing.csv")
    df["negara"] = df["negara_operator"].apply(kelompok_negara)
    return df


def muat_anggaran_indonesia() -> pd.DataFrame:
    return _baca("anggaran_indonesia.csv").sort_values("tahun")


def muat_anggaran_kawasan() -> pd.DataFrame:
    return _baca("anggaran_kawasan.csv")


def muat_alutsista() -> pd.DataFrame:
    return _baca("alutsista.csv")


def _validasi_koordinat(df: pd.DataFrame, nama: str) -> None:
    """Semua titik Indonesia harus berada di kotak kasar wilayah Indonesia."""
    salah = df[(df["lat"] < -11.5) | (df["lat"] > 6.5) | (df["lon"] < 94.5) | (df["lon"] > 141.5)]
    if not salah.empty:
        raise ValueError(f"{nama}: koordinat di luar Indonesia -> {salah['nama'].tolist()}")
