"""
app.py - WebGIS Pertahanan Indonesia
=====================================
Jalankan dengan:   streamlit run app.py

Alur besar file ini (baca dari atas ke bawah):
  1. Import library + konfigurasi halaman
  2. Muat data (CSV di folder data/)
  3. Sidebar: pilih lapisan, radius lingkaran, pangkalan asing yang dianalisis
  4. Hitung jarak (src/geo.py)
  5. Tampilkan: angka ringkasan -> tab peta / analisis jarak / statistik / data / cara kerja

Tiap bagian punya komentar "APA" dan "KENAPA". Istilah asing ada di docs/BELAJAR.md.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from src import geo, muat_data
from src.peta import LABEL_PULAU, WARNA_MATRA, WARNA_NEGARA, buat_peta, legenda_html

# ----------------------------------------------------------------------------
# 0. KONFIGURASI HALAMAN
# ----------------------------------------------------------------------------
st.set_page_config(page_title="WebGIS Pertahanan Indonesia", page_icon="🛡️", layout="wide")

DISCLAIMER = (
    "ℹ️ Semua titik di peta ini berasal dari **sumber publik** (Wikipedia, situs resmi, media, laporan "
    "think tank). Koordinat adalah perkiraan lokasi umum, bukan data operasional. Ini project edukasi "
    "dan portofolio, bukan dokumen resmi."
)
TEMPLATE = "plotly_white"


def rapikan(fig: go.Figure, tinggi: int = 420) -> go.Figure:
    """Gaya seragam untuk semua grafik Plotly: grid tipis, margin kecil, legenda di atas."""
    fig.update_layout(
        template=TEMPLATE,
        height=tinggi,
        margin=dict(l=10, r=20, t=70, b=10),
        title=dict(y=0.97, yanchor="top", x=0, xanchor="left", font=dict(size=15)),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, title=None),
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#e6e6e6", zeroline=False)
    return fig


# ----------------------------------------------------------------------------
# 1. MUAT DATA (di-cache: CSV cuma dibaca sekali walau halaman rerun terus)
# ----------------------------------------------------------------------------
@st.cache_data
def ambil_data():
    return (
        muat_data.muat_markas_tni(),
        muat_data.muat_pulau_terluar(),
        muat_data.muat_alki(),
        muat_data.muat_pangkalan_asing(),
        muat_data.muat_anggaran_indonesia(),
        muat_data.muat_anggaran_kawasan(),
        muat_data.muat_alutsista(),
    )


@st.cache_data
def ambil_tabel_jarak(df_asing, df_tni, df_pulau):
    return geo.tabel_jarak(df_asing, df_tni, df_pulau)


df_tni_semua, df_pulau, df_alki, df_asing_semua, df_anggaran, df_kawasan, df_alutsista = ambil_data()

# ----------------------------------------------------------------------------
# 2. SIDEBAR: filter & pilihan
# ----------------------------------------------------------------------------
with st.sidebar:
    st.title("🛡️ WebGIS Pertahanan")
    st.caption("Peta interaktif markas TNI, perbatasan, dan pangkalan asing di kawasan.")

    st.subheader("Lapisan peta")
    tampil = {
        "tni": st.checkbox("Markas TNI", True),
        "pulau": st.checkbox("Pulau terluar & perbatasan", True),
        "alki": st.checkbox("ALKI (alur laut)", True),
        "asing": st.checkbox("Pangkalan asing di kawasan", True),
        "lingkaran": st.checkbox("Lingkaran jarak dari pangkalan asing", True),
    }

    st.subheader("Filter")
    matra = st.multiselect("Matra TNI", ["AD", "AL", "AU", "Gabungan"], default=["AD", "AL", "AU", "Gabungan"])
    negara_pilihan = st.multiselect(
        "Negara operator pangkalan asing",
        sorted(df_asing_semua["negara"].unique()),
        default=sorted(df_asing_semua["negara"].unique()),
    )
    radius_km = st.multiselect("Radius lingkaran (km)", [250, 500, 1000, 1500], default=[500, 1000])

    st.subheader("Analisis jarak")
    nama_terpilih = st.selectbox(
        "Pilih satu pangkalan asing",
        ["(tidak ada)"] + df_asing_semua.sort_values("nama")["nama"].tolist(),
        index=0,
        help="Peta akan menarik garis ke markas TNI dan pulau terluar terdekat.",
    )

    mode_belajar = st.toggle("🎓 Mode belajar", value=False, help="Tampilkan rumus & potongan kode di tiap bagian.")
    st.caption("Data publik, koordinat perkiraan. Lihat tab *Data & Sumber*.")

# APA: terapkan filter. KENAPA: df_*_semua tetap utuh supaya angka pembanding tidak ikut berubah.
df_tni = df_tni_semua[df_tni_semua["matra"].isin(matra)]
df_asing = df_asing_semua[df_asing_semua["negara"].isin(negara_pilihan)]

# ----------------------------------------------------------------------------
# 3. HITUNG: jarak dari pangkalan terpilih
# ----------------------------------------------------------------------------
terpilih = tni_terdekat = pulau_terdekat = None
jarak_tni = jarak_pulau = None
if nama_terpilih != "(tidak ada)":
    terpilih = df_asing_semua[df_asing_semua["nama"] == nama_terpilih].iloc[0]
    if not df_tni.empty:
        tni_terdekat, jarak_tni = geo.titik_terdekat(terpilih["lat"], terpilih["lon"], df_tni)
    pulau_terdekat, jarak_pulau = geo.titik_terdekat(terpilih["lat"], terpilih["lon"], df_pulau)

tabel_jarak = ambil_tabel_jarak(df_asing_semua, df_tni_semua, df_pulau)

# ----------------------------------------------------------------------------
# 4. HEADER + ANGKA RINGKASAN
# ----------------------------------------------------------------------------
st.title("🛡️ WebGIS Pertahanan Indonesia")
st.markdown(
    "Peta interaktif **markas TNI**, **pulau terluar & perbatasan**, **ALKI**, dan **pangkalan militer asing "
    "di kawasan** lengkap dengan lingkaran jarak dan analisis pangkalan TNI terdekat."
)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Markas TNI di peta", len(df_tni), help="Kodam, Koarmada, Lantamal, Lanud, Kogabwilhan")
k2.metric("Pulau terluar & pos batas", len(df_pulau))
k3.metric("Pangkalan asing di kawasan", len(df_asing))
k4.metric("Negara operator", df_asing["negara"].nunique())
paling_dekat = tabel_jarak.iloc[0]
k5.metric("Asing terdekat ke batas RI", f"{paling_dekat['jarak_pulau_km']:,} km", help=f"{paling_dekat['nama']} → {paling_dekat['pulau_terdekat']}")

tab_peta, tab_jarak, tab_stat, tab_data, tab_cara = st.tabs(
    ["🗺️ Peta", "📏 Analisis Jarak", "📊 Statistik", "📋 Data & Sumber", "🧭 Cara Kerja"]
)

# ----------------------------------------------------------------------------
# 5a. TAB PETA
# ----------------------------------------------------------------------------
with tab_peta:
    if terpilih is not None:
        c1, c2, c3 = st.columns(3)
        c1.info(f"**Terpilih:** {terpilih['nama']}  \n{terpilih['negara_operator']} · {terpilih['jenis']}")
        if tni_terdekat is not None:
            c2.success(f"**Markas TNI terdekat:** {tni_terdekat['nama']}  \n≈ **{jarak_tni:,.0f} km** ke arah {geo.arah_kompas(terpilih['lat'], terpilih['lon'], tni_terdekat['lat'], tni_terdekat['lon'])}")
        c3.warning(f"**Batas terdekat:** {pulau_terdekat['nama']}  \n≈ **{jarak_pulau:,.0f} km** ({LABEL_PULAU[pulau_terdekat['jenis']].lower()})")

    peta = buat_peta(df_tni, df_pulau, df_alki, df_asing, tampil, radius_km, terpilih, tni_terdekat, pulau_terdekat)
    # returned_objects=[] -> klik di peta TIDAK memicu rerun (lebih ringan)
    st_folium(peta, height=600, use_container_width=True, returned_objects=[])
    st.markdown(legenda_html(), unsafe_allow_html=True)
    st.caption(DISCLAIMER)

    if mode_belajar:
        with st.expander("🎓 Di balik peta ini"):
            st.markdown(
                """
