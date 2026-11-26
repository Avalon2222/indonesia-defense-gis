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


def test_baca_isi_kolom_teks_kosong(tmp_path, monkeypatch):
    (tmp_path / "uji.csv").write_text("nama,catatan,lat,lon\nNatuna,,3.9,108.4\nSabang,pelabuhan,5.9,95.3\n")
    monkeypatch.setattr(muat_data, "FOLDER_DATA", tmp_path)
    df = muat_data._baca("uji.csv")
    assert df["catatan"].tolist() == ["", "pelabuhan"]
    assert df["lat"].dtype == float  # kolom angka tidak disentuh


def test_kolom_teks_kenali_object_dan_string():
    import numpy as np

    assert muat_data._kolom_teks(pd.Series(["a", None], dtype=object))
    assert muat_data._kolom_teks(pd.Series(["a", None], dtype="string"))
    assert not muat_data._kolom_teks(pd.Series([1.0, np.nan]))


def test_pulau_terluar_unik_dan_di_indonesia():
    pulau = muat_data.muat_pulau_terluar()
    assert not pulau["nama"].duplicated().any()
    assert pulau["lat"].between(-11.5, 6.5).all() and pulau["lon"].between(94.5, 141.5).all()


def test_pangkalan_asing_koordinat_valid_dan_unik():
    asing = muat_data.muat_pangkalan_asing()
    assert asing["lat"].between(-90, 90).all() and asing["lon"].between(-180, 180).all()
    assert not asing["nama"].duplicated().any()
    # Pangkalan asing tidak boleh jatuh di daratan utama Jawa (cek kasar salah ketik tanda lat/lon).
    jawa = asing["lat"].between(-8.8, -5.8) & asing["lon"].between(105.0, 114.6)
    assert not jawa.any()


def test_validasi_koordinat_menangkap_titik_tanpa_koordinat():
    df = pd.DataFrame({"nama": ["Merauke", "Pos Baru"], "lat": [-8.5, None], "lon": [140.4, 120.0]})
    with pytest.raises(ValueError, match="Pos Baru"):
        muat_data._validasi_koordinat(df, "uji.csv")


def test_validasi_koordinat_teks_salah_ketik_sebut_namanya():
    # Koma desimal membuat kolom lat terbaca sebagai teks; pesan error harus menyebut titiknya.
    df = pd.DataFrame({"nama": ["Merauke", "Pos Koma"], "lat": ["-8.5", "-6,2"], "lon": [140.4, 106.8]})
    with pytest.raises(ValueError, match="Pos Koma"):
        muat_data._validasi_koordinat(df, "uji.csv")


def test_pangkalan_asing_koordinat_salah_ketik_jadi_nan(tmp_path, monkeypatch):
    from src import geo

    (tmp_path / "pangkalan_asing.csv").write_text(
        "id,nama,negara_operator,jenis,lat,lon\n"
        "1,Darwin,Australia,udara,-12.41,130.88\n"
        "2,Changi,Singapura,laut,\"1,35\",103.99\n"
    )
    monkeypatch.setattr(muat_data, "FOLDER_DATA", tmp_path)
    df = muat_data.muat_pangkalan_asing()
    assert pd.api.types.is_float_dtype(df["lat"])
    assert pd.isna(df.loc[1, "lat"])
    tni = pd.DataFrame({"nama": ["Lanud"], "lat": [-6.2], "lon": [106.8]})
    tabel = geo.tabel_jarak(df, tni, tni)
    assert tabel["nama"].tolist() == ["Darwin"]


def test_alki_urutan_teks_tetap_diurutkan_sebagai_angka(tmp_path, monkeypatch):
    (tmp_path / "alki.csv").write_text(
        "alki,urutan,lat,lon\nALKI I,10,1.0,104.0\nALKI I,2,-1.0,106.0\nALKI I,?,-2.0,106.5\nALKI I,1,2.0,104.0\n"
    )
    monkeypatch.setattr(muat_data, "FOLDER_DATA", tmp_path)
    df = muat_data.muat_alki()
    assert df["urutan"].tolist()[:3] == [1, 2, 10]


