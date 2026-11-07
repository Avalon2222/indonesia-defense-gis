"""
geo.py - Rumus jarak & analisis spasial sederhana
==================================================
Semua fungsi di sini murni Python + pandas: tidak ada Streamlit, tidak ada peta.
Tujuannya agar mudah diuji (lihat tests/test_geo.py) dan dapat dipakai ulang
di proyek lain.

Istilah:
- Haversine : rumus jarak dua titik di permukaan bola (bumi dianggap bola).
- Great-circle distance : jarak terpendek di permukaan bumi ("jarak terbang lurus").
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

RADIUS_BUMI_KM = 6371.0  # jari-jari rata-rata bumi (km)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Jarak great-circle (km) antara dua koordinat derajat desimal.

    Contoh: Jakarta (-6.21, 106.85) ke Singapura (1.35, 103.82) ≈ 900 km.

    >>> round(haversine_km(-6.21, 106.85, 1.35, 103.82))
    900
    """
    # 1. derajat -> radian, karena fungsi trigonometri Python pakai radian
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    # 2. rumus haversine
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # 3. sudut pusat (radian) x jari-jari = panjang busur
    return RADIUS_BUMI_KM * c


def arah_kompas(lat1: float, lon1: float, lat2: float, lon2: float) -> str:
    """Arah dari titik 1 ke titik 2 dalam 8 mata angin (U, TL, T, TG, S, BD, B, BL).

    >>> arah_kompas(0, 100, 5, 100)   # ke utara
    'U'
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_lambda = math.radians(lon2 - lon1)
    x = math.sin(d_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(d_lambda)
    bearing = (math.degrees(math.atan2(x, y)) + 360) % 360
    arah = ["U", "TL", "T", "TG", "S", "BD", "B", "BL"]
    return arah[int((bearing + 22.5) // 45) % 8]


def jarak_ke_semua(lat: float, lon: float, df: pd.DataFrame) -> pd.Series:
    """Jarak (km) dari satu titik ke SETIAP baris df (df harus punya kolom lat & lon).

    Mengembalikan Series dengan index sama seperti df, jadi bisa langsung
    dijadikan kolom baru: df["jarak_km"] = jarak_ke_semua(...).
    """
    # Versi vektor (numpy) dari haversine_km: semua baris dihitung sekaligus,
    # jauh lebih cepat daripada df.apply baris per baris.
    lat2 = np.radians(df["lat"].to_numpy(dtype=float))
    lon2 = np.radians(df["lon"].to_numpy(dtype=float))
    phi1 = math.radians(lat)
    a = np.sin((lat2 - phi1) / 2) ** 2 + math.cos(phi1) * np.cos(lat2) * np.sin((lon2 - math.radians(lon)) / 2) ** 2
    jarak = 2 * RADIUS_BUMI_KM * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return pd.Series(jarak, index=df.index, dtype=float)


def titik_terdekat(lat: float, lon: float, df: pd.DataFrame) -> tuple[pd.Series, float]:
    """Baris df yang paling dekat ke (lat, lon), beserta jaraknya (km)."""
    if df.empty:
        raise ValueError("DataFrame kosong, tidak ada titik untuk dibandingkan")
    jarak = jarak_ke_semua(lat, lon, df)
    idx = jarak.idxmin()
    return df.loc[idx], float(jarak.loc[idx])


def jumlah_dalam_radius(lat: float, lon: float, df: pd.DataFrame, radius_km: float) -> int:
    """Berapa baris df yang berada dalam jarak <= radius_km dari (lat, lon)."""
    return int((jarak_ke_semua(lat, lon, df) <= radius_km).sum())


def tabel_jarak(df_asing: pd.DataFrame, df_tni: pd.DataFrame, df_pulau: pd.DataFrame) -> pd.DataFrame:
    """Untuk tiap pangkalan asing: markas TNI terdekat + pulau terluar terdekat.

    Hasil: satu baris per pangkalan asing dengan kolom
    nama, negara_operator, tni_terdekat, jarak_tni_km, arah_ke_tni,
    pulau_terdekat, jarak_pulau_km, jumlah_tni_500km, jumlah_tni_1000km.
    Diurutkan dari yang paling dekat ke pulau terluar.
    """
    hasil = []
    for _, p in df_asing.iterrows():
        tni, jarak_tni = titik_terdekat(p["lat"], p["lon"], df_tni)
        pulau, jarak_pulau = titik_terdekat(p["lat"], p["lon"], df_pulau)
        hasil.append(
            {
                "nama": p["nama"],
                "negara_operator": p["negara_operator"],
                "jenis": p["jenis"],
                "tni_terdekat": tni["nama"],
                "jarak_tni_km": round(jarak_tni),
                "arah_ke_tni": arah_kompas(p["lat"], p["lon"], tni["lat"], tni["lon"]),
                "pulau_terdekat": pulau["nama"],
                "jarak_pulau_km": round(jarak_pulau),
                "jumlah_tni_500km": jumlah_dalam_radius(p["lat"], p["lon"], df_tni, 500),
                "jumlah_tni_1000km": jumlah_dalam_radius(p["lat"], p["lon"], df_tni, 1000),
            }
        )
    return pd.DataFrame(hasil).sort_values("jarak_pulau_km").reset_index(drop=True)


def kelompok_negara(negara_operator: str) -> str:
    """Sederhanakan teks operator ("Australia (+ AS rotasi)") jadi satu label negara utama."""
    teks = negara_operator.lower()
    if teks.startswith("amerika"):
        return "Amerika Serikat"
    if teks.startswith("australia"):
        return "Australia"
    if teks.startswith("china"):
        return "China"
    if teks.startswith("singapura"):
        return "Singapura"
    if teks.startswith("malaysia"):
        return "Malaysia"
    if teks.startswith("filipina"):
        return "Filipina"
    if teks.startswith("vietnam"):
        return "Vietnam"
    if teks.startswith("india"):
        return "India"
    return "Lainnya"
