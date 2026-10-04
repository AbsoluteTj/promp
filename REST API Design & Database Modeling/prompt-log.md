# 📝 Log Prompt & Catatan Iterasi AI — PTM-05 (Backend API & Database Design)

**Nama Mata Kuliah:** Pengembangan Aplikasi Mobile & Web Cerdas (IMWAD)  
**Pertemuan:** PTM-05 — Desain REST API & Pemodelan Database  
**Proyek:** CassavaCare AI (Sistem Diagnosis Penyakit Daun Singkong)  
**Tanggal:** 3 Oktober 2026  

---

## 📌 1. Pendahuluan & Strategi Prompting

Dokumen ini mencatat seluruh rangkaian interaksi, perintah (*prompt*), iterasi perbaikan, serta catatan asumsi teknis (`[ASUMSI-XX]`) dalam penyusunan artefak teknis **PTM-05** untuk backend **CassavaCare AI**. 

### **Peran AI (System Persona):**
* **Role:** Senior Backend Architect, Database Engineer, & OWASP Security Specialist.
* **Metode Prompting:** *Structured Chain-of-Thought Prompting*, *Step-by-Step Task Execution*, dan *Test-Driven Schema Validation*.

---

## 🗂️ 2. Log PromptBertahap per Dokumen

### 📄 Tahap 1: `api-contract.md` (Spesifikasi Kontrak REST API)
* **Tujuan:** Membuat dokumen spesifikasi REST API yang menetapkan endpoint, DTO request/response, kriteria sukses/gagal, dan integrasi fitur AI.
* **Prompt Utama:**
  > *"Berdasarkan SRS dan PRD CassavaCare AI, buatkan dokumen `api-contract.md` yang mencakup resource Auth, Predictions (AI), dan Diseases. Cantumkan penanganan ambang batas kepastian AI (confidence score < 0.70) dan standar OWASP API Security."*
* **Iterasi & Perbaikan AI:**
  * **Umpan Balik:** Menambahkan traceability ke Requirement ID (`FR-01` s.d. `FR-04`).
  * **Perbaikan:** Menambahkan penanda khusus `[★ AI]` pada endpoint inferensi (`POST /predictions`) dan skema `fallback_warning` untuk memenuhi Aturan Bisnis `BR-01`.

---

### 🗂️ Tahap 2: `erd.md` (Diagram ERD & Pemodelan Data)
* **Tujuan:** Merancang skema relasional terstruktur (3NF) dalam bentuk Mermaid ERD, Kamus Data, dan DDL SQL PostgreSQL.
* **Prompt Utama:**
  > *"Buatkan dokumen `erd.md` berisi diagram Mermaid ERD, Kamus Data, DDL SQL PostgreSQL, dan matriks traceability. Gunakan UUID v4 untuk Primary Key, buat komposit indeks pada riwayat prediksi, dan pastikan sesuai dengan `api-contract.md`."*
* **Iterasi & Perbaikan AI:**
  * **Umpan Balik:** Sintaks Mermaid harus tervalidasi tanpa karakter ilegal dan klausa DDL harus mendukung constraint `CHECK` enum.
  * **Perbaikan:** Penyesuaian sintaks diagram Mermaid ERD dan pembuatan tipe ENUM PostgreSQL (`user_role_enum`, `prediction_status_enum`, `disease_code_enum`).

---

### 🐍 Tahap 3: `models.py` (Model SQLAlchemy 2.0 & Skema Pydantic v2)
* **Tujuan:** Menyediakan kode sumber Python yang menggabungkan ORM SQLAlchemy dan DTO Pydantic v2.
* **Prompt Utama:**
  > *"Terjemahkan `erd.md` dan `api-contract.md` ke dalam `models.py` menggunakan SQLAlchemy 2.0 ORM dan Pydantic v2 schemas. Sertakan validasi input yang ketat."*
* **Iterasi & Perbaikan AI:**
  * **Pesan Error Runtime:** `ImportError: email-validator is not installed`.
  * **Perbaikan AI:** AI mendeteksi ketiadaan dependensi `email-validator` di lingkungan sandbox dan mengubah tipe `EmailStr` menjadi `str` dengan validasi Regular Expression `Field(pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")`.
  * **Konflik Kata Kunci:** Mengubah nama atribut ORM `metadata` menjadi `metadata_json` untuk menghindari bentrokan dengan atribut privat `DeclarativeBase.metadata` pada SQLAlchemy.

