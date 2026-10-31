# Sumber data & catatan metodologi

Dikompilasi 31 Oktober 2026 dari sumber publik. Tiap baris CSV punya kolom `sumber` dan (untuk data spasial)
`url_sumber`. Tidak ada informasi di sini yang tidak bisa ditemukan lewat pencarian internet biasa.

## Prinsip

1. **Hanya data publik.** Wikipedia (ID/EN), situs resmi (TNI, Kemhan, RAAF, US Navy), media arus utama, laporan
   think tank (CSIS Asia Maritime Transparency Initiative, SIPRI, IISS Military Balance).
2. **Koordinat = perkiraan lokasi umum.** Cukup untuk peta skala nasional/kawasan; bukan alamat persis dan bukan
   data operasional. Untuk markas yang menempati kota, dipakai koordinat kota atau bandara/pelabuhan terkait.
3. **Label netral.** Pangkalan negara lain diberi label "pangkalan asing di kawasan". Sebagian besar milik negara mitra.
4. **Kolom `keyakinan`** (pada data anggaran): `sedang` = pembulatan dari sumber resmi/sekunder yang konsisten;
   `rendah` = estimasi atau angka usulan yang belum terealisasi.

## Per file

### markas_tni.csv (65 baris)
- Daftar Kodam, Lantamal, Lanud, Koarmada, Kogabwilhan mengikuti halaman Wikipedia Indonesia masing-masing
  (per Oktober 2026). TNI sedang reorganisasi (pembentukan Kodam/Koarmada baru); daftar ini bisa tertinggal.
- Lanud dibatasi pada pangkalan tipe A/B yang paling dikenal (27 dari 60-an Lanud).
- Lanal Ranai dimasukkan walau bukan Lantamal karena perannya di Natuna.

### pulau_terluar_perbatasan.csv (24 baris)
- Pulau terluar dipilih dari daftar 111 pulau kecil terluar (Keppres 6/2017) yang paling sering disebut dalam
  konteks perbatasan; bukan daftar lengkap.
- PLBN mengikuti daftar Pos Lintas Batas Negara di Wikipedia.
- "Wilayah rawan" (Laut Natuna Utara, Ambalat, Selat Malaka) adalah titik tengah ilustratif, bukan batas wilayah.

### alki.csv (18 baris)
- ALKI I/II/III digambar sebagai garis tengah ilustratif dari 6 titik tiap alur. Koordinat resmi ada di
  PP No. 37 Tahun 2002. Jangan dipakai untuk navigasi.

### pangkalan_asing.csv (37 baris)
- Australia: Wikipedia tiap pangkalan RAAF/RAN; rotasi Marinir AS dan rencana B-52 dari liputan ABC/Reuters.
- AS: Andersen AFB, Naval Base Guam, Diego Garcia (Wikipedia). Sembawang & akses Changi (Wikipedia, US Navy).
- China: Fiery Cross, Subi, Mischief, Woody Island dari CSIS AMTI (amti.csis.org); Yulin dan Ream dari Wikipedia.
- Filipina/EDCA: daftar lokasi EDCA dari Wikipedia "Enhanced Defense Cooperation Agreement".
- India: INS Baaz, Andaman & Nicobar Command (Wikipedia). Malaysia, Singapura, Vietnam, Brunei, Thailand, PNG: Wikipedia.
- Status "aktif / dibangun / siaga (bare base)" mengikuti deskripsi sumber; bisa berubah.

### anggaran_indonesia.csv (12 baris)
- Pagu awal APBN Kementerian Pertahanan, dibulatkan dari Nota Keuangan dan liputan media (Kompas, CNBC Indonesia,
  Katadata). Bukan realisasi. Persen PDB adalah perkiraan kasar (pagu ÷ PDB nominal).
- 2026 = angka RAPBN yang diberitakan Agustus 2025; ditandai `rendah` karena belum terealisasi dan lonjakannya besar.

### anggaran_kawasan.csv (10 baris)
- SIPRI Military Expenditure Database (rilis April 2025, data 2024), dibulatkan. Vietnam dan Myanmar adalah estimasi
  SIPRI dengan ketidakpastian tinggi. Personel aktif dari IISS Military Balance / Wikipedia (ribuan, pembulatan).

### alutsista.csv (13 baris)
- Wikipedia "Daftar alutsista TNI AD/AL/AU" dan liputan media untuk pesanan (Rafale, Scorpene, Arrowhead 140).
  Jumlah bisa berbeda dengan data resmi; dipakai untuk gambaran, bukan inventaris.

## Yang sengaja TIDAK dilakukan
- Tidak memasukkan lokasi satuan tempur/gudang/radar yang tidak tercantum di sumber publik tingkat Wikipedia.
- Tidak membuat skor "ancaman" otomatis; penilaian ada di README sebagai pendapat pribadi.
- Tidak mengklaim jangkauan senjata; lingkaran radius hanya jarak geometris.
