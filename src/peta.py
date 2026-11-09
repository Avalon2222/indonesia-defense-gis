"""
peta.py - Membangun objek peta Folium dari DataFrame.
Folium = pembungkus Python untuk Leaflet.js (library peta web paling populer).
Fungsi di sini mengembalikan folium.Map; app.py tinggal menampilkannya.
"""

from __future__ import annotations

import html

import folium
import pandas as pd

# Satu warna per kategori, urutannya tetap supaya konsisten di peta & grafik.
WARNA_MATRA = {"AD": "#2e7d32", "AL": "#1565c0", "AU": "#6a1b9a", "Gabungan": "#424242"}
WARNA_NEGARA = {
    "Amerika Serikat": "#b23a3a",
    "Australia": "#e08a1e",
    "China": "#c62828",
    "Singapura": "#8e24aa",
    "Malaysia": "#f9a825",
    "Filipina": "#00838f",
    "Vietnam": "#5d4037",
    "India": "#ef6c00",
    "Lainnya": "#757575",
}
WARNA_PULAU = {"pulau_terluar": "#00897b", "pos_perbatasan_darat": "#795548", "wilayah_rawan": "#d81b60"}
LABEL_PULAU = {
    "pulau_terluar": "Pulau terluar",
    "pos_perbatasan_darat": "Pos perbatasan darat",
    "wilayah_rawan": "Wilayah rawan",
}
WARNA_ALKI = {"ALKI I": "#0288d1", "ALKI II": "#0097a7", "ALKI III": "#00796b"}


def _popup(judul: str, baris: pd.Series, kolom: list[tuple[str, str]]) -> str:
    """HTML kecil untuk popup: judul tebal + daftar label: nilai + link sumber."""
    isi = "".join(f"<b>{label}:</b> {_aman(baris[k])}<br>" for label, k in kolom if _aman(baris.get(k, "")))
    link = _aman(baris.get("url_sumber", ""))
    nama_sumber = _aman(baris.get("sumber", ""))
    sumber = f'<a href="{link}" target="_blank">{nama_sumber or "sumber"}</a>' if link else nama_sumber
    return f"<div style='font-family:sans-serif;font-size:12px;min-width:200px'><b style='font-size:13px'>{_aman(judul)}</b><br>{isi}<i>{sumber}</i></div>"


def _aman(nilai) -> str:
    """Teks siap tempel ke HTML: NaN/None jadi kosong, karakter seperti & dan < di-escape."""
    if nilai is None or (isinstance(nilai, float) and pd.isna(nilai)):
        return ""
    return html.escape(str(nilai).strip())


