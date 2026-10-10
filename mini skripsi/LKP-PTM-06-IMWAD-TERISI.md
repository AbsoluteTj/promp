# LEMBAR KERJA PRAKTIKUM (LKP-PTM-06) - TERISI LENGKAP
## Intelligent Mobile and Web Application Development (IMWAD)

---

| **Mata Kuliah** | Intelligent Mobile and Web Application Development |
| :--- | :--- |
| **Kode / SKS** | TIF-IMWAD / 3 SKS |
| **Program Studi** | Teknik Informatika |
| **Pertemuan ke-** | 06 dari 16 |
| **Topik** | Implementasi Backend API, Validasi Masukan, Autentikasi JWT, dan Keamanan OWASP API |
| **CPMK** | CPMK-2 → Sub-CPMK 2.1 & 2.2 (Backend Services, Auth JWT & Keamanan OWASP API) |
| **Dosen Pengampu** | Edwin Hari Agus Prastyo, S.Kom., M.Kom. |
| **Semester / T.A.** | Ganjil 2025/2026 |

---

### ▌ IDENTITAS MAHASISWA & TIM

| **Nama Mahasiswa / Tim** | **NIM** | **Peran / Tanggung Jawab** |
| :--- | :--- | :--- |
| Mahasiswa 1 (Ketiga Anggota Tim) | 220101001 | Backend Lead & OWASP Security Auditor |
| Mahasiswa 2 | 220101002 | Database & API Integration Engineer |
| Mahasiswa 3 | 220101003 | QA & Postman Test Engineer |

---

### E. LEMBAR KERJA ISIAN MAHASISWA

#### E.1 Daftar Endpoint Backend & Status Implementasi Lapisan
Berikut adalah daftar seluruh endpoint backend yang diimplementasikan berdasarkan spesifikasi OpenAPI 3.0 (PTM-05) menggunakan arsitektur modular 3 lapisan (**Router → Service → Repository**):

| No | Resource / Endpoint | HTTP Method | Lapisan Terpasang (Router / Svc / Repo) | Status & Cek OWASP Anti-BOLA |
| :-: | :--- | :-: | :--- | :--- |
| 1 | `/auth/signup` | `POST` | `auth_router.py` → `auth_service.py` → `user_repo.py` | **Lolos** (Hash Bcrypt + Unique Email Constraint) |
| 2 | `/auth/login` | `POST` | `auth_router.py` → `auth_service.py` → `user_repo.py` | **Lolos** (OAuth2 Password Flow + JWT Pair) |
| 3 | `/auth/refresh` | `POST` | `auth_router.py` → `auth_service.py` → `token_repo.py` | **Lolos** (DB Refresh Token Revocation Check) |
| 4 | `/auth/me` | `GET` | `auth_router.py` → `auth_service.py` → `user_repo.py` | **Lolos** (Protected Route `Bearer JWT` Auth) |
| 5 | `/diseases` | `GET` | `disease_router.py` → `disease_service.py` → `disease_repo.py` | **Lolos** (Public Catalog Read-Only) |
| 6 | `/diseases/{disease_id}` | `GET` | `disease_router.py` → `disease_service.py` → `disease_repo.py` | **Lolos** (UUID v4 Validation) |
| 7 | `/predictions` [★ AI] | `POST` | `prediction_router.py` → `prediction_service.py` → `prediction_repo.py` | **Lolos** (Sanitasi File 5 Layer + User Binding) |
| 8 | `/predictions` [★ AI] | `GET` | `prediction_router.py` → `prediction_service.py` → `prediction_repo.py` | **Lolos Anti-BOLA** (`WHERE user_id = current_user.id`) |
| 9 | `/predictions/{prediction_id}` [★ AI] | `GET` | `prediction_router.py` → `prediction_service.py` → `prediction_repo.py` | **Lolos Anti-BOLA** (`prediction.user_id == current_user.id`) |

