# Product Requirements Document (PRD): CassavaCare AI

## 1. Ringkasan Eksekutif
CassavaCare AI adalah aplikasi seluler Android yang menggunakan model *Computer Vision* (TensorFlow Lite) untuk membantu petani singkong mendeteksi penyakit dan hama daun secara langsung (*on-device*) di ladang tanpa memerlukan koneksi internet.

## 2. Problem Statement & Bukti
*   **Masalah Utama:** Petani singkong mengalami kerugian panen secara massal akibat keterlambatan identifikasi penyakit daun karena minimnya akses ke pakar botani secara cepat di lapangan.
*   **Bukti (Fakta):** Model AI *Computer Vision* terbukti mampu mendeteksi 3 penyakit utama dan 2 jenis hama pada daun singkong langsung dari citra kamera ponsel dengan akurasi 93% (Ramcharan et al., 2017, DOI: 10.3389/fpls.2017.01852).
*   **Asumsi:** [ASUMSI-01] Target pengguna memiliki perangkat Android dengan spesifikasi RAM minimal 2GB dan sistem operasi Android 8.0 ke atas agar model TensorFlow Lite dapat berjalan lancar.

## 3. Target User & Stakeholder
| Peran | Kebutuhan Utama | Pengaruh |
| :--- | :--- | :--- |
| **Petani Singkong (User Utama)** | Diagnosis penyakit secara *offline* dengan antarmuka yang sangat sederhana. | Tinggi |
| **Pakar Pertanian (Stakeholder)** | Data agregat sebaran penyakit musiman (jika fitur sinkronisasi ditambahkan kelak). | Menengah |
| **Pengepul (Stakeholder)** | Kepastian stabilitas kualitas panen singkong dari petani binaan. | Rendah |

## 4. Value Proposition
*   **Pain Relieved:** Menghilangkan ketergantungan pada koneksi internet dan waktu tunggu konsultasi pakar botani secara fisik.
*   **Gain Created:** Memberikan saran penanganan penyakit secara seketika di lokasi ladang.
*   **Justifikasi AI:** Fitur AI bukan *gimmick*; pengenalan pola penyakit mikroskopis atau bercak samar pada daun membutuhkan komputasi klasifikasi citra yang mustahil dilakukan hanya dengan logika pemrograman tradisional (IF/THEN).

## 5. Tujuan Produk & KPI
*   **Tujuan:** Mempercepat proses deteksi penyakit daun di lapangan menjadi di bawah 1 menit per tanaman.
*   **KPI & Cara Ukur 1:** Akurasi klasifikasi AI di lapangan minimal 90% (diukur dari metrik *confusion matrix* selama fase pengujian beta).
*   **KPI & Cara Ukur 2:** Ukuran final aplikasi tidak lebih dari 50MB agar mudah dibagikan (diukur dari *APK build analyzer*).

## 6. Scope Fitur 1 Semester (MoSCoW)
| Fitur | Prioritas MoSCoW | Keterangan |
| :--- | :--- | :--- |
| Pemindaian foto daun secara lokal (*offline*) | Must Have | Fitur AI (*Computer Vision*) |
| Menampilkan tingkat persentase keyakinan (Confidence Score) | Must Have | Fitur AI |
| Panduan penanganan penyakit berbasis teks | Must Have | Non-AI |
| Menyimpan riwayat pindaian di memori lokal ponsel | Should Have | Non-AI |

## 7. Non-Goals Eksplisit
*   Aplikasi ini **tidak** dirancang untuk mendeteksi penyakit pada bagian akar, batang, atau umbi singkong (hanya daun).
*   Aplikasi ini **tidak** menyediakan fitur obrolan langsung (*live chat*) dengan pakar pertanian manusia.

## 8. Asumsi & Risiko Utama + Mitigasi
*   **Risiko:** Petani mengambil foto daun dengan pencahayaan yang terlalu gelap, terlalu terang, atau buram (blur), yang akan menurunkan akurasi deteksi AI secara drastis.
*   **Mitigasi:** Menyediakan antarmuka (UI) panduan berupa kotak pembidik transparan pada layar kamera saat memotret, serta instruksi visual singkat tentang cara mengambil foto yang benar sebelum pemindaian pertama dilakukan.