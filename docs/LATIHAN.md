# 🏋️ Latihan

Diurutkan dari yang mudah ke yang lebih menantang. Setiap latihan dilengkapi petunjuk dan kunci jawaban yang dapat
dibuka. Usahakan mencoba minimal 10 menit sebelum membuka kunci. Setelah setiap latihan, jalankan
`python -m pytest tests/` dan `streamlit run app.py`.

---

### Latihan 1 — Menambah satu pulau terluar (cukup edit CSV) ⭐

Tambahkan **Pulau Sophialouisa** (NTB, titik paling selatan Lombok) ke `data/pulau_terluar_perbatasan.csv`:
jenis `pulau_terluar`, provinsi `Nusa Tenggara Barat`, lat `-8.9100`, lon `116.0000`, berbatasan dengan
`Australia`, sumber `Wikipedia: Pulau Sophialouisa`, url `https://id.wikipedia.org/wiki/Pulau_Sophialouisa`.

Kemudian buka dashboard dan temukan segitiganya di selatan Lombok.

<details><summary>Petunjuk</summary>
Salin baris terakhir, ganti `id` menjadi 25 beserta nilainya. Kolom yang mengandung koma harus dibungkus tanda kutip.
</details>

<details><summary>Kunci</summary>

```
25,Pulau Sophialouisa,pulau_terluar,Nusa Tenggara Barat,-8.9100,116.0000,Australia,Titik paling selatan Lombok,Wikipedia: Pulau Sophialouisa,https://id.wikipedia.org/wiki/Pulau_Sophialouisa
```
Jika `test_dataset_bisa_dimuat_dan_valid` tetap hijau, koordinatnya valid. Angka KPI "Pulau terluar & pos batas"
naik menjadi 25.
</details>

---

### Latihan 2 — Radius baru 750 km ⭐

Di sidebar, pilihan radius hanya 250/500/1000/1500. Tambahkan **750**.

<details><summary>Petunjuk</summary>
Cari `st.multiselect("Radius lingkaran (km)"` di `app.py`. Daftarnya ada pada argumen kedua.
</details>

<details><summary>Kunci</summary>

```python
radius_km = st.multiselect("Radius lingkaran (km)", [250, 500, 750, 1000, 1500], default=[500, 1000])
```
Perhatikan bahwa `src/peta.py` tidak perlu diubah sama sekali karena ia menerima daftar apa pun. Itulah manfaat
memisahkan tampilan dari logika.
</details>

---

### Latihan 3 — Jarak Jakarta ke seluruh Kodam ⭐⭐

Tanpa Streamlit, di `python`, buat tabel jarak dari Mabes TNI Cilangkap ke setiap Kodam, diurutkan dari yang terdekat.

<details><summary>Petunjuk</summary>
Gunakan `geo.jarak_ke_semua(lat, lon, df)` lalu simpan hasilnya ke kolom baru. Filter `jenis == "Kodam"` terlebih dahulu.
</details>

<details><summary>Kunci</summary>

```python
from src import geo, muat_data
df = muat_data.muat_markas_tni()
kodam = df[df["jenis"] == "Kodam"].copy()
kodam["jarak_km"] = geo.jarak_ke_semua(-6.3362, 106.8998, kodam).round()
print(kodam.sort_values("jarak_km")[["nama", "kota", "jarak_km"]])
```
Kodam Jaya 15 km, Kodam III/Siliwangi ±120 km, ... Kodam XVII/Cenderawasih ±3.800 km.
</details>

---

### Latihan 4 — Jumlah pangkalan asing dalam radius dari setiap markas TNI ⭐⭐

Kebalikan dari tab Analisis Jarak: untuk **setiap markas TNI**, berapa pangkalan asing yang berada dalam 1.000 km?
Tampilkan 10 teratas.

<details><summary>Petunjuk</summary>
Panggil `geo.jumlah_dalam_radius(lat, lon, df_asing, 1000)` per baris TNI dengan `df.apply(..., axis=1)`.
</details>

