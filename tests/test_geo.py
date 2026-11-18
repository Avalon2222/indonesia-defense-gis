"""Tes rumus jarak dan validitas data. Jalankan: python -m pytest tests/ -v"""

import math

import numpy as np
import pandas as pd
import pytest

from src import geo, muat_data


def test_haversine_titik_sama_nol():
    assert geo.haversine_km(-6.2, 106.8, -6.2, 106.8) == 0


def test_haversine_jakarta_singapura():
    # Jakarta - Singapura dikenal sekitar 880-900 km garis lurus
    assert geo.haversine_km(-6.21, 106.85, 1.35, 103.82) == pytest.approx(900, abs=15)


def test_haversine_simetris():
    a = geo.haversine_km(3.95, 108.38, 9.55, 112.89)
    b = geo.haversine_km(9.55, 112.89, 3.95, 108.38)
    assert a == pytest.approx(b)


def test_haversine_satu_derajat_lintang_111km():
    assert geo.haversine_km(0, 100, 1, 100) == pytest.approx(111.2, abs=0.5)


def test_arah_kompas():
    assert geo.arah_kompas(0, 100, 5, 100) == "U"
    assert geo.arah_kompas(0, 100, 0, 105) == "T"
    assert geo.arah_kompas(0, 100, -5, 100) == "S"
    assert geo.arah_kompas(0, 100, 0, 95) == "B"


def test_titik_terdekat_dan_radius():
    df_tni = muat_data.muat_markas_tni()
    # Fiery Cross Reef -> markas TNI terdekat harus di Natuna (Ranai)
    baris, jarak = geo.titik_terdekat(9.55, 112.89, df_tni)
    assert "Ranai" in baris["nama"] or "Raden Sadjad" in baris["nama"]
    assert 700 < jarak < 850
    assert geo.jumlah_dalam_radius(9.55, 112.89, df_tni, 500) == 0
    assert geo.jumlah_dalam_radius(9.55, 112.89, df_tni, 1000) >= 2


def test_titik_terdekat_df_kosong():
    import pandas as pd
    with pytest.raises(ValueError):
        geo.titik_terdekat(0, 0, pd.DataFrame(columns=["lat", "lon"]))


def test_dataset_bisa_dimuat_dan_valid():
    tni = muat_data.muat_markas_tni()
    pulau = muat_data.muat_pulau_terluar()
    asing = muat_data.muat_pangkalan_asing()
    assert len(tni) >= 60 and set(tni["matra"]) == {"AD", "AL", "AU", "Gabungan"}
    assert len(pulau) >= 20
    assert len(asing) >= 30 and asing["negara"].notna().all()
    assert (asing["url_sumber"].str.startswith("http")).all()


def test_tabel_jarak_bentuk():
    tabel = geo.tabel_jarak(muat_data.muat_pangkalan_asing(), muat_data.muat_markas_tni(), muat_data.muat_pulau_terluar())
    assert len(tabel) == len(muat_data.muat_pangkalan_asing())
    assert tabel["jarak_pulau_km"].is_monotonic_increasing
    # INS Baaz (Nicobar) harus jadi salah satu yang paling dekat ke pulau terluar (Pulau Rondo)
    assert "INS Baaz" in tabel.head(8)["nama"].str.cat(sep=" ")


def test_kelompok_negara():
    assert geo.kelompok_negara("Australia (+ AS rotasi)") == "Australia"
    assert geo.kelompok_negara("Kamboja (dibangun China)") == "Lainnya"


def test_semua_csv_terbaca():
    for fungsi in (muat_data.muat_alki, muat_data.muat_anggaran_indonesia, muat_data.muat_anggaran_kawasan, muat_data.muat_alutsista):
        assert not fungsi().empty


def test_jarak_ke_semua_sama_dengan_haversine_satu_satu():
    df = muat_data.muat_markas_tni()
    vektor = geo.jarak_ke_semua(-6.21, 106.85, df)
    satu_satu = [geo.haversine_km(-6.21, 106.85, la, lo) for la, lo in zip(df["lat"], df["lon"])]
    assert vektor.index.equals(df.index)
    assert vektor.tolist() == pytest.approx(satu_satu)


def test_jarak_ke_semua_df_kosong():
    import pandas as pd
    hasil = geo.jarak_ke_semua(0, 0, pd.DataFrame(columns=["lat", "lon"]))
    assert hasil.empty and hasil.dtype == float


def test_arah_kompas_diagonal():
    assert geo.arah_kompas(0, 100, 5, 105) == "TL"
    assert geo.arah_kompas(0, 100, -5, 95) == "BD"


def test_tabel_jarak_tanpa_pangkalan_asing():
    asing = muat_data.muat_pangkalan_asing().iloc[0:0]
    tabel = geo.tabel_jarak(asing, muat_data.muat_markas_tni(), muat_data.muat_pulau_terluar())
    assert tabel.empty
    assert {"nama", "tni_terdekat", "jarak_pulau_km", "jumlah_tni_1000km"} <= set(tabel.columns)