Peta dibangun di `src/peta.py` dengan **Folium** (pembungkus Python untuk Leaflet.js).
Polanya selalu sama: bikin `folium.Map`, bikin `FeatureGroup` per lapisan, tambah marker ke grup, lalu
`LayerControl` supaya user bisa matikan lapisan dari peta.

```python
m = folium.Map(location=[-2, 118], zoom_start=5)
fg = folium.FeatureGroup(name="Markas TNI")
for _, b in df_tni.iterrows():
    folium.CircleMarker([b["lat"], b["lon"]], radius=7, fill_color=WARNA_MATRA[b["matra"]],
                        tooltip=b["nama"]).add_to(fg)
fg.add_to(m)
folium.LayerControl().add_to(m)
```

Lingkaran jarak pakai `folium.Circle(radius=meter)`: radius dalam **meter**, jadi 500 km = 500.000.
Di Streamlit, peta ditempel dengan `st_folium(m, returned_objects=[])`.
"""
            )

# ----------------------------------------------------------------------------
# 5b. TAB ANALISIS JARAK
# ----------------------------------------------------------------------------
with tab_jarak:
    st.subheader("Seberapa dekat tiap pangkalan asing ke wilayah Indonesia?")
    st.markdown(
        "Untuk setiap pangkalan asing dihitung **jarak garis lurus** (great-circle) ke markas TNI terdekat dan ke "
        "pulau terluar / pos perbatasan terdekat. Angka ini **bukan** penilaian ancaman; cuma geometri."
    )
    tabel_tampil = tabel_jarak[tabel_jarak["nama"].isin(df_asing["nama"])].copy()
    tabel_tampil["negara"] = tabel_tampil["negara_operator"].apply(geo.kelompok_negara)

    teratas = tabel_tampil.head(20).sort_values("jarak_pulau_km", ascending=True)
    fig = px.bar(
        teratas,
        x="jarak_pulau_km",
        y="nama",
        color="negara",
        orientation="h",
        color_discrete_map=WARNA_NEGARA,
        text="jarak_pulau_km",
        hover_data={"pulau_terdekat": True, "tni_terdekat": True, "jarak_tni_km": True, "negara": False},
        title="20 pangkalan asing terdekat ke pulau terluar / pos perbatasan Indonesia (km)",
        labels={"jarak_pulau_km": "Jarak ke batas terdekat (km)", "nama": "", "negara": "Negara"},
    )
    fig.update_traces(texttemplate="%{text:,} km", textposition="outside", cliponaxis=False)
    fig.update_layout(yaxis=dict(categoryorder="total descending", autorange="reversed"))
    fig.update_xaxes(range=[0, teratas["jarak_pulau_km"].max() * 1.2])
    st.plotly_chart(rapikan(fig, 640), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        ringkas = (
            tabel_tampil.groupby("negara")
            .agg(jumlah=("nama", "count"), rata_rata_km=("jarak_pulau_km", "mean"), terdekat_km=("jarak_pulau_km", "min"))
            .round(0)
            .sort_values("terdekat_km")
            .reset_index()
        )
        fig2 = px.bar(
            ringkas, x="negara", y="jumlah", color="negara", color_discrete_map=WARNA_NEGARA, text="jumlah",
            title="Jumlah pangkalan asing per negara operator", labels={"jumlah": "Jumlah", "negara": ""},
        )
        fig2.update_traces(textposition="outside", cliponaxis=False)
        fig2.update_layout(showlegend=False)
        st.plotly_chart(rapikan(fig2, 380), use_container_width=True)
    with c2:
        dalam = pd.DataFrame(
            {
                "Radius": ["≤ 500 km", "≤ 1.000 km", "> 1.000 km"],
                "Pangkalan asing": [
                    (tabel_tampil["jarak_pulau_km"] <= 500).sum(),
                    ((tabel_tampil["jarak_pulau_km"] > 500) & (tabel_tampil["jarak_pulau_km"] <= 1000)).sum(),
                    (tabel_tampil["jarak_pulau_km"] > 1000).sum(),
                ],
            }
        )
        fig3 = px.bar(dalam, x="Radius", y="Pangkalan asing", text="Pangkalan asing",
                      title="Pangkalan asing menurut jarak ke batas Indonesia",
                      color_discrete_sequence=["#b23a3a"])
        fig3.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(rapikan(fig3, 380), use_container_width=True)

    st.markdown("**Tabel lengkap** (klik judul kolom untuk mengurutkan):")
    st.dataframe(
        tabel_tampil[["nama", "negara_operator", "jenis", "pulau_terdekat", "jarak_pulau_km", "tni_terdekat", "jarak_tni_km", "arah_ke_tni", "jumlah_tni_500km", "jumlah_tni_1000km"]]
        .rename(columns={
            "nama": "Pangkalan asing", "negara_operator": "Operator", "jenis": "Jenis",
            "pulau_terdekat": "Batas terdekat", "jarak_pulau_km": "Jarak ke batas (km)",
            "tni_terdekat": "Markas TNI terdekat", "jarak_tni_km": "Jarak ke TNI (km)", "arah_ke_tni": "Arah ke TNI",
            "jumlah_tni_500km": "Markas TNI ≤500 km", "jumlah_tni_1000km": "Markas TNI ≤1.000 km",
        }),
        use_container_width=True, hide_index=True, height=420,
    )
    st.info(
        "💡 **Cara baca:** pangkalan di Singapura dan Nicobar (India) secara geografis paling dekat, tapi keduanya negara "
        "mitra. Pos China di Spratly ada di 500–900 km dari Natuna, dan tidak ada markas TNI dalam radius 500 km dari "
        "pos-pos itu. Jarak hanya satu faktor; niat politik, jenis alutsista, dan aliansi jauh lebih menentukan."
    )
    if mode_belajar:
        with st.expander("🎓 Rumus haversine di balik angka ini"):
            st.markdown("Jarak dua titik di permukaan bola (φ = lintang, λ = bujur dalam radian, R = 6.371 km):")
            st.latex(r"a = \sin^2\!\left(\tfrac{\Delta\varphi}{2}\right) + \cos\varphi_1 \cos\varphi_2 \sin^2\!\left(\tfrac{\Delta\lambda}{2}\right)")
            st.latex(r"d = 2R \cdot \operatorname{atan2}\left(\sqrt{a}, \sqrt{1-a}\right)")
            st.markdown(
                """
