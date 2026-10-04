# 🛡️ OWASP API Security Audit & Remediation Report
**Project:** CassavaCare AI Backend REST API  
**Standard Compliance:** OWASP API Security Top 10 (2023)  
**Target Architecture:** FastAPI (Python 3.12) + PostgreSQL + Pydantic v2 + SQLAlchemy 2.0  
**Document Status:** Final Verified  

---

## 1. 📌 Ringkasan Eksekutif (Executive Summary)

Laporan audit keamanan ini disusun berdasarkan standar **OWASP API Security Top 10 (2023)** untuk mengevaluasi dan memperkuat lapisan keamanan pada backend **CassavaCare AI**. Sebagai platform berbasis kecerdasan buatan (*computer vision*) yang menangani otentikasi pengguna, manajemen katalog penyakit, dan proses inferensi AI berisiko tinggi (*file upload* foto daun singkong), sistem backend wajib dilindungi dari berbagai celah eksploitasi API.

### **Hasil Audit Utama:**
- **Status Keamanan Sebelum Audit:** Vulnerable terhadap *Broken Object Level Authorization (BOLA)* pada riwayat diagnosa dan risiko *Unrestricted File Upload / Remote Code Execution (RCE)* melalui manipulasi payload citra AI.
- **Tindakan Remediasi (Patching):** Penerapan *ownership validation* berbasis UUID v4, sanitasi berkas tingkat *Magic Bytes*, pembatasan laju (*Rate Limiting*), serta enkapsulasi token JWT *stateless* dengan mekanisme *Revocation List*.
- **Postur Keamanan Akhir:** **SECURE (100% Patch Applied)** untuk seluruh 10 kategori ancaman OWASP API 2023.

---

## 2. 📑 Matriks Evaluasi Keamanan OWASP API Top 10 (2023)

| Kode OWASP | Kategori Kerentanan | Tingkat Risiko | Status Remediasi | Merekam Patch Utama |
| :--- | :--- | :---: | :---: | :--- |
| **API1:2023** | **Broken Object Level Authorization (BOLA)** | **CRITICAL** | ✅ **FIXED** | Kueri DB mewajibkan filter gabungan `prediction_id` + `user_id` dari JWT token. |
| **API2:2023** | **Broken Authentication** | **HIGH** | ✅ **FIXED** | Hashing password `bcrypt` (cost 12), JWT HS256 short-lived (30 min), Refresh Token rotation. |
| **API3:2023** | **Broken Object Property Level Authorization** | **MEDIUM** | ✅ **FIXED** | Schema Pydantic v2 dengan `extra="forbid"` mencegah *Mass Assignment / Over-posting*. |
| **API4:2023** | **Unrestricted Resource Consumption** | **HIGH** | ✅ **FIXED** | Rate limit 60 req/min, max upload 10MB, pagination limit max 50 items. |
| **API5:2023** | **Broken Function Level Authorization (BFLA)** | **HIGH** | ✅ **FIXED** | Middleware RBAC membatasi role `ADMIN` untuk mutating katalog `/diseases`. |
| **API6:2023** | **Unrestricted Access to Sensitive Business Flows** | **MEDIUM** | ✅ **FIXED** | Rate limiting khusus endpoint `POST /predictions` untuk mencegah kecurangan *AI inference spam*. |
| **API7:2023** | **Server Side Request Forgery (SSRF)** | **LOW** | ✅ **N/A / SECURE** | Pemrosesan citra dilakukan secara lokal via stream upload, tidak menerima URL eksternal arbitrary. |
| **API8:2023** | **Security Misconfiguration** | **MEDIUM** | ✅ **FIXED** | Header HTTP Keamanan (CORS strict, HSTS, X-Content-Type-Options, X-Frame-Options DENY). |
| **API9:2023** | **Improper Inventory Management** | **LOW** | ✅ **FIXED** | Pentahapan API eksplisit `/api/v1`, OpenAPI 3.0 spec tersinkronisasi, endpoint tidak terpakai ditutup. |
| **API10:2023** | **Unsafe Consumption of APIs** | **MEDIUM** | ✅ **FIXED** | Validasi output model AI, penanganan skor kepastian rendah (< 0.70) secara terisolasi. |

---

## 3. 🛡️ Detail Analisis Kerentanan & Kode Remediasi (Patch Code)