##### Deskripsi Endpoint Inferensi AI (*) & Mekanisme Validasi/Sanitasi Masukan:
Endpoint `POST /api/v1/predictions` menerima berkas citra daun singkong via `multipart/form-data`. Pipa sanitasi masukan menerapkan 5 lapis pengamanan OWASP API4:2023:
1. **Size Guard:** Membatasi ukuran berkas maksimal 10MB (`413 Payload Too Large`).
2. **MIME Whitelisting:** Mengunci header tipe media hanya untuk `image/jpeg` dan `image/png`.
3. **Magic Bytes Validation:** Memeriksa byte biner awal (`FF D8 FF` / `89 50 4E 47`) untuk mengagalkan pengelabuan ekstensi berkas.
4. **Filename Randomization:** Mengubah nama berkas asli menjadi UUID v4 acak guna mencegah kerentanan *Directory Traversal*.
5. **PIL Re-encoding & AI Thresholding:** Membaca ulang matriks piksel dengan PIL untuk mengikis skrip webshell di metadata EXIF, lalu mengeksekusi model TF-Lite/ONNX. Jika *confidence score* < 0.70, sistem memberikan `fallback_warning` (`[BR-01, AC-02]`).

---

#### E.2 Iterasi & Revisi Prompt AI

| Prompt | Masalah pada Output AI Pertama | Revisi / Prompt Lanjutan yang Digunakan |
| :--- | :--- | :--- |
| **D.1 Scaffold Modular** | Kode Router menaruh logika kueri SQLAlchemy langsung di dalam HTTP handler endpoint tanpa pemisahan Repository. | *"Refaktor arsitektur menjadi 3 layer terpisah ketat: Router hanya mengurus HTTP request/response, Service mengurus logika bisnis, dan Repository mengurus kueri DB via SQLAlchemy session."* |
| **D.2 Autentikasi JWT** | Modul `Pydantic` gagal *import* akibat dependensi `email-validator` yang belum terpasang saat mendeklarasikan `EmailStr`. | *"Ganti `EmailStr` dengan tipe `str` terannotasi `Field(pattern=r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')` untuk validasi regex native tanpa dependensi eksternal."* |
| **D.3 Audit OWASP & BOLA** | Endpoint `GET /predictions/{prediction_id}` masih mengembalikan data diagnosa hanya berdasarkan `prediction_id` tanpa memverifikasi pemilik token. | *"Tambahkan klausa filter kepemilikan objek pada repository kueri: `WHERE predictions.id = :prediction_id AND predictions.user_id = :current_user.id`. Jika tidak cocok, lempar `HTTPException(status_code=404, detail='Data tidak ditemukan')`."* |

---

#### E.3 Asumsi Teknis & Keputusan Desain Backend `[ASUMSI-XX]`

| Kode Asumsi | Isi Asumsi / Keputusan Desain AI | Verifikasi Tim (Diterapkan / Diubah / Ditolak) |
| :--- | :--- | :--- |
| **`[ASUMSI-07]`** | Pemisahan arsitektur backend menggunakan kerangka kerja FastAPI dengan pola modular *Router-Service-Repository* untuk kemudahan pengujian dan pemeliharaan. | **Diterapkan.** Pola ini memisahkan kueri basis data dan logika bisnis dari HTTP router. |
| **`[ASUMSI-08]`** | Token Refresh disimpan dalam tabel basis data (`refresh_tokens`) untuk mendukung fitur pencabutan sesi secara langsung (*instant revocation*). | **Diterapkan.** Meningkatkan keamanan dari kebocoran token jangka panjang. |
| **`[ASUMSI-09]`** | Kegagalan otorisasi kepemilikan objek (BOLA) direspons dengan status `HTTP 404 Not Found` alih-alih `403 Forbidden`. | **Diterapkan.** Mencegah *resource enumeration attack* (OWASP API3:2023). |
| **`[ASUMSI-10]`** | Model AI inferensi diakomodasi via *mock inference engine* berlatar TensorFlow Lite/ONNX yang menghasilkan probabilitas 5 kelas penyakit daun singkong secara deterministik. | **Diterapkan.** Menjamin fungsionalitas inferensi backend tetap dapat diuji 100% tanpa beban komputasi GPU berat. |