Kodenya di `src/geo.py`:

```python
from src import geo
geo.haversine_km(3.95, 108.38, 9.55, 112.89)   # Ranai -> Fiery Cross Reef ≈ 797 km
geo.titik_terdekat(9.55, 112.89, df_tni)       # (baris Lanal Ranai, 797.0)
```
Kenapa bukan Pythagoras biasa? Karena bumi bulat: 1° bujur di khatulistiwa ≈ 111 km, di Oslo cuma ≈ 56 km.
"""
            )

# ----------------------------------------------------------------------------
# 5c. TAB STATISTIK
# ----------------------------------------------------------------------------
with tab_stat:
    st.subheader("Anggaran pertahanan Indonesia")
    c1, c2 = st.columns([3, 2])
    with c1:
        fig = px.bar(
            df_anggaran, x="tahun", y="anggaran_rp_triliun", text="anggaran_rp_triliun",
            color="keyakinan", color_discrete_map={"sedang": "#b23a3a", "rendah": "#e0a0a0"},
            title="Pagu anggaran Kementerian Pertahanan (Rp triliun)",
            labels={"anggaran_rp_triliun": "Rp triliun", "tahun": "", "keyakinan": "Keyakinan data"},
            hover_data={"catatan": True, "persen_pdb": True},
        )
        fig.update_traces(texttemplate="%{text:.0f}", textposition="outside", cliponaxis=False)
        fig.update_xaxes(dtick=1)
        st.plotly_chart(rapikan(fig, 420), use_container_width=True)
    with c2:
        fig = px.line(df_anggaran, x="tahun", y="persen_pdb", markers=True, title="Anggaran pertahanan (% PDB, perkiraan)",
                      labels={"persen_pdb": "% PDB", "tahun": ""}, color_discrete_sequence=["#b23a3a"])
        fig.update_yaxes(range=[0, max(1.6, df_anggaran["persen_pdb"].max() * 1.2)])
        fig.update_xaxes(dtick=2)
        st.plotly_chart(rapikan(fig, 420), use_container_width=True)
    st.caption("Angka pagu awal APBN (bukan realisasi), dibulatkan dari Nota Keuangan & liputan media. Nilai 2026 adalah usulan RAPBN; warna muda = keyakinan rendah.")

    st.subheader("Perbandingan kawasan (2024)")
    c1, c2 = st.columns(2)
    urut = df_kawasan.sort_values("belanja_usd_miliar_2024", ascending=True)
    warna_negara_stat = {n: ("#b23a3a" if n == "Indonesia" else "#c9c3bb") for n in urut["negara"]}
    with c1:
        fig = px.bar(urut, x="belanja_usd_miliar_2024", y="negara", orientation="h", text="belanja_usd_miliar_2024",
                     color="negara", color_discrete_map=warna_negara_stat, log_x=True,
                     title="Belanja militer 2024 (US$ miliar, skala log)",
                     labels={"belanja_usd_miliar_2024": "US$ miliar", "negara": ""})
        fig.update_traces(texttemplate="%{text:,.1f}", textposition="outside", cliponaxis=False)
        fig.update_layout(showlegend=False)
        st.plotly_chart(rapikan(fig, 440), use_container_width=True)
    with c2:
        urut2 = df_kawasan.sort_values("persen_pdb_2024", ascending=True)
        fig = px.bar(urut2, x="persen_pdb_2024", y="negara", orientation="h", text="persen_pdb_2024",
                     color="negara", color_discrete_map=warna_negara_stat,
                     title="Belanja militer 2024 (% PDB)", labels={"persen_pdb_2024": "% PDB", "negara": ""})
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False)
        fig.update_layout(showlegend=False)
        fig.update_xaxes(range=[0, urut2["persen_pdb_2024"].max() * 1.25])
        st.plotly_chart(rapikan(fig, 440), use_container_width=True)
    st.info(
        "💡 Secara nominal Indonesia nomor dua di ASEAN setelah Singapura, tapi secara **% PDB** termasuk yang paling rendah "
        "di kawasan (di bawah 1%). Skala log dipakai di grafik kiri karena China 30× lebih besar dari Indonesia; tanpa log, "
        "batang negara ASEAN tidak kelihatan."
    )

    st.subheader("Alutsista utama per matra (perkiraan publik)")
    st.dataframe(df_alutsista.rename(columns={"matra": "Matra", "alutsista": "Alutsista", "jumlah_perkiraan": "Jumlah (perkiraan)", "status": "Status", "sumber": "Sumber"}),
                 use_container_width=True, hide_index=True)
    st.caption("Sumber: Wikipedia & liputan media; jumlah bisa berbeda dengan data resmi. Belanja militer: SIPRI Military Expenditure Database (pembulatan).")

    if mode_belajar:
        with st.expander("🎓 Kenapa pakai skala log?"):
            st.markdown(
                """