def buat_peta(
    df_tni: pd.DataFrame,
    df_pulau: pd.DataFrame,
    df_alki: pd.DataFrame,
    df_asing: pd.DataFrame,
    tampil: dict[str, bool],
    radius_km: list[int],
    terpilih: pd.Series | None = None,
    tni_terdekat: pd.Series | None = None,
    pulau_terdekat: pd.Series | None = None,
) -> folium.Map:
    """Susun semua lapisan jadi satu peta.

    tampil      : {"tni": True, "pulau": True, "alki": True, "asing": True, "lingkaran": True}
    radius_km   : daftar radius lingkaran dari tiap pangkalan asing, mis. [500, 1000]
    terpilih    : baris pangkalan asing yang dipilih user (ditarik garis ke TNI terdekat)
    """
    # Peta dasar: Esri World Ocean (bebas API key, cocok untuk tema maritim). OpenStreetMap sebagai alternatif.
    m = folium.Map(location=[-2.0, 118.0], zoom_start=5, tiles=None, control_scale=True)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; GEBCO, NOAA, National Geographic, DeLorme, HERE, Geonames.org",
        name="Peta dasar: Esri Ocean",
        control=True,
    ).add_to(m)
    folium.TileLayer("OpenStreetMap", name="Peta dasar: OpenStreetMap", show=False).add_to(m)

    # --- Lapisan 1: lingkaran jarak (digambar dulu supaya di bawah titik) ---
    if tampil.get("lingkaran") and tampil.get("asing"):
        fg = folium.FeatureGroup(name="Lingkaran jarak dari pangkalan asing", show=True)
        for _, b in df_asing.iterrows():
            # radius terkecil diisi warna tipis, radius lebih besar hanya garis putus-putus (agar tidak menumpuk)
            for i, r in enumerate(sorted(radius_km)):
                folium.Circle(
                    location=[b["lat"], b["lon"]],
                    radius=r * 1000,  # Folium pakai meter
                    color=WARNA_NEGARA.get(b["negara"], "#757575"),
                    weight=1.2,
                    fill=(i == 0),
                    fill_opacity=0.07,
                    opacity=0.6 if i == 0 else 0.35,
                    dash_array=None if i == 0 else "4 6",
                    tooltip=f"{b['nama']} – radius {r} km",
                ).add_to(fg)
        fg.add_to(m)

    # --- Lapisan 2: ALKI (garis) ---
    if tampil.get("alki"):
        fg = folium.FeatureGroup(name="ALKI (alur laut kepulauan)", show=True)
        for nama, grup in df_alki.groupby("alki"):
            titik = grup[["lat", "lon"]].values.tolist()
            folium.PolyLine(titik, color=WARNA_ALKI[nama], weight=3, opacity=0.7, dash_array="10 8",
                            tooltip=f"{nama} (ilustrasi, bukan koordinat resmi)").add_to(fg)
            folium.Marker(titik[0], icon=folium.DivIcon(html=f"<div style='font-size:11px;font-weight:bold;color:{WARNA_ALKI[nama]}'>{nama}</div>")).add_to(fg)
        fg.add_to(m)

    # --- Lapisan 3: pulau terluar, pos perbatasan, wilayah rawan ---
    if tampil.get("pulau"):
        fg = folium.FeatureGroup(name="Pulau terluar & perbatasan", show=True)
        for _, b in df_pulau.iterrows():
            folium.RegularPolygonMarker(
                location=[b["lat"], b["lon"]],
                number_of_sides=3 if b["jenis"] == "pulau_terluar" else 4,
                radius=7,
                color=WARNA_PULAU[b["jenis"]],
                fill_color=WARNA_PULAU[b["jenis"]],
                fill_opacity=0.9,
                popup=folium.Popup(_popup(b["nama"], b, [("Jenis", "jenis"), ("Provinsi", "provinsi"), ("Berbatasan dengan", "berbatasan_dengan"), ("Catatan", "keterangan")]), max_width=300),
                tooltip=f"{LABEL_PULAU[b['jenis']]}: {b['nama']}",
            ).add_to(fg)
        fg.add_to(m)

    # --- Lapisan 4: markas TNI ---
    if tampil.get("tni"):
        fg = folium.FeatureGroup(name="Markas TNI", show=True)
        for _, b in df_tni.iterrows():
            folium.CircleMarker(
                location=[b["lat"], b["lon"]],
                radius=6 if b["jenis"] in ("Lanud", "Lantamal", "Lanal") else 8,
                color="white",
                weight=1,
                fill=True,
                fill_color=WARNA_MATRA[b["matra"]],
                fill_opacity=0.95,
                popup=folium.Popup(_popup(b["nama"], b, [("Matra", "matra"), ("Jenis", "jenis"), ("Lokasi", "kota"), ("Catatan", "keterangan")]), max_width=300),
                tooltip=f"TNI {b['matra']}: {b['nama']}",
            ).add_to(fg)
        fg.add_to(m)

    # --- Lapisan 5: pangkalan asing di kawasan ---
    if tampil.get("asing"):
        fg = folium.FeatureGroup(name="Pangkalan asing di kawasan", show=True)
        for _, b in df_asing.iterrows():
            folium.Marker(
                location=[b["lat"], b["lon"]],
                icon=folium.DivIcon(
                    icon_size=(18, 18),
                    icon_anchor=(9, 9),
                    html=f"<div style='width:16px;height:16px;transform:rotate(45deg);background:{WARNA_NEGARA.get(b['negara'], '#757575')};border:2px solid white;box-shadow:0 0 3px #333'></div>",
                ),
                popup=folium.Popup(_popup(b["nama"], b, [("Operator", "negara_operator"), ("Lokasi", "negara_tuan_rumah"), ("Jenis", "jenis"), ("Status", "status"), ("Catatan", "keterangan")]), max_width=320),
                tooltip=f"{b['negara']}: {b['nama']}",
            ).add_to(fg)
        fg.add_to(m)

    # --- Lapisan 6: garis analisis dari pangkalan terpilih ---
    if terpilih is not None:
        fg = folium.FeatureGroup(name="Analisis jarak (pangkalan terpilih)", show=True)
        folium.CircleMarker([terpilih["lat"], terpilih["lon"]], radius=14, color="#000", weight=2, fill=False,
                            tooltip=f"Terpilih: {terpilih['nama']}").add_to(fg)
        for target, warna, label in ((tni_terdekat, "#1565c0", "Markas TNI terdekat"), (pulau_terdekat, "#00897b", "Pulau terluar/perbatasan terdekat")):
            if target is not None:
                folium.PolyLine([[terpilih["lat"], terpilih["lon"]], [target["lat"], target["lon"]]],
                                color=warna, weight=3, opacity=0.9, tooltip=f"{label}: {target['nama']}").add_to(fg)
        fg.add_to(m)

    folium.LayerControl(collapsed=True).add_to(m)
    return m


def legenda_html() -> str:
    """Legenda kecil dalam HTML untuk ditempel di bawah peta (Streamlit markdown)."""
    def kotak(warna, bentuk="circle"):
        radius = "50%" if bentuk == "circle" else "0"
        rot = "transform:rotate(45deg);" if bentuk == "diamond" else ""
        return f"<span style='display:inline-block;width:11px;height:11px;background:{warna};border-radius:{radius};{rot}margin:0 4px 0 10px'></span>"

    tni = "".join(f"{kotak(w)}{m}" for m, w in WARNA_MATRA.items())
    asing = "".join(f"{kotak(w, 'diamond')}{n}" for n, w in WARNA_NEGARA.items())
    pulau = "".join(f"{kotak(w, 'square')}{LABEL_PULAU[j]}" for j, w in WARNA_PULAU.items())
    return (
        "<div style='font-size:12px;line-height:2'>"
        f"<b>Markas TNI</b> (lingkaran):{tni}<br>"
        f"<b>Pangkalan asing</b> (belah ketupat):{asing}<br>"
        f"<b>Batas</b>:{pulau}"
        "</div>"
    )
