"""Tes rumus jarak dan validitas data. Jalankan: python -m pytest tests/ -v"""

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