Kalau satu nilai 30× lebih besar dari yang lain, grafik biasa (linear) bikin nilai kecil jadi garis tipis.
Skala logaritmik menjadikan tiap "langkah" sumbu = dikali 10, jadi 5, 50, 500 terlihat berjarak sama.

```python
px.bar(df, x="belanja", y="negara", log_x=True)
```
Harganya: pembaca harus sadar sumbunya log, makanya ditulis di judul grafik.
"""
            )

# ----------------------------------------------------------------------------
# 5d. TAB DATA & SUMBER
# ----------------------------------------------------------------------------
with tab_data:
    st.subheader("Dataset")
    st.markdown(DISCLAIMER)
    pilih = st.radio("Pilih tabel", ["Markas TNI", "Pulau terluar & perbatasan", "Pangkalan asing", "ALKI", "Anggaran Indonesia", "Anggaran kawasan", "Alutsista"], horizontal=True)
    peta_df = {
        "Markas TNI": (df_tni_semua, "markas_tni.csv"),
        "Pulau terluar & perbatasan": (df_pulau, "pulau_terluar_perbatasan.csv"),
        "Pangkalan asing": (df_asing_semua, "pangkalan_asing.csv"),
        "ALKI": (df_alki, "alki.csv"),
        "Anggaran Indonesia": (df_anggaran, "anggaran_indonesia.csv"),
        "Anggaran kawasan": (df_kawasan, "anggaran_kawasan.csv"),
        "Alutsista": (df_alutsista, "alutsista.csv"),
    }
    df_pilih, nama_file = peta_df[pilih]
    kolom_config = {"url_sumber": st.column_config.LinkColumn("Sumber (link)")} if "url_sumber" in df_pilih.columns else None
    st.dataframe(df_pilih.replace("", "–"), use_container_width=True, hide_index=True, column_config=kolom_config, height=420)
    st.download_button("⬇️ Unduh CSV", df_pilih.to_csv(index=False).encode("utf-8"), file_name=nama_file, mime="text/csv")

    st.subheader("Catatan kejujuran data")
    st.markdown(
        """