---

### ⚙️ Tahap 4: `openapi.yaml` (Spesifikasi OpenAPI 3.0.3)
* **Tujuan:** Menyediakan spesifikasi OpenAPI 3.0 yang valid untuk diimpor ke Swagger UI / Postman Collection.
* **Prompt Utama:**
  > *"Susun `openapi.yaml` yang konsisten secara presisi dengan `api-contract.md` dan `models.py`. Pastikan menyertakan komponen security HTTP Bearer JWT."*
* **Iterasi & Perbaikan AI:**
  * **Pesan Error Runtime:** `yaml.scanner.ScannerError: mapping values are not allowed here`.
  * **Perbaikan AI:** Memperbaiki kesalahan indentasi YAML pada deskripsi contoh string JSON multilini dan memvalidasi sintaks menggunakan parser `pyyaml`.

---

## 📋 3. Daftar Catatan Asumsi Teknis `[ASUMSI-XX]`

Dalam proses penerjemahan dari dokumen tingkat tinggi (PRD/SRS) ke desain teknik backend PTM-05, ditetapkan beberapa asumsi teknis berikut:

| Kode Asumsi | Area / Topik | Deskripsi Asumsi Teknis |
| :--- | :--- | :--- |
| **`[ASUMSI-01]`** | Authentication | Menggunakan mekanisme **Stateless JWT** (*Access Token* berlaku 15 menit, *Refresh Token* berlaku 7 hari dan disimpan di database dalam bentuk hash SHA-256 untuk mendukung pencabutan sesi). |
| **`[ASUMSI-02]`** | Authorization (RBAC) | Terdapat 3 tingkatan peran pengguna: `FARMER` (akses standar), `EXPERT` (dapat menambah/memperbarui katalog penyakit), dan `ADMIN` (akses penuh manajemen pengguna & sistem). |
| **`[ASUMSI-03]`** | AI Confidence Threshold | Kriteria kepastian hasil diagnosa AI ditetapkan pada ambang batas **70% (0.70)**. Skor $\ge 0.70$ berstatus `CONFIDENT`, sedangkan $< 0.70$ berstatus `LOW_CONFIDENCE` dan memicu objek `fallback_warning`. |
| **`[ASUMSI-04]`** | Relasi Diagnosa & Penyakit | Kolom `disease_id` pada tabel `predictions` bersifat opsional (`NULLABLE`). Jika diagnosa berstatus `LOW_CONFIDENCE` atau `FAILED`, `disease_id` diisi `NULL` agar tidak menyesatkan pengguna. |
| **`[ASUMSI-05]`** | Storage Gambar Diagnosa | Gambar daun singkong dikirimkan via endpoint `multipart/form-data`, disimpan pada Object Storage (S3/GCS), dan database PostgreSQL hanya menyimpan string URL HTTPS yang valid (`image_url`). |
| **`[ASUMSI-06]`** | SQLAlchemy Model Mapping | Kolom `metadata` pada tabel `predictions` dipetakan ke atribut `metadata_json` di SQLAlchemy ORM guna mencegah konflik kata kunci terdistribusi (*reserved attribute*) milik `DeclarativeBase`. |

---

## 🎯 4. Evaluasi Refleksi & Penjaminan Kualitas

1. **Konsistensi Lintas Dokumen (Traceability):**
   * Seluruh entitas dan endpoint dalam `api-contract.md`, `erd.md`, `models.py`, dan `openapi.yaml` telah terhubung 100% tanpa adanya perbedaan tipe data atau penamaan variabel.
2. **Kepatuhan OWASP API Security:**
   * Penggunaan **UUID v4** mencegah *Broken Object Level Authorization* (BOLA).
   * Validasi DTO Pydantic mencegah *Mass Assignment* dan *Injection Attack*.
   * Penggunaan token JWT ter-hash mencegah kebocoran sesi.
3. **Validasi Eksekusi Kode:**
   * Seluruh skema Python di `models.py` dan struktur YAML di `openapi.yaml` telah diuji dan lolos verifikasi sintaks di lingkungan eksekusi sandbox.
