# LOG PROMPT & DOKUMENTASI ITERASI AI (PTM-06)
**Mata Kuliah:** Pengembangan Aplikasi Mobile & Web Berbasis AI (IMWAD)  
**Topik:** Implementasi Backend API, Autentikasi JWT, & Keamanan OWASP API Security  
**Proyek:** CassavaCare AI
**Tanggal:** Oktober 2026  
**Versi:** 1.0.0  

---

## 1. Pendahuluan & Ringkasan Aktivitas

Dokumen ini mendokumentasikan seluruh riwayat *prompting*, strategi *chain-of-thought*, iterasi perbaikan bug/error, serta analisis keamanan yang dilakukan selama sesi **Pertemuan 06 (PTM-06)**. 

Tujuan utama dari PTM-06 adalah mentransformasikan spesifikasi desain PTM-05 (`api-contract.md`, `erd.md`, `models.py`, `openapi.yaml`) menjadi implementasi backend API yang modular, aman, dan teruji berdasarkan standar **OWASP API Security Top 10 (2023)**.

### **Artefak yang Dihasilkan pada PTM-06:**
1. **`.env.example`** — Template variabel lingkungan terstandar tanpa kredensial keras (*zero hardcoded secrets*).
2. **`owasp-audit.md`** — Laporan audit keamanan OWASP API Top 10 (2023), patch mitigasi BOLA (API1:2023), dan sanitasi berkas upload AI 5-layer.
3. **`postman-collection.json`** — Koleksi pengujian API Postman v2.1.0 otomatis dengan skrip assertions JavaScript untuk *Happy Path* dan *Error Path*.
4. **`ptm-06-prompt-log.md`** — Laporan log prompt, evaluasi iterasi, dan pelacakan asumsi teknis `[ASUMSI-07]` s.d. `[ASUMSI-10]`.

---

## 2. Catatan Log Prompt Utama & Iterasi AI

### 📄 **Log Prompt 1: Penyusunan Template Variabel Lingkungan (`.env.example`)**
* **Role / Context:** Senior Backend & Security Engineer.
* **Prompt Input:**
  > *"Berdasarkan dokumen PTM-05 (`api-contract.md` & `models.py`), susunlah template `.env.example` untuk backend FastAPI CassavaCare AI. Pastikan mencakup konfigurasi DB PostgreSQL, JWT Secret & Expiry, Limit Size Upload AI (10MB), Confidence Threshold (0.70), Rate Limiting, dan CORS CORS Whitelist. Sediakan penjelasan lengkap untuk setiap variabel."*
* **Hasil AI & Evaluasi:**
  - AI menghasilkan struktur `.env.example` yang rapi dengan pemisahan kategori (*App, DB, JWT, Storage, AI, Rate Limit*).
  - *Evaluasi & Penyesuaian:* Memastikan faktor biaya hashing bcrypt (`BCRYPT_LOG_ROUNDS=12`) dan `CONFIDENCE_THRESHOLD=0.70` dicantumkan sesuai Aturan Bisnis `[BR-01]`.

---

### 🛡️ **Log Prompt 2: Audit Keamanan OWASP API & Patch Mitigation (`owasp-audit.md`)**
* **Role / Context:** Cybersecurity Auditor & Penetration Tester.
* **Prompt Input:**
  > *"Lakukan audit keamanan terhadap rancangan backend CassavaCare AI berdasarkan standar OWASP API Security Top 10 (2023). Fokus pada mitigasi BOLA (API1:2023) pada kueri riwayat prediksi, sanitasi upload gambar AI (API4:2023) 5 layer (size, mime, magic bytes, uuid rename, PIL re-encoding), serta manajemen revocation token JWT (API2:2023). Format hasil audit ke dalam `owasp-audit.md`."*
* **Hasil AI & Evaluasi:**
  - AI menyusun analisis komprehensif 10 kategori OWASP API 2023 beserta kode perbaikan Python/FastAPI.
  - *Iterasi Bug Fix:* AI awalnya menyarankan validasi MIME type hanya berdasarkan header HTTP `Content-Type`. Dilakukan prompt koreksi (*follow-up*) untuk menambahkan pemeriksaan *Magic Bytes* biner asli (`FF D8 FF` / `89 50 4E 47`) guna menghentikan serangan *Content-Type Spoofing*.

---

### 🧪 **Log Prompt 3: Pembuatan Test Suite Postman Collection v2.1.0 (`postman-collection.json`)**
* **Role / Context:** QA Automation Engineer.
* **Prompt Input:**
  > *"Buatlah koleksi Postman v2.1.0 lengkap dalam bentuk `postman-collection.json` untuk menguji seluruh endpoint CassavaCare AI (`/auth`, `/diseases`, `/predictions`). Sertakan otomatisasi skrip test JavaScript untuk menyimpan `accessToken` dan `predictionId` secara dinamis ke environment variables. Sertakan juga test case pengujian keamanan OWASP BOLA dan Upload File berbahaya."*