- **Semua data publik.** Tiap baris punya kolom `sumber` dan `url_sumber`. Tidak ada informasi yang tidak bisa dicari di internet.
- **Koordinat = perkiraan lokasi umum** (kota/pangkalan), cukup untuk peta skala nasional, bukan alamat persis.
- **ALKI digambar sebagai ilustrasi** garis tengah alur; koordinat resmi ada di PP No. 37/2002.
- **Daftar markas TNI mengikuti Wikipedia** dan bisa tertinggal dari reorganisasi terbaru (mis. pembentukan Kodam/Koarmada baru).
- **"Pangkalan asing di kawasan" adalah label netral.** Banyak di antaranya milik negara mitra Indonesia. Penilaian ancaman ada di README sebagai analisis pribadi, bukan bagian dari data.
- **Anggaran & alutsista** adalah angka pembulatan dari sumber sekunder; kolom `keyakinan` menandai yang perlu dicek ulang.
"""
    )

# ----------------------------------------------------------------------------
# 5e. TAB CARA KERJA
# ----------------------------------------------------------------------------
with tab_cara:
    st.subheader("Alur data → rumus → peta")
    st.graphviz_chart(
        """
digraph G {
  rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#f0efec", fontname="sans-serif", fontsize=11];
  csv  [label="data/*.csv\n(7 file, tiap baris ada sumber)"];
  muat [label="src/muat_data.py\nbaca CSV, validasi koordinat"];
  geo  [label="src/geo.py\nhaversine, titik terdekat,\njumlah dalam radius"];
  peta [label="src/peta.py\nFolium: lapisan, marker,\nlingkaran, garis"];
  app  [label="app.py\nsidebar, tab, grafik Plotly"];
  user [label="Browser\n(Streamlit)", fillcolor="#e8d9d9"];
  csv -> muat -> geo -> app; muat -> peta -> app; app -> user; user -> app [label="geser/klik → rerun", fontsize=9];
}
"""
    )
    st.markdown(
        """
