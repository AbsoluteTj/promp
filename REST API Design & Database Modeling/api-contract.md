# Dokumentasi Kontrak REST API — CassavaCare AI

**Sistem:** CassavaCare AI Backend API  
**Versi API:** 1.0.0  
**Base URL:** `http://localhost:8000/api/v1`  
**Stack Backend:** FastAPI (Python 3.10+), Pydantic v2, PostgreSQL / SQLite  
**Dokumen Acuan:** PRD CassavaCare AI, SRS PTM-02, User Stories PTM-03, LLD PTM-04  

---

## 1. Ringkasan & Keputusan Desain API

1. **Arsitektur RESTful:** Penamaan endpoint berbasis kata benda jamak (*plural nouns*), misal: `/users`, `/predictions`, `/diseases`.
2. **Format Data:** Semua pertukaran data menggunakan format JSON (`application/json`), kecuali endpoint upload citra yang menggunakan `multipart/form-data`.
3. **Autentikasi & Otorisasi:** Menggunakan JSON Web Token (JWT) dengan mekanisme *Bearer Token* pada *Header Authorization*: `Authorization: Bearer <access_token>`.
4. **Mekanisme Handling AI & Fallback (BR-01 & AC-02):**
   - Ambang batas keyakinan (*confidence threshold*) ditetapkan sebesar **70% (0.70)**.
   - Jika `confidence_score >= 0.70`: Sistem mengembalikan hasil klasifikasi penyakit beserta persentase keyakinan dan rekomendasi penanganan.
   - Jika `confidence_score < 0.70`: `fallback_triggered` bernilai `true`, dan sistem mengembalikan pesan peringatan perbaikan foto tanpa memaksakan diagnosis salah.
5. **Format Respons Standar:**
   - **Sukses:** Mengembalikan objek JSON berstruktur `{ "status": "success", "data": { ... } }` atau payload resource langsung.
   - **Gagal/Error:** Mengembalikan struktur error konsisten `{ "detail": "Pesan error", "error_code": "KODE_ERROR", "timestamp": "ISO-8601" }`.

---

## 2. Pemetaan Resource & Endpoint (Traceability)

| No | Resource | HTTP Method | Path / Endpoint | Deskripsi & Tag | Requirement Terkait |
|---|---|---|---|---|---|
| 1 | Auth | `POST` | `/auth/signup` | Registrasi akun pengguna baru | FR-04, US-01 |
| 2 | Auth | `POST` | `/auth/login` | Otentikasi & penerbitan token JWT | FR-04, US-01 |
| 3 | Auth | `POST` | `/auth/refresh` | Pembaruan Access Token via Refresh Token | FR-04, Security |
| 4 | Auth | `GET` | `/auth/me` | Mengambil profil pengguna aktif | FR-04, Security |
| 5 | Predictions | `POST` | `/predictions` | **[★ AI]** Unggah foto & inferensi deteksi penyakit daun | FR-01, FR-02, FR-03, BR-01, US-01 |
| 6 | Predictions | `GET` | `/predictions` | Mengambil daftar riwayat pindaian pengguna | FR-04, US-04 |
| 7 | Predictions | `GET` | `/predictions/{id}` | Mengambil detail 1 riwayat pindaian | FR-04, US-04 |
| 8 | Predictions | `DELETE`| `/predictions/{id}` | Menghapus catatan riwayat pindaian | FR-04, US-04 |
| 9 | Diseases | `GET` | `/diseases` | Katalog informasi penyakit & hama daun singkong | FR-03, US-03 |
| 10| Diseases | `GET` | `/diseases/{code}` | Detail penyakit & panduan penanganan lengkap | FR-03, US-03 |

---

## 3. Spesifikasi Detail Endpoint REST API

### 3.1 Resource: Authentication (`/auth`)

#### A. `POST /auth/signup`
- **Deskripsi:** Pendaftaran akun petani/pengguna baru.
- **Request Body (`application/json`):**
  ```json
  {
    "full_name": "Pak Yanto",
    "email": "yanto@petani.id",
    "password": "PasswordAman123!"
  }
  ```
- **Response Sukses (`201 Created`):**
  ```json
  {
    "message": "Registrasi berhasil",
    "user": {
      "id": "usr_9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "full_name": "Pak Yanto",
      "email": "yanto@petani.id",
      "created_at": "2026-10-03T22:00:00Z"
    }
  }
  ```
- **Response Error (`400 Bad Request` / `422 Unprocessable Entity`):**
  ```json
  {
    "detail": "Email sudah terdaftar",
    "error_code": "EMAIL_ALREADY_EXISTS"
  }
  ```

#### B. `POST /auth/login`
- **Deskripsi:** Otentikasi pengguna menggunakan email dan kata sandi.
- **Request Body (`application/json`):**
  ```json
  {
    "email": "yanto@petani.id",
    "password": "PasswordAman123!"
  }
  ```