def test_pangkalan_asing_koordinat_tak_hingga_jadi_kosong(tmp_path, monkeypatch):
    (tmp_path / "pangkalan_asing.csv").write_text(
        "nama,negara_operator,jenis,lat,lon\nA,China,laut,inf,110\nB,China,laut,10,-inf\nC,China,laut,10,110\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(muat_data, "FOLDER_DATA", tmp_path)
    df = muat_data.muat_pangkalan_asing()
    assert df[["lat", "lon"]].isna().any(axis=1).tolist() == [True, True, False]


def test_anggaran_sel_bukan_angka_tidak_merusak_kolom(tmp_path, monkeypatch):
    (tmp_path / "anggaran_indonesia.csv").write_text(
        "tahun,anggaran_rp_triliun,persen_pdb,keyakinan,catatan,sumber\n"
        "2024,139.3,0.6,sedang,,x\n"
        "10000,1,0.1,rendah,,x\n"
        "2025,belum ada,,rendah,,x\n"
        "perkiraan,1,0.1,rendah,,x\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(muat_data, "FOLDER_DATA", tmp_path)
    ang = muat_data.muat_anggaran_indonesia()
    assert ang["tahun"].tolist() == [2024, 2025, 10000]
    assert pd.api.types.is_numeric_dtype(ang["anggaran_rp_triliun"])
    assert pd.isna(ang.loc[ang["tahun"] == 2025, "anggaran_rp_triliun"]).all()


def test_kawasan_dan_alutsista_sel_bukan_angka_jadi_nan(tmp_path, monkeypatch):
    (tmp_path / "anggaran_kawasan.csv").write_text(
        "negara,belanja_usd_miliar_2024,persen_pdb_2024,personel_aktif_ribu,keyakinan,sumber\n"
        "Indonesia,10.6,0.8,400,sedang,x\n"
        "Timor Leste,n.a.,,2,rendah,x\n",
        encoding="utf-8",
    )
    (tmp_path / "alutsista.csv").write_text(
        "matra,alutsista,jumlah_perkiraan,status,sumber\n"
        "AD,Tank,103,aktif,x\n"
        "AL,Kapal,rahasia,aktif,x\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(muat_data, "FOLDER_DATA", tmp_path)
    kaw = muat_data.muat_anggaran_kawasan()
    assert kaw["belanja_usd_miliar_2024"].sum() == pytest.approx(10.6)
    assert kaw["persen_pdb_2024"].isna().tolist() == [False, True]
    alut = muat_data.muat_alutsista()
    assert alut["jumlah_perkiraan"].sum() == 103


def test_anggaran_tahun_tak_hingga_dibuang(tmp_path, monkeypatch):
    (tmp_path / "anggaran_indonesia.csv").write_text(
        "tahun,anggaran_rp_triliun,persen_pdb\n2023,135,0.65\ninf,140,0.7\n2024,inf,0.68\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(muat_data, "FOLDER_DATA", tmp_path)
    df = muat_data.muat_anggaran_indonesia()
    assert df["tahun"].tolist() == [2023, 2024]
    assert pd.isna(df["anggaran_rp_triliun"].iloc[1])


def test_alki_koordinat_tak_hingga_jadi_kosong(tmp_path, monkeypatch):
    (tmp_path / "alki.csv").write_text(
        "alki,urutan,lat,lon\nALKI I,1,2.0,104.0\nALKI I,2,inf,106.0\nALKI I,3,-2.0,-inf\n", encoding="utf-8"
    )
    monkeypatch.setattr(muat_data, "FOLDER_DATA", tmp_path)
    df = muat_data.muat_alki()
    assert df[["lat", "lon"]].isna().any(axis=1).tolist() == [False, True, True]


def test_pangkalan_asing_koordinat_di_luar_jangkauan_jadi_kosong(tmp_path, monkeypatch):
    (tmp_path / "pangkalan_asing.csv").write_text(
        "nama,negara_operator,jenis,lat,lon\nA,China,laut,110.5,10\nB,China,laut,10,190\nC,China,laut,-12.4,130.9\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(muat_data, "FOLDER_DATA", tmp_path)
    df = muat_data.muat_pangkalan_asing()
    assert df[["lat", "lon"]].isna().any(axis=1).tolist() == [True, True, False]


def test_anggaran_tahun_pecahan_dibuang(tmp_path, monkeypatch):
    (tmp_path / "anggaran_indonesia.csv").write_text(
        "tahun,anggaran_rp_triliun,persen_pdb\n2023,135,0.65\n2024.5,140,0.7\n2024.0,139,0.68\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(muat_data, "FOLDER_DATA", tmp_path)
    df = muat_data.muat_anggaran_indonesia()
    assert df["tahun"].tolist() == [2023, 2024]
    assert df["anggaran_rp_triliun"].tolist() == [135, 139]


def test_baca_buang_spasi_di_kolom_teks(tmp_path, monkeypatch):
    (tmp_path / "uji.csv").write_text("nama,matra,lat,lon\nA,Laut ,3.9,108.4\nB, Laut,5.9,95.3\nC,Udara,1.0,104.0\n")
    monkeypatch.setattr(muat_data, "FOLDER_DATA", tmp_path)
    df = muat_data._baca("uji.csv")
    assert sorted(df["matra"].unique()) == ["Laut", "Udara"]