| Langkah | File | Yang terjadi |
|---|---|---|
| 1 | `data/*.csv` | Data mentah: markas TNI, pulau terluar, ALKI, pangkalan asing, anggaran. Satu baris = satu objek + sumber. |
| 2 | `src/muat_data.py` | Baca CSV jadi DataFrame pandas, isi kosong → "", tolak koordinat di luar Indonesia. |
| 3 | `src/geo.py` | Rumus **haversine** (jarak di bola), **titik terdekat**, **hitung dalam radius**, **arah kompas**. Murni Python, dites di `tests/`. |
| 4 | `src/peta.py` | Bangun peta Folium: tiap kategori jadi *FeatureGroup* supaya bisa dimatikan dari peta. |
| 5 | `app.py` | Sidebar → filter → hitung → tampilkan. Setiap interaksi menjalankan ulang file dari atas. |

**Konsep GIS yang dipakai**

- **Koordinat geografis** (lintang/bujur, derajat desimal, WGS84). Lintang negatif = selatan khatulistiwa.
- **Layer / lapisan**: peta disusun dari lapisan terpisah (titik, garis, lingkaran) yang bisa dinyalakan satu-satu.
- **Buffer**: lingkaran radius X km dari sebuah titik. Di sini dipakai untuk "jangkauan" ilustratif dari pangkalan.
- **Nearest-neighbour**: mencari objek terdekat dengan menghitung jarak ke semua kandidat lalu ambil minimum.
- **Tile map**: gambar latar peta diambil per kotak kecil dari server (CartoDB), sedangkan titik-titik kita digambar di atasnya.
"""
    )
    st.caption(DISCLAIMER)