* **Hasil AI & Evaluasi:**
  - AI membuat skrip generator Python untuk memproduksi file JSON Postman v2.1.0 berstruktur valid.
  - *Iterasi Bug Fix:* Terjadi kesalahan sintaks escaping JSON pada pengujian Postman awal. Diperbaiki dengan mengompilasi struktur JSON secara native menggunakan pustaka `json` Python sebelum ditulis ke file.

---

## 3. Pelacakan Asumsi Teknis `[ASUMSI-XX]` (Lanjutan PTM-05)

Untuk memastikan konsistensi teknis antara PTM-05 dan PTM-06, berikut adalah daftar asumsi lanjutan yang ditetapkan:

| Kode Asumsi | Kategori | Deskripsi Asumsi Teknis | Justifikasi & Dampak Arsitektur |
| :--- | :--- | :--- | :--- |
| **`[ASUMSI-07]`** | Infrastructure | Penggunaan driver `psycopg2-binary` dan `SQLAlchemy 2.0` dengan *connection pooling* (`pool_size=10`, `max_overflow=20`). | Menjamin koneksi DB efisien, efisiensi resource, dan mencegah *connection exhaustion* saat beban puncak. |
| **`[ASUMSI-08]`** | AI Storage | Berkas gambar upload AI disimpan sementara di sistem lokal terisolasi `/storage/uploads/predictions/` dengan sanitasi PIL re-encoding. | Mengisolasi berkas sebelum diunggah ke Cloud Object Storage (AWS S3 / GCP Bucket) pada tahap produksi. |
| **`[ASUMSI-09]`** | Security Auth | Pencabutan sesi JWT (*Refresh Token Revocation*) menggunakan tabel `refresh_tokens` berkolom `is_revoked`. | Memungkinkan fitur *logout* dan pembatalan token secara *real-time* tanpa mengorbankan sifat *stateless* access token. |
| **`[ASUMSI-10]`** | QA Testing | Postman Collection menggunakan skrip JavaScript `pm.environment.set()` untuk mengekstraksi token dan UUID secara dinamis. | Pengujian API dapat dijalankan secara sekuensial (CI/CD friendly) tanpa perlu mengisi token secara manual. |

---

## 4. Matriks Evaluasi Keamanan OWASP API Top 10 (2023)

| Kode OWASP | Kerentanan | Status Sebelum Audit | Mitigasi & Patch Terimplementasi (PTM-06) |
| :--- | :--- | :--- | :--- |
| **API1:2023** | Broken Object Level Auth (BOLA) | Potensial (Akses riwayat via integer ID) | **PATCHED**: Menggunakan UUID v4 & klausa wajib `WHERE user_id = :current_user_id` pada kueri DB. |
| **API2:2023** | Broken Authentication | Token JWT tidak dapat dicabut sebelum *expired* | **PATCHED**: Implementasi *Refresh Token Revocation* via DB & hashing password `bcrypt` (cost 12). |
| **API3:2023** | Broken Object Property Level Authorization | Klien dapat mengirim field terlarang | **PATCHED**: Skema DTO Pydantic v2 dengan `extra="forbid"` menolak field yang tidak didefinisikan. |
| **API4:2023** | Unrestricted Resource Consumption | Risiko *DDoS* via upload berkas raksasa & bom AI | **PATCHED**: Batas ukuran file 10MB, Rate Limiting (60 req/min), & sanitasi gambar 5 layer. |
| **API5:2023** | Broken Function Level Authorization (BFLA) | Pengguna biasa bisa mengubah katalog penyakit | **PATCHED**: Middleware RBAC membatasi endpoint `POST /diseases` khusus untuk peran `ADMIN`. |
| **API8:2023** | Security Misconfiguration | Header HTTP standar tidak dikonfigurasi | **PATCHED**: Pengaturan CORS ketat & penambahan Security Headers (`nosniff`, `DENY`, `HSTS`). |

---

## 5. Refleksi & Pembelajaran (*Lesson Learned*)

1. **Efektivitas Co-Pilot AI dalam Audit Keamanan:**  
   Penggunaan AI sebagai co-pilot sangat membantu dalam menyimulasikan skenario serangan (*penetration testing*) seperti pemalsuan header file dan eksploitasi BOLA, sehingga kerentanan dapat dideteksi sebelum kode masuk ke tahap produksi.
2. **Pentingnya Otomatisasi Test Suite (Postman Collection):**  
   Pengujian API menggunakan variabel lingkungan dinamis di Postman memastikan bahwa seluruh pengandalan alur (*token chaining*) dari Login -> Upload AI -> Cek Riwayat berjalan secara konsisten tanpa kesalahan kofigurasi manual.
3. **Penerapan Prinsip Defense-in-Depth:**  
   Validasi input tidak boleh hanya mengandalkan satu lapisan (seperti ekstensi file), melainkan harus menerapkan *defense-in-depth* (MIME, Magic Bytes, PIL re-encoding, dan rename UUID).

---
*Dokumen ini merupakan artefak resmi penutup untuk Pertemuan 06 (PTM-06) CassavaCare AI.*