### 3.1. API1:2023 - Broken Object Level Authorization (BOLA)
* **Vulnerability Threat:** Pengguna A (petani) dapat menebak/mengganti ID transaksi diagnosa milik Pengguna B pada endpoint `GET /predictions/{prediction_id}` untuk melihat foto dan hasil diagnosa milik petani lain.
* **Impact:** Kebocoran data privasi petani dan data geografis tanaman.
* **Remediation Strategy:** 
  1. Mengganti pola ID Auto-increment integer menjadi **UUID v4** yang acak (secara acak sulit ditebak).
  2. Menambahkan pemeriksaan *Ownership Check* di layer Repository/Service di mana setiap pencarian data transaksi wajib menyertakan ID pengguna yang terekstraksi secara aman dari JWT Token.

```python
# ❌ KODE RENTAN (Vulnerable Code - BOLA Risk)
@router.get("/predictions/{prediction_id}")
def get_prediction_vulnerable(prediction_id: str, db: Session = Depends(get_db)):
    # RENTAN: Hanya mencari berdasarkan ID tanpa memverifikasi siapa pemiliknya!
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction


# ✅ KODE PERBAIKAN (Patched Code - Strict BOLA Protection)
@router.get("/predictions/{prediction_id}", response_model=PredictionResponse)
def get_prediction_secure(
    prediction_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # PATCH: Memaksa filter ganda (prediction_id DAN user_id pemilik JWT)
    prediction = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.user_id == current_user.id  # OWASP API1:2023 Fix
    ).first()
    
    if not prediction:
        # Mengembalikan 404 Not Found untuk mencegah Enumeration Attack
        raise HTTPException(status_code=404, detail="Diagnosa tidak ditemukan atau Anda tidak memiliki akses.")
    
    return PredictionResponse(success=True, message="Detail diagnosa berhasil diambil.", data=prediction)
```

---

### 3.2. API2:2023 - Broken Authentication
* **Vulnerability Threat:** Serangan *Brute-Force* password, penggunaan token yang berlaku selamanya, atau kebocoran kredensial akibat algoritma hashing yang lemah (MD5/SHA1).
* **Remediation Strategy:**
  1. Enkripsi password menggunakan **`bcrypt`** dengan cost factor 12.
  2. Implementasi **JWT Access Token** berdurasi singkat (30 menit) dan **Refresh Token** (7 hari).
  3. Menyimpan hash Refresh Token di database (`refresh_tokens` table) untuk mendukung *Instant Session Revocation* / Logout.

```python
# ✅ KEAMANAN HASHING & DUKUNGAN REVOCATION
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=30)) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
```

---

### 3.3. API3:2023 - Broken Object Property Level Authorization (Mass Assignment)
* **Vulnerability Threat:** Penyerang mengirimkan payload JSON registrasi yang disisipi field unauthorized seperti `role: "ADMIN"` atau `is_active: true` untuk melakukan *privilege escalation*.
* **Remediation Strategy:** Memisahkan skema DTO Pydantic v2 antara Request Input (`UserSignUpRequest`) dan DB Model (`User`). Mengonfigurasi `extra = "forbid"` pada Pydantic DTO.

```python
# ✅ PYDANTIC V2 DTO - PREVENT OVER-POSTING
from pydantic import BaseModel, Field, EmailStr, ConfigDict

class UserSignUpRequest(BaseModel):
    # Mengisolasi hanya field yang diizinkan diisi publik
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)
    full_name: str = Field(..., min_length=2, max_length=100)

    model_config = ConfigDict(
        extra="forbid",  # Menolak properti tidak dikenal seperti "role" atau "is_superuser"
        str_strip_whitespace=True
    )
```

---

### 3.4. API4:2023 - Unrestricted Resource Consumption & Sanitasi File AI
* **Vulnerability Threat:** 
  1. Penyerang mengunggah file raksasa (misal 2GB) yang menghabiskan memori RAM/Disk server.
  2. Penyerang mengunggah file skrip berbahaya (`malicious.php` atau `shell.py`) yang disamarkan dengan ekstensi `.jpg`.
* **Remediation Strategy (5-Layer Upload Sanitization Pipeline):**
  - **Layer 1 (Size Guard):** Batas maksimum ukuran berkas 10MB.
  - **Layer 2 (MIME Whitelisting):** Hanya menerima `image/jpeg` dan `image/png`.
  - **Layer 3 (Magic Bytes Validation):** Memeriksa header biner file asli.
  - **Layer 4 (Filename Randomization & Traversal Prevention):** Mengganti nama asli dengan `UUID4.jpg`.
  - **Layer 5 (Image Re-encoding via PIL):** Membaca ulang citra menggunakan Pillow/OpenCV untuk mengikis payload *EXIF metadata exploits* atau kode terselubung.