- **Response Sukses (`200 OK`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in_minutes": 30
  }
  ```
- **Response Error (`401 Unauthorized`):**
  ```json
  {
    "detail": "Email atau password salah",
    "error_code": "INVALID_CREDENTIALS"
  }
  ```

#### C. `POST /auth/refresh`
- **Deskripsi:** Menerbitkan access token baru dari refresh token yang valid.
- **Request Body (`application/json`):**
  ```json
  {
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- **Response Sukses (`200 OK`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in_minutes": 30
  }
  ```

---

### 3.2 Resource: Predictions / Inferensi AI (`/predictions`)

#### A. `POST /predictions` **[★ Fitur Utama AI]**
- **Deskripsi:** Menerima foto daun singkong, menjalankan inferensi model Computer Vision (TensorFlow Lite / PyTorch ONNX), menyimpan hasil ke basis data, dan mengembalikan hasil diagnosis.
- **Headers:** `Authorization: Bearer <access_token>`
- **Request Body (`multipart/form-data`):**
  - `file`: Binary File Image (JPEG/PNG, maks 5MB)
  - `notes` *(optional)*: String catatan tambahan dari petani.
- **Response Sukses — High Confidence (`200 OK`):**
  ```json
  {
    "id": "prd_a1b2c3d4-e5f6-7890-abcd-1234567890ab",
    "image_url": "/uploads/predictions/2026/10/leaf_001.jpg",
    "disease_code": "CMD",
    "disease_name": "Cassava Mosaic Disease (CMD)",
    "confidence_score": 0.95,
    "confidence_percentage": "95.0%",
    "fallback_triggered": false,
    "treatment_guide": "Gunakan bibit bebas virus, musnahkan tanaman yang terinfeksi parah, dan kendalikan populasi kutu kebul (Bemisia tabaci).",
    "created_at": "2026-10-03T22:05:00Z"
  }
  ```
- **Response Sukses — Low Confidence / Fallback (BR-01 & AC-02) (`200 OK`):**
  ```json
  {
    "id": "prd_f9e8d7c6-b5a4-3210-fedc-0987654321ba",
    "image_url": "/uploads/predictions/2026/10/leaf_blur.jpg",
    "disease_code": "UNKNOWN",
    "disease_name": "Tidak Teridentifikasi",
    "confidence_score": 0.48,
    "confidence_percentage": "48.0%",
    "fallback_triggered": true,
    "message": "Hasil tidak pasti, silakan ambil ulang foto dengan pencahayaan yang lebih baik",
    "treatment_guide": null,
    "created_at": "2026-10-03T22:06:00Z"
  }
  ```
- **Response Error (`400 Bad Request` / `415 Unsupported Media Type` / `413 Payload Too Large`):**
  ```json
  {
    "detail": "Ukuran file melebihi batas maksimum 5MB atau format file tidak didukung",
    "error_code": "INVALID_FILE_FORMAT_OR_SIZE"
  }
  ```

#### B. `GET /predictions`
- **Deskripsi:** Mengambil daftar riwayat hasil pindaian daun pengguna yang sedang login.
- **Query Parameters:** `page` (default 1), `limit` (default 10).
- **Headers:** `Authorization: Bearer <access_token>`
- **Response Sukses (`200 OK`):**
  ```json
  {
    "total": 1,
    "page": 1,
    "limit": 10,
    "data": [
      {
        "id": "prd_a1b2c3d4-e5f6-7890-abcd-1234567890ab",
        "image_url": "/uploads/predictions/2026/10/leaf_001.jpg",
        "disease_code": "CMD",
        "disease_name": "Cassava Mosaic Disease (CMD)",
        "confidence_score": 0.95,
        "created_at": "2026-10-03T22:05:00Z"
      }
    ]
  }
  ```

---

### 3.3 Resource: Disease Catalog (`/diseases`)

#### A. `GET /diseases`
- **Deskripsi:** Katalog seluruh jenis penyakit & hama daun singkong yang dikenali sistem.
- **Response Sukses (`200 OK`):**
  ```json
  {
    "total": 6,
    "data": [
      { "code": "HEALTHY", "name": "Daun Sehat" },
      { "code": "CMD", "name": "Cassava Mosaic Disease" },
      { "code": "CBSD", "name": "Cassava Brown Streak Disease" },
      { "code": "BLS", "name": "Brown Leaf Spot" },
      { "code": "GMD", "name": "Green Mite Damage" },
      { "code": "RMD", "name": "Red Mite Damage" }
    ]
  }
  ```

---

## 4. Daftar Asumsi Teknis (`[ASUMSI-XX]`)

| Kode Asumsi | Rincian Asumsi Teknis | Status Verifikasi |
|---|---|---|
| `[ASUMSI-01]` | Model AI dijalankan secara *in-process* atau via *internal service handler* pada backend FastAPI (menggunakan TensorFlow Lite / ONNX Runtime Python). | Terverifikasi |
| `[ASUMSI-02]` | Berkas citra daun singkong disimpan di direktori media server lokal (`/uploads/predictions/`), dan path yang tersimpan di DB dapat diakses via static file route. | Terverifikasi |
| `[ASUMSI-03]` | Katalog penyakit daun mencakup 6 kelas utama: HEALTHY, CMD, CBSD, BLS, GMD, dan RMD sesuai riset Ramcharan et al. (2017). | Terverifikasi |
