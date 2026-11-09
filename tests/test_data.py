"""Tes pemuat data (src/muat_data.py): validasi koordinat dan konsistensi tiap CSV."""

import pandas as pd
import pytest

from src import muat_data


def test_validasi_koordinat_menangkap_titik_di_luar_indonesia():
    df = pd.DataFrame({"nama": ["Natuna", "Darwin"], "lat": [3.9, -12.4], "lon": [108.4, 130.8]})
    with pytest.raises(ValueError, match="Darwin"):
        muat_data._validasi_koordinat(df, "uji.csv")


def test_validasi_koordinat_lolos_untuk_titik_di_dalam():
    df = pd.DataFrame({"nama": ["Merauke", "Sabang"], "lat": [-8.5, 5.9], "lon": [140.4, 95.3]})
    muat_data._validasi_koordinat(df, "uji.csv")     # tidak error


def test_teks_kosong_jadi_string_kosong():
    for df in (muat_data.muat_markas_tni(), muat_data.muat_pangkalan_asing(), muat_data.muat_alutsista()):
        teks = df[[k for k in df.columns if muat_data._kolom_teks(df[k])]]
        assert not teks.isna().any().any()           # aman dipakai di popup peta


def test_id_markas_tni_unik():
    tni = muat_data.muat_markas_tni()
    assert tni["id"].is_unique
    assert not tni["nama"].duplicated().any()


def test_alki_urut_dan_bersambung():
    alki = muat_data.muat_alki()
    assert set(alki["alki"]) >= {"ALKI I", "ALKI II", "ALKI III"}
    for _, jalur in alki.groupby("alki"):
        assert jalur["urutan"].is_monotonic_increasing and jalur["urutan"].is_unique
        assert len(jalur) >= 2                      # minimal satu ruas garis


def test_anggaran_masuk_akal():
    ang = muat_data.muat_anggaran_indonesia()
    assert ang["tahun"].is_monotonic_increasing and ang["tahun"].is_unique
    assert (ang["anggaran_rp_triliun"] > 0).all()
    assert ang["persen_pdb"].between(0, 5).all()


def test_anggaran_kawasan_lengkap():
    kaw = muat_data.muat_anggaran_kawasan()
    assert "Indonesia" in set(kaw["negara"]) and kaw["negara"].is_unique
    assert (kaw["belanja_usd_miliar_2024"] > 0).all()
    assert (kaw["personel_aktif_ribu"] > 0).all()
    assert set(kaw["keyakinan"]) <= {"tinggi", "sedang", "rendah"}
    assert kaw["sumber"].str.strip().ne("").all()


def test_alutsista_matra_dikenal_dan_bersumber():
    from src.peta import WARNA_MATRA

    alut = muat_data.muat_alutsista()
    assert set(alut["matra"]) <= set(WARNA_MATRA)
    assert alut["alutsista"].str.strip().ne("").all()
    assert alut["sumber"].str.strip().ne("").all()


def test_pangkalan_asing_dikelompokkan_per_negara():
    asing = muat_data.muat_pangkalan_asing()
    assert asing["negara"].str.strip().ne("").all()
    assert asing["url_sumber"].str.startswith("http").all()
