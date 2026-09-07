# Use Case & Acceptance Criteria: CassavaCare AI

## Use Case 1: Memindai dan Mendeteksi Penyakit Daun
* **ID Use Case:** UC-01
* **Aktor Utama:** Petani Singkong
* **Pre- kondisi:** Pengguna membuka aplikasi di area ladang dan berada di menu utama kamera.
* **Post-kondisi:** Sistem menampilkan nama penyakit, tingkat *confidence score*, dan panduan penanganan.

### Skenario Utama (Happy Flow):
1. Pengguna membuka fitur kamera pemindai di aplikasi.
2. Pengguna mengarahkan kotak pembidik ke daun singkong yang bergejala.
3. Pengguna menekan tombol "Pindai".
4. Sistem menjalankan model *TensorFlow Lite* secara lokal untuk mengklasifikasikan citra.
5. Sistem menampilkan hasil deteksi berupa jenis penyakit, skor probabilitas, dan teks panduan penanganan.

---

## Acceptance Criteria (Kriteria Penerimaan)

### Skenario AC-01: Pemindaian Berhasil dengan Akurasi Tinggi
* **Given** aplikasi terbuka di perangkat Android dengan model AI aktif,
* **When** pengguna mengambil foto daun singkong yang memiliki gejala penyakit *Cassava Mosaic Disease* (CMD) dengan pencahayaan yang cukup dan menekan tombol "Pindai",
* **Then** sistem harus memproses gambar dalam waktu kurang dari 3 detik dan menampilkan label "CMD" beserta *confidence score* $\ge 70\%$.

### Skenario AC-02: Peringatan Ambang Batas Rendah (Fallback)
* **Given** pengguna memotret daun dalam kondisi buram (*blur*) atau pencahayaan gelap,
* **When** model AI menghasilkan skor probabilitas di bawah 70% (< 0.70),
* **Then** sistem harus menampilkan pesan peringatan: *"Hasil tidak pasti, silakan ambil ulang foto dengan pencahayaan yang lebih baik"* alih-alih menampilkan diagnosis yang salah.