def test_titik_terdekat_lewati_koordinat_kosong():
    df = pd.DataFrame({"nama": ["tanpa koordinat", "Batam"], "lat": [np.nan, 1.1], "lon": [np.nan, 104.0]})
    baris, jarak = geo.titik_terdekat(1.1, 104.0, df)
    assert baris["nama"] == "Batam" and jarak == pytest.approx(0)
    with pytest.raises(ValueError, match="koordinat lengkap"):
        geo.titik_terdekat(1.1, 104.0, df.iloc[[0]])


@pytest.mark.parametrize("teks, label", [
    ("Amerika Serikat (Marinir rotasi)", "Amerika Serikat"),
    ("china", "China"),
    ("Singapura", "Singapura"),
    ("Malaysia", "Malaysia"),
    ("Filipina (+ AS EDCA)", "Filipina"),
    ("Vietnam", "Vietnam"),
    ("India (Komando Andaman)", "India"),
    ("Inggris", "Lainnya"),
])
def test_kelompok_negara_semua_cabang(teks, label):
    assert geo.kelompok_negara(teks) == label


def test_kelompok_negara_data_asli_tidak_banyak_lainnya():
    asing = muat_data.muat_pangkalan_asing()
    label = asing["negara_operator"].map(geo.kelompok_negara)
    # Sebagian besar pangkalan harus masuk kelompok negara yang punya warna sendiri di peta.
    assert (label == "Lainnya").mean() < 0.25


@pytest.mark.parametrize("teks, label", [
    ("  Australia", "Australia"),
    ("AS (Diego Garcia)", "Amerika Serikat"),
    ("AS", "Amerika Serikat"),
    ("Asia Tenggara", "Lainnya"),
    (float("nan"), "Lainnya"),
    (None, "Lainnya"),
])
def test_kelompok_negara_spasi_singkatan_dan_kosong(teks, label):
    assert geo.kelompok_negara(teks) == label


def test_haversine_titik_antipoda_tidak_error():
    # Contoh nyata yang dulu memicu "math domain error" karena a sedikit di atas 1.
    lat, lon = -18.718240534908475, -38.31958713665131
    setengah_keliling = np.pi * geo.RADIUS_BUMI_KM
    assert geo.haversine_km(lat, lon, -lat, lon + 180) == pytest.approx(setengah_keliling)
    df = pd.DataFrame({"lat": [-lat], "lon": [lon + 180]})
    assert geo.jarak_ke_semua(lat, lon, df).iloc[0] == pytest.approx(setengah_keliling)


def test_tabel_jarak_lewati_pangkalan_tanpa_koordinat():
    asing = muat_data.muat_pangkalan_asing().head(3).copy()
    asing.loc[asing.index[0], ["lat", "lon"]] = np.nan
    tabel = geo.tabel_jarak(asing, muat_data.muat_markas_tni(), muat_data.muat_pulau_terluar())
    assert len(tabel) == 2
    assert asing["nama"].iloc[0] not in set(tabel["nama"])


def test_arah_kompas_koordinat_kosong():
    assert geo.arah_kompas(float("nan"), 100, 5, 100) == ""
    assert geo.arah_kompas(0, 100, None, 100) == ""


def test_arah_kompas_titik_sama_tanpa_arah():
    assert geo.arah_kompas(-6.2, 106.8, -6.2, 106.8) == "-"


def test_kelompok_negara_singkatan_as_dan_tiongkok():
    assert geo.kelompok_negara("AS/Inggris (AUKUS)") == "Amerika Serikat"
    assert geo.kelompok_negara("AS (rotasi)") == "Amerika Serikat"
    assert geo.kelompok_negara("AS") == "Amerika Serikat"
    assert geo.kelompok_negara("ASEAN") == "Lainnya"
    assert geo.kelompok_negara("Tiongkok") == "China"
    assert geo.kelompok_negara("RRT (PLAN)") == "China"


def test_arah_kompas_koordinat_pd_na():
    assert geo.arah_kompas(pd.NA, 100, 5, 100) == ""
    assert geo.arah_kompas(0, 100, 5, pd.NA) == ""
    assert geo.arah_kompas(np.float64(0), 100, np.float64(5), 100) == "U"


@pytest.mark.parametrize("kosong", [None, pd.NA, float("nan")])
def test_haversine_koordinat_kosong_jadi_nan(kosong):
    assert math.isnan(geo.haversine_km(kosong, 106.85, 1.35, 103.82))
    assert math.isnan(geo.haversine_km(-6.21, 106.85, 1.35, kosong))


def test_titik_terdekat_koordinat_asal_kosong_pesannya_jelas():
    df = pd.DataFrame({"nama": ["A"], "lat": [1.0], "lon": [104.0]})
    with pytest.raises(ValueError, match="Koordinat asal"):
        geo.titik_terdekat(float("nan"), 106.85, df)