<details><summary>Kunci</summary>

```python
from src import geo, muat_data
tni = muat_data.muat_markas_tni()
asing = muat_data.muat_pangkalan_asing()
tni["asing_1000km"] = tni.apply(lambda b: geo.jumlah_dalam_radius(b["lat"], b["lon"], asing, 1000), axis=1)
print(tni.sort_values("asing_1000km", ascending=False)[["nama", "matra", "asing_1000km"]].head(10))
```
Markas di Kepulauan Riau dan Sumatera Utara berada di puncak: Selat Malaka memang padat.
Bonus: tambahkan hasil ini sebagai grafik batang baru di tab Analisis Jarak.
</details>

---

### Latihan 5 — Ukuran marker mengikuti jenis markas ⭐⭐

Di `src/peta.py`, markas TNI digambar dengan radius 6 atau 8 piksel. Ubah agar **Kodam dan Koarmada** 10 piksel,
**Kogabwilhan dan Mabes** 12 piksel, dan sisanya 6.

<details><summary>Petunjuk</summary>
Buat kamus `UKURAN_JENIS = {"Kodam": 10, ...}` lalu gunakan `radius=UKURAN_JENIS.get(b["jenis"], 6)`.
</details>

<details><summary>Kunci</summary>

```python
UKURAN_JENIS = {"Kodam": 10, "Koarmada": 10, "Kogabwilhan": 12, "Markas Besar": 12}
...
radius=UKURAN_JENIS.get(b["jenis"], 6),
```
Kamus + `.get(kunci, default)` adalah pola yang jauh lebih rapi daripada rangkaian if-elif yang panjang.
</details>

---

### Latihan 6 — Klik titik di peta → tampilkan detail ⭐⭐⭐

Saat ini klik di peta tidak melakukan apa pun (`returned_objects=[]`). Ubah agar ketika pengguna mengklik marker,
nama objek yang diklik muncul di bawah peta.

<details><summary>Petunjuk</summary>
`st_folium` mengembalikan dict. Minta `returned_objects=["last_object_clicked_tooltip"]`, lalu tampilkan dengan
`st.write`. Perlu diingat: setiap klik kini memicu rerun.
</details>

<details><summary>Kunci</summary>

```python
hasil = st_folium(peta, height=600, use_container_width=True, returned_objects=["last_object_clicked_tooltip"])
if hasil and hasil.get("last_object_clicked_tooltip"):
    st.success(f"Objek yang diklik: {hasil['last_object_clicked_tooltip']}")
```
Peta akan terasa sedikit lebih lambat karena rerun. Itulah kompromi antara interaktivitas dan performa.
</details>

---

### Latihan 7 — Garis ZEE dengan GeoJSON ⭐⭐⭐

Unduh GeoJSON batas ZEE Indonesia dari Marine Regions (marineregions.org, cari "Indonesia EEZ"), simpan sebagai
`data/zee_indonesia.geojson`, dan tambahkan sebagai lapisan di `peta.py` dengan `folium.GeoJson(...)`.

<details><summary>Petunjuk</summary>

```python
import json
with open("data/zee_indonesia.geojson") as f:
    zee = json.load(f)
folium.GeoJson(zee, name="ZEE Indonesia", style_function=lambda x: {"color": "#b23a3a", "weight": 1.5, "fillOpacity": 0.03}).add_to(m)
```
GeoJSON memakai urutan **[lon, lat]**, tetapi `folium.GeoJson` sudah menanganinya. File ZEE dapat berukuran beberapa
MB; jika lambat, sederhanakan terlebih dahulu dengan GeoPandas: `gdf.simplify(0.05)`.
</details>

Setelah menyelesaikan latihan ini, Anda sudah memegang seluruh bahan untuk WebGIS yang lengkap: titik, garis,
poligon, buffer, dan nearest-neighbour. Topik berikutnya: GeoPandas dan PostGIS.