---

### F. LOG PROMPT WAJIB (ptm-06-prompt-log)

| No | Target Prompt | Alat AI & Versi | Ringkasan Prompt | Kualitas Output (1-5) | Revisi Manual |
| :-: | :--- | :--- | :--- | :-: | :--- |
| 1 | D.1 Scaffold Modular | Gemini Notebook | Generate struktur folder modular Router-Service-Repository & `.env.example`. | 4/5 | Memisahkan file `config.py` dan `database.py` ke direktori `app/core/`. |
| 2 | D.2 Autentikasi JWT | Gemini Notebook | Implementasi alur signup, login bcrypt, token pair (access 30m / refresh 7d), & `/auth/me`. | 5/5 | Penyesuaian regex email pada Pydantic v2 untuk menghindari *ImportError*. |
| 3 | D.3 Audit OWASP & BOLA | Gemini Notebook | Audit OWASP API Top 10 (2023), patch Anti-BOLA pada `/predictions/{id}`, dan sanitasi upload. | 5/5 | Menambahkan validasi magic bytes biner pada pipa sanitasi unggahan gambar. |
| 4 | Iterasi Postman Export | Gemini Notebook | Buat spesifikasi Postman Collection v2.1.0 lengkap dengan skrip pengujian otomatis. | 5/5 | Menambahkan variabel otomatis `pm.environment.set` pada skrip tes Postman. |

---

### G. DELIVERABLE ARTEFAK REPOSITORI

| File / Artefak | Lokasi di Repositori | Keterangan Status |
| :--- | :--- | :--- |
| **Source Code Backend** | `backend/app/` (`models.py`, `routers/`, `services/`, `repositories/`, `core/`) | **Selesai & Tervalidasi** (Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2) |
| **.env.example** | `.env.example` | **Selesai** (Template variabel lingkungan aman tanpa hardcoded secrets) |
| **postman-collection.json** | `docs/postman/postman-collection.json` | **Selesai** (Koleksi uji Postman v2.1.0 dengan Happy/Error Path & BOLA test) |
| **owasp-audit.md** | `docs/security/owasp-audit.md` | **Selesai** (Laporan audit OWASP API Security Top 10 2023 & patch Anti-BOLA) |
| **ptm-06-prompt-log.md** | `docs/prompt-log/ptm-06-prompt-log.md` | **Selesai** (Log prompt, iterasi AI, evaluasi, & verifikasi asumsi teknis) |
| **LKP-PTM-06 (Lembar ini)** | `docs/lkp/LKP-PTM-06-IMWAD-TERISI.md` | **Terisi Lengkap** |

**Pesan Commit Wajib Git:**  
`feat(backend): implement JWT auth, CRUD endpoints, OWASP patches [PTM-06]`

---

### H. DEKLARASI INTEGRITAS AKADEMIK & AI

Dengan mengumpulkan tugas ini, seluruh anggota tim menyatakan bahwa:  
*"Kami memahami seluruh isi tugas ini, mengerjakan secara mandiri sesuai panduan, dan menggunakan AI sebagai alat bantu yang dideklarasikan secara jujur dalam `ptm-06-prompt-log.md`."*

| Nama Lengkap & NIM | Tanda Tangan | Tanggal |
| :--- | :--- | :--- |
| 1. Mahasiswa 1 (NIM 220101001) | *[Tandatangan Digital]* | 09 Oktober 2026 |
| 2. Mahasiswa 2 (NIM 220101002) | *[Tandatangan Digital]* | 09 Oktober 2026 |
| 3. Mahasiswa 3 (NIM 220101003) | *[Tandatangan Digital]* | 09 Oktober 2026 |
