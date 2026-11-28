"""
muat_data.py - Baca semua CSV di folder data/ jadi DataFrame yang rapi.
Tidak ada Streamlit di sini; caching dilakukan di app.py.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
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
            # Spasi sisa suntingan ("Laut ") membuat filter matra punya dua pilihan untuk satu matra.
            df[kolom] = df[kolom].fillna("").map(lambda v: v.strip() if isinstance(v, str) else v)
    return df


# Ejaan baku matra, dipakai filter dan warna peta. Kunci huruf kecil supaya "al" atau "gabungan" tetap cocok.
MATRA_BAKU = {"ad": "AD", "al": "AL", "au": "AU", "gabungan": "Gabungan"}


def muat_markas_tni() -> pd.DataFrame:
    df = _baca("markas_tni.csv")
    # Matra "al" (huruf kecil) tidak cocok dengan pilihan filter "AL", sehingga markasnya hilang dari peta.
    df["matra"] = df["matra"].map(lambda m: MATRA_BAKU.get(m.lower(), m) if isinstance(m, str) else m)
    _validasi_koordinat(df, "markas_tni.csv")
    return df


def muat_pulau_terluar() -> pd.DataFrame:
    df = _baca("pulau_terluar_perbatasan.csv")
    _validasi_koordinat(df, "pulau_terluar_perbatasan.csv")
    return df


def muat_alki() -> pd.DataFrame:
    df = _baca("alki.csv")
    # Kalau satu sel urutan tidak berupa angka, kolomnya terbaca sebagai teks dan "10" tersortir
    # sebelum "2", sehingga garis ALKI melompat bolak-balik. Koordinat rusak juga jadi NaN.
    for kolom in ("urutan", "lat", "lon"):
        angka = pd.to_numeric(df[kolom], errors="coerce")
        # Titik "inf" lolos dropna di peta dan membuat garis ALKI ditulis sebagai Infinity di JavaScript.
        df[kolom] = angka.where(np.isfinite(angka))
    # Titik tanpa urutan tidak punya tempat di garis; kalau dibiarkan, sort menaruhnya di ujung
    # dan garis ALKI tiba-tiba melompat ke titik itu.
    df = df.dropna(subset=["urutan"])
    return df.sort_values(["alki", "urutan"], kind="mergesort")


def muat_pangkalan_asing() -> pd.DataFrame:
    df = _baca("pangkalan_asing.csv")
    # Koordinat pangkalan asing tidak divalidasi kotak Indonesia, tetapi satu sel salah ketik
    # ("1,35" pakai koma) tetap tidak boleh membuat seluruh kolom jadi teks. Sel itu jadi NaN
    # dan barisnya dilewati di peta dan tabel jarak.
    for kolom in ("lat", "lon"):
        angka = pd.to_numeric(df[kolom], errors="coerce")
        # "inf" lolos to_numeric dan dropna, lalu menggagalkan tabel jarak dan peta; samakan dengan NaN.
        df[kolom] = angka.where(np.isfinite(angka))
    # Lintang di luar ±90 atau bujur di luar ±180 (misalnya lat/lon tertukar) bukan titik nyata;
    # haversine tetap menghitungnya dan tabel jarak menampilkan angka ngawur.
    df["lat"] = df["lat"].where(df["lat"].abs() <= 90)
    df["lon"] = df["lon"].where(df["lon"].abs() <= 180)
    df["negara"] = df["negara_operator"].apply(kelompok_negara)
    return df


def _angka(df: pd.DataFrame, kolom: list[str]) -> pd.DataFrame:
    """Satu sel bukan angka ("n.a.") membuat seluruh kolom terbaca teks dan _baca mengisinya "".
    Grafik lalu menganggapnya kategori; sel itu dijadikan NaN saja."""
    for k in kolom:
        if k in df.columns:
            angka = pd.to_numeric(df[k].replace("", None), errors="coerce")
            # "inf" juga terbaca angka; lolos dropna lalu membuat astype(int) tahun dan skala grafik rusak.
            df[k] = angka.where(np.isfinite(angka))
    return df


def muat_anggaran_indonesia() -> pd.DataFrame:
    df = _angka(_baca("anggaran_indonesia.csv"), ["tahun", "anggaran_rp_triliun", "persen_pdb"])
    # Tahun teks ("2025*") tersortir sebagai teks; baris tanpa tahun angka tidak bisa digambar di linimasa.
    # Tahun pecahan (2024.5) juga dibuang; astype(int) memotongnya jadi 2024 dan tahun itu muncul dua kali.
    df = df[df["tahun"] % 1 == 0]
    df = df.dropna(subset=["tahun"]).astype({"tahun": int})
    # Tahun yang tercatat dua kali (baris tersalin saat menyunting) membuat linimasa naik-turun di
    # tahun yang sama; pakai baris terakhir, yang biasanya revisi terbaru.
    df = df.drop_duplicates("tahun", keep="last")
    return df.sort_values("tahun", kind="mergesort").reset_index(drop=True)


def _tidak_negatif(df: pd.DataFrame, kolom: list[str]) -> pd.DataFrame:
    """Belanja, personel, dan jumlah alutsista tidak mungkin negatif; nilai seperti -5 dianggap salah ketik.
    Grafik belanja memakai skala log, dan batang negatif atau nol hilang tanpa pesan apa pun."""
    for k in kolom:
        if k in df.columns:
            df[k] = df[k].where(~(df[k] < 0))
    return df


def muat_anggaran_kawasan() -> pd.DataFrame:
    kolom = ["belanja_usd_miliar_2024", "persen_pdb_2024", "personel_aktif_ribu"]
    return _tidak_negatif(_angka(_baca("anggaran_kawasan.csv"), kolom), kolom)


def muat_alutsista() -> pd.DataFrame:
    return _tidak_negatif(_angka(_baca("alutsista.csv"), ["jumlah_perkiraan"]), ["jumlah_perkiraan"])


def _validasi_koordinat(df: pd.DataFrame, nama: str) -> None:
    """Semua titik Indonesia harus berada di kotak kasar wilayah Indonesia."""
    # Satu sel salah ketik ("-6,2" pakai koma) membuat seluruh kolom terbaca sebagai teks, dan
    # perbandingan di bawah gagal dengan TypeError yang tidak menyebut titik mana yang rusak.
    lat = pd.to_numeric(df["lat"], errors="coerce")
    lon = pd.to_numeric(df["lon"], errors="coerce")
    kosong = df[lat.isna() | lon.isna()]
    if not kosong.empty:
        # NaN selalu lolos perbandingan < dan >, jadi harus dicek terpisah.
        raise ValueError(f"{nama}: koordinat kosong atau bukan angka -> {kosong['nama'].tolist()}")
    salah = df[(lat < -11.5) | (lat > 6.5) | (lon < 94.5) | (lon > 141.5)]
    if not salah.empty:
        raise ValueError(f"{nama}: koordinat di luar Indonesia -> {salah['nama'].tolist()}")
