# 🏋️ Latihan

Urut dari gampang ke susah. Tiap latihan ada petunjuk dan kunci jawaban di bagian yang bisa dibuka. Jangan buka
kunci sebelum nyoba minimal 10 menit. Habis tiap latihan: jalankan `python -m pytest tests/` dan `streamlit run app.py`.

---

### Latihan 1 — Tambah satu pulau terluar (edit CSV saja) ⭐

Tambahkan **Pulau Sophialouisa** (NTB, titik paling selatan Lombok) ke `data/pulau_terluar_perbatasan.csv`:
jenis `pulau_terluar`, provinsi `Nusa Tenggara Barat`, lat `-8.9100`, lon `116.0000`, berbatasan dengan
`Australia`, sumber `Wikipedia: Pulau Sophialouisa`, url `https://id.wikipedia.org/wiki/Pulau_Sophialouisa`.

Lalu buka dashboard dan cari segitiganya di selatan Lombok.

<details><summary>Petunjuk</summary>
Salin baris terakhir, ganti `id` jadi 25 dan nilainya. Kolom yang mengandung koma harus dibungkus tanda kutip.
</details>

<details><summary>Kunci</summary>

```
25,Pulau Sophialouisa,pulau_terluar,Nusa Tenggara Barat,-8.9100,116.0000,Australia,Titik paling selatan Lombok,Wikipedia: Pulau Sophialouisa,https://id.wikipedia.org/wiki/Pulau_Sophialouisa
```
Kalau `test_dataset_bisa_dimuat_dan_valid` masih hijau, koordinatmu valid. Angka KPI "Pulau terluar & pos batas"
naik jadi 25.
</details>

---

### Latihan 2 — Radius baru 750 km ⭐

Di sidebar, pilihan radius cuma 250/500/1000/1500. Tambahkan **750**.

<details><summary>Petunjuk</summary>
Cari `st.multiselect("Radius lingkaran (km)"` di `app.py`. Daftarnya ada di argumen kedua.
</details>

<details><summary>Kunci</summary>

```python
radius_km = st.multiselect("Radius lingkaran (km)", [250, 500, 750, 1000, 1500], default=[500, 1000])
```
Perhatikan `src/peta.py` tidak perlu diubah sama sekali: dia menerima daftar apa pun. Itu manfaat memisahkan
tampilan dari logika.
</details>

---

### Latihan 3 — Jarak Jakarta ke semua Kodam ⭐⭐

Tanpa Streamlit, di `python`, buat tabel jarak dari Mabes TNI Cilangkap ke setiap Kodam, urut dari terdekat.

<details><summary>Petunjuk</summary>
Pakai `geo.jarak_ke_semua(lat, lon, df)` lalu simpan hasilnya ke kolom baru. Filter `jenis == "Kodam"` dulu.
</details>

<details><summary>Kunci</summary>

```python
from src import geo, muat_data
df = muat_data.muat_markas_tni()
kodam = df[df["jenis"] == "Kodam"].copy()
kodam["jarak_km"] = geo.jarak_ke_semua(-6.3362, 106.8998, kodam).round()
print(kodam.sort_values("jarak_km")[["nama", "kota", "jarak_km"]])
```
Kodam Jaya 15 km, Kodam III/Siliwangi ±120 km, ... Kodam XVII/Cenderawasih ±3.800 km. Jauh ya.
</details>

---

### Latihan 4 — Hitung jumlah pangkalan asing dalam radius dari tiap markas TNI ⭐⭐

Kebalikan dari tab Analisis Jarak: untuk **setiap markas TNI**, berapa pangkalan asing dalam 1.000 km?
Tampilkan 10 teratas.

<details><summary>Petunjuk</summary>
`geo.jumlah_dalam_radius(lat, lon, df_asing, 1000)` dipanggil per baris TNI. Pakai `df.apply(..., axis=1)`.
</details>

<details><summary>Kunci</summary>

```python
from src import geo, muat_data
tni = muat_data.muat_markas_tni()
asing = muat_data.muat_pangkalan_asing()
tni["asing_1000km"] = tni.apply(lambda b: geo.jumlah_dalam_radius(b["lat"], b["lon"], asing, 1000), axis=1)
print(tni.sort_values("asing_1000km", ascending=False)[["nama", "matra", "asing_1000km"]].head(10))
```
Markas di Kepulauan Riau dan Sumatera Utara ada di puncak: Selat Malaka memang ramai.
Bonus: tambahkan hasil ini sebagai grafik batang baru di tab Analisis Jarak.
</details>

---

### Latihan 5 — Marker ikut ukuran ⭐⭐

Di `src/peta.py`, markas TNI digambar dengan radius 6 atau 8 piksel. Ubah supaya **Kodam dan Koarmada** 10 piksel,
**Kogabwilhan dan Mabes** 12 piksel, sisanya 6.

<details><summary>Petunjuk</summary>
Bikin kamus `UKURAN_JENIS = {"Kodam": 10, ...}` lalu `radius=UKURAN_JENIS.get(b["jenis"], 6)`.
</details>

<details><summary>Kunci</summary>

```python
UKURAN_JENIS = {"Kodam": 10, "Koarmada": 10, "Kogabwilhan": 12, "Markas Besar": 12}
...
radius=UKURAN_JENIS.get(b["jenis"], 6),
```
Kamus + `.get(kunci, default)` adalah pola yang jauh lebih rapi daripada if-elif panjang.
</details>

---

### Latihan 6 — Klik titik di peta → tampilkan detail ⭐⭐⭐

Sekarang klik di peta tidak melakukan apa-apa (`returned_objects=[]`). Ubah supaya kalau user mengklik marker,
nama objek yang diklik muncul di bawah peta.

<details><summary>Petunjuk</summary>
`st_folium` mengembalikan dict. Minta `returned_objects=["last_object_clicked_tooltip"]`, lalu tampilkan dengan
`st.write`. Siap-siap: setiap klik sekarang memicu rerun.
</details>

<details><summary>Kunci</summary>

```python
hasil = st_folium(peta, height=600, use_container_width=True, returned_objects=["last_object_clicked_tooltip"])
if hasil and hasil.get("last_object_clicked_tooltip"):
    st.success(f"Kamu mengklik: {hasil['last_object_clicked_tooltip']}")
```
Rasakan bedanya: peta jadi sedikit lebih lambat karena rerun. Itu trade-off interaktivitas vs performa.
</details>

---

### Latihan 7 — Garis ZEE dengan GeoJSON ⭐⭐⭐

Unduh GeoJSON batas ZEE Indonesia dari Marine Regions (marineregions.org, cari "Indonesia EEZ"), simpan di
`data/zee_indonesia.geojson`, dan tambahkan sebagai lapisan di `peta.py` dengan `folium.GeoJson(...)`.

<details><summary>Petunjuk</summary>

```python
import json
with open("data/zee_indonesia.geojson") as f:
    zee = json.load(f)
folium.GeoJson(zee, name="ZEE Indonesia", style_function=lambda x: {"color": "#b23a3a", "weight": 1.5, "fillOpacity": 0.03}).add_to(m)
```
GeoJSON pakai urutan **[lon, lat]**, tapi `folium.GeoJson` sudah mengurusnya. File ZEE bisa beberapa MB; kalau
lambat, sederhanakan dulu dengan GeoPandas: `gdf.simplify(0.05)`.
</details>

Setelah ini kamu sudah pegang semua bahan buat WebGIS yang "beneran": titik, garis, poligon, buffer, dan
nearest-neighbour. Topik berikutnya: GeoPandas dan PostGIS.