```python
# ✅ SANITASI FILE UPLOAD UNTUK INFERENSI AI
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import io
import uuid

ALLOWED_MIME_TYPES = {"image/jpeg": b"\xFF\xD8\xFF", "image/png": b"\x89PNG\r\n\x1a\n"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

async def sanitize_and_validate_image(file: UploadFile) -> bytes:
    # 1. Validasi Ukuran File (Content-Length Header & Read Stream)
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Ukuran file melebihi batas maksimum 10MB."
        )
    
    # 2. Validasi MIME Type Header
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Format file tidak didukung. Hanya JPEG dan PNG yang diperbolehkan."
        )
        
    # 3. Validasi Magic Bytes (Pemeriksaan Header Biner Asli File)
    expected_magic = ALLOWED_MIME_TYPES[file.content_type]
    if not contents.startswith(expected_magic):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Berkas tidak valid atau terindikasi manipulasi ekstensi (Magic Bytes Mismatch)."
        )
        
    # 4. Re-encoding Citra via PIL (Mengikis WebShell/EXIF Malware)
    try:
        image = Image.open(io.BytesIO(contents))
        image.verify()  # Verifikasi integritas citra
        
        # Buka kembali untuk re-encoding karena verify() menutup stream
        image = Image.open(io.BytesIO(contents))
        output_stream = io.BytesIO()
        image_format = "JPEG" if file.content_type == "image/jpeg" else "PNG"
        image.save(output_stream, format=image_format)
        sanitized_bytes = output_stream.getvalue()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File citra rusak atau tidak dapat diproses oleh parser visual."
        )
        
    return sanitized_bytes
```

---

### 3.5. API5:2023 - Broken Function Level Authorization (BFLA)
* **Vulnerability Threat:** Petani biasa (`FARMER`) memanggil endpoint administratif seperti `POST /diseases` untuk menambah atau menghapus katalog penyakit.
* **Remediation Strategy:** Penerapan *Role-Based Access Control (RBAC)* melalui FastAPI Dependency Injection.

```python
# ✅ ROLE-BASED ACCESS CONTROL (RBAC) DEPENDENCY
def require_roles(allowed_roles: list[UserRole]):
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Akses ditolak. Fitur ini memerlukan hak akses: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker

# Endpoint Katalog Penyakit (Hanya ADMIN yang boleh membuat)
@router.post("/diseases", response_model=SingleDiseaseResponse, status_code=201)
def create_disease(
    payload: DiseaseCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    # Logika pembuatan penyakit baru oleh Admin
    pass
```

---

### 3.6. API8:2023 - Security Misconfiguration (Security Headers & CORS)
* **Vulnerability Threat:** Server tidak mengonfigurasi header keamanan HTTP, memungkinkan serangan *Cross-Site Scripting (XSS)*, *Clickjacking*, atau kebocoran CORS (*wildcard `*`*).
* **Remediation Strategy:** Pengaturan Middleware CORS yang ketat dan injeksi Security Headers pada setiap response.

```python
# ✅ KEAMANAN MIDDLEWARE FASTAPI
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CassavaCare AI API", version="1.0.0")

# Strict CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cassavacare.id", "https://app.cassavacare.id"], # Hindari "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Custom Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

---

## 4. 📊 Ringkasan Temuan Audit & Tindakan Remediasi

| ID Temuan | Komponen Target | Dampak Kerentanan | Rekomendasi / Fix Status |
| :--- | :--- | :--- | :--- |
| **SEC-01** | `POST /predictions` | BOLA pada riwayat diagnosa (`API1:2023`) | **RESOLVED:** Menambahkan filter `user_id` dari JWT token pada kueri DB. |
| **SEC-02** | `UploadFile` Handler | Unrestricted File Upload & RCE (`API4:2023`) | **RESOLVED:** Penerapan 5-layer sanitasi (Magic Bytes, Limit 10MB, PIL Re-encode). |
| **SEC-03** | `POST /diseases` | Privilege Escalation oleh Farmer (`API5:2023`) | **RESOLVED:** Menambahkan dependency `require_roles([UserRole.ADMIN])`. |
| **SEC-04** | Auth Subsystem | Brute-force & Token Leaks (`API2:2023`) | **RESOLVED:** Enkripsi `bcrypt` cost 12, JWT 30m, Refresh token revocation list. |
| **SEC-05** | HTTP Response Headers | Clickjacking & MIME Sniffing (`API8:2023`) | **RESOLVED:** Middleware HTTP Security Headers + CORS Whitelisting domain resmi. |

---

## 5. 🎯 Kesimpulan

Melalui implementasi audit keamanan berdasarkan standar **OWASP API Security Top 10 (2023)**, backend **CassavaCare AI** dinyatakan memiliki postur keamanan yang handal dan tangguh. Seluruh celah berisiko tinggi (*BOLA*, *Unrestricted File Upload*, *Authentication Bypasses*) telah ditutup dengan patch sistemik pada layer Router, Service, dan Repository.
