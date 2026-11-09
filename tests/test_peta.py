"""Tes penyusunan peta Folium. Jalankan: python -m pytest tests/ -v"""

from src import muat_data, peta

SEMUA_LAPISAN = {"tni": True, "pulau": True, "alki": True, "asing": True, "lingkaran": True}


def _data():
    return (
        muat_data.muat_markas_tni(),
        muat_data.muat_pulau_terluar(),
        muat_data.muat_alki(),
        muat_data.muat_pangkalan_asing(),
    )


def test_semua_kategori_di_data_punya_warna():
    # buat_peta memakai WARNA_MATRA[...] / WARNA_PULAU[...] / WARNA_ALKI[...] langsung,
    # jadi kategori baru di CSV tanpa warna akan bikin peta gagal digambar.
    tni, pulau, alki, _ = _data()
    assert set(tni["matra"]) <= set(peta.WARNA_MATRA)
    assert set(pulau["jenis"]) <= set(peta.WARNA_PULAU)
    assert set(pulau["jenis"]) <= set(peta.LABEL_PULAU)
    assert set(alki["alki"]) <= set(peta.WARNA_ALKI)


def test_peta_lengkap_bisa_dirender():
    tni, pulau, alki, asing = _data()
    terpilih = asing.iloc[0]
    m = peta.buat_peta(tni, pulau, alki, asing, SEMUA_LAPISAN, [500, 1000],
                       terpilih=terpilih, tni_terdekat=tni.iloc[0], pulau_terdekat=pulau.iloc[0])
    html = m.get_root().render()
    assert "Markas TNI" in html
    assert "Analisis jarak (pangkalan terpilih)" in html
    assert "radius 1000 km" in html


def test_lapisan_bisa_dimatikan():
    tni, pulau, alki, asing = _data()
    m = peta.buat_peta(tni, pulau, alki, asing, {k: False for k in SEMUA_LAPISAN}, [500])
    html = m.get_root().render()
    assert "Markas TNI" not in html
    assert "Pangkalan asing di kawasan" not in html


def test_legenda_memuat_semua_kategori():
    html = peta.legenda_html()
    for label in list(peta.WARNA_MATRA) + list(peta.WARNA_NEGARA) + list(peta.LABEL_PULAU.values()):
        assert label in html


def test_popup_escape_html_dan_lewati_kosong():
    import numpy as np
    import pandas as pd

    b = pd.Series({"nama": "Andaman & Nicobar", "jenis": "gabungan", "keterangan": "", "status": np.nan,
                   "sumber": "Wikipedia", "url_sumber": "https://contoh.org/a?b=1&c=2"})
    h = peta._popup(b["nama"], b, [("Jenis", "jenis"), ("Status", "status"), ("Catatan", "keterangan")])
    assert "Andaman &amp; Nicobar" in h
    assert "<b>Jenis:</b> gabungan" in h
    assert "Status" not in h and "Catatan" not in h and "nan" not in h
    assert 'href="https://contoh.org/a?b=1&amp;c=2"' in h


def test_popup_tanpa_link_tampilkan_nama_sumber_saja():
    import pandas as pd

    b = pd.Series({"nama": "Pos A", "sumber": "Kemhan", "url_sumber": ""})
    h = peta._popup("Pos A", b, [])
    assert "<a " not in h and "<i>Kemhan</i>" in h
