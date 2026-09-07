# Software Requirements Specification (SRS): CassavaCare AI

## 1. Tujuan, Scope, dan Definisi Istilah
*   **Tujuan:** Mendokumentasikan spesifikasi kebutuhan perangkat lunak (fungsional dan non-fungsional) untuk pengembangan aplikasi CassavaCare AI.
*   **Scope:** Pengembangan aplikasi Android berbasis Kotlin yang menggunakan TensorFlow Lite untuk klasifikasi citra penyakit daun singkong secara lokal (*offline*).
*   **Definisi Istilah:**
    *   **FR:** *Functional Requirement* (Kebutuhan Fungsional).
    *   **NFR:** *Non-Functional Requirement* (Kebutuhan Non-Fungsional).
    *   **On-device AI:** Pemrosesan kecerdasan buatan yang berjalan langsung di memori perangkat pintar tanpa mengirim data ke server.

## 2. User & Stakeholder, Lingkungan Operasi, Asumsi & Dependensi
*   **User Utama:** Petani Singkong (membutuhkan antarmuka ringkas).
*   **Lingkungan Operasi:** Perangkat seluler dengan sistem operasi minimal Android 8.0 (Oreo) dan RAM minimum 2GB. Aplikasi berjalan di area tanpa jaringan internet (*blank spot*).
*   **Asumsi & Dependensi:** Kualitas hasil deteksi sangat bergantung pada kondisi pencahayaan dan resolusi kamera perangkat pengguna (*smartphone camera dependency*).

## 3. Kebutuhan Fungsional (FR)
| ID | Deskripsi (Sistem harus dapat...) | Prioritas MoSCoW | Metode Verifikasi |
| :--- | :--- | :--- | :--- |
| **FR-01** | Mengklasifikasikan foto daun saat pengguna menekan tombol "Pindai" -> menampilkan hasil jenis penyakit. | Must Have | Pengujian Sistematis (Uji 100 citra tes) |
| **FR-02** | Menampilkan persentase keyakinan (Confidence Score) saat hasil deteksi muncul -> menampilkan angka probabilitas. | Must Have | Inspeksi UI/UX |
| **FR-03** | Menampilkan panduan penanganan saat penyakit teridentifikasi -> memunculkan teks rekomendasi tindakan. | Must Have | Pengujian Fungsional |
| **FR-04** | Menyimpan riwayat gambar dan diagnosis saat pemindaian selesai -> data tersimpan di basis data lokal ponsel. | Should Have | Inspeksi Database Lokal (Room/SQLite) |

## 4. Kebutuhan Non-Fungsional (NFR)
| ID | Kategori (ISO/IEC 25010) | Target & Kondisi Ukur |
| :--- | :--- | :--- |
| **NFR-01** | *Functional Suitability* (Akurasi AI) | Akurasi klasifikasi minimal 90% saat diuji menggunakan *confusion matrix* pada set data lapangan. |
| **NFR-02** | *Performance Efficiency* (Latensi AI) | Waktu inferensi (pemrosesan gambar hingga hasil keluar) di bawah 3 detik per gambar pada perangkat dengan RAM 2GB. |
| **NFR-03** | *Portability* (Ukuran Aplikasi) | Ukuran akhir instalasi aplikasi (*APK size*) maksimal 50MB. |
| **NFR-04** | *Usability* | Petani dapat menyelesaikan satu alur pemindaian foto tanpa bantuan eksternal dalam waktu kurang dari 2 menit. |
| **NFR-05** | *Reliability* (Keamanan/Fallback) | Sistem menampilkan pesan *error* (tidak *crash*) saat pengguna menolak izin akses kamera. |

## 5. Kebutuhan Data Minimum Fitur AI
*   **Input:** Citra digital daun singkong (format matriks RGB), yang akan diubah ukurannya (*resize*) secara otomatis oleh sistem menjadi 224x224 piksel sebelum masuk ke model AI.
*   **Output Model:** Array probabilitas (skor 0-1) yang memetakan ke 5 kelas (Daun Sehat, CMD, CBB, CGM, CBSD).

## 6. Aturan Bisnis Hasil Riset
*   **BR-01:** Aplikasi hanya akan memberikan rekomendasi penanganan apabila tingkat keyakinan (*confidence score*) model AI terhadap suatu penyakit berada di atas ambang batas 70%. Jika di bawah 70%, aplikasi akan meminta pengguna mengambil ulang foto.

## 7. Matriks Traceability
| Fitur PRD (Sumber) | FR Terkait | NFR Terkait |
| :--- | :--- | :--- |
| Pemindaian foto daun secara lokal (*offline*) | FR-01 | NFR-01, NFR-02 |
| Menampilkan tingkat persentase keyakinan | FR-02 | NFR-01 |
| Panduan penanganan penyakit berbasis teks | FR-03 | NFR-04 |
| Menyimpan riwayat pindaian lokal | FR-04 | NFR-03 |