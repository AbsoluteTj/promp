"""
models.py
---------
Modul data model untuk aplikasi Backend CassavaCare AI (PTM-05).
Menggabungkan:
1. SQLAlchemy ORM Models (Layer Database Relasional PostgreSQL)
2. Pydantic v2 Schemas (Layer Validasi Request/Response & Serialisasi DTO)

Tracing Requirement & Asumsi:
- FR-01: Autentikasi Pengguna & Manajemen Token JWT
- FR-02: Diagnosa Penyakit Daun Singkong [★ AI]
- FR-03: Riwayat Diagnosa Pengguna
- FR-04: Katalog Informasi Penyakit & Hama
- [ASUMSI-01]: Password di-hash menggunakan Argon2id / bcrypt.
- [ASUMSI-02]: Primary Key menggunakan UUID v4 untuk mitigasi BOLA/IDOR (OWASP API1:2023).
- [ASUMSI-03]: Batas ambang keyakinan (confidence score) AI adalah 0.70 (70%).
- [ASUMSI-04]: Jika confidence < 0.70, status = LOW_CONFIDENCE dan disease_id bernilai NULL.
- [ASUMSI-05]: Token Refresh di-hash dengan SHA-256 sebelum disimpan di database.
- [ASUMSI-06]: Kolom 'metadata' pada tabel predictions di ORM dinamai 'metadata_json' 
               guna menghindari konflik kata kunci reserved 'metadata' milik SQLAlchemy MetaData.
"""

import enum
import uuid
import re
from datetime import datetime
from typing import List, Optional, Any, Dict

# ------------------------------------------------------------------------------
# Pydantic v2 Imports & Configuration
# ------------------------------------------------------------------------------
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator
)

# Regex standar validasi email tanpa ketergantungan library luar
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

# ------------------------------------------------------------------------------
# SQLAlchemy ORM Imports
# ------------------------------------------------------------------------------
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Float,
    Text,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ==============================================================================
# ENUMERATIONS (Shared Domain Enums)
# ==============================================================================

class UserRole(str, enum.Enum):
    """Peran pengguna dalam sistem CassavaCare AI."""
    FARMER = "FARMER"
    EXPERT = "EXPERT"
    ADMIN = "ADMIN"


class PredictionStatus(str, enum.Enum):
    """Status hasil inferensi model AI."""
    CONFIDENT = "CONFIDENT"          # Confidence >= 0.70
    LOW_CONFIDENCE = "LOW_CONFIDENCE" # Confidence < 0.70 [ASUMSI-04]
    FAILED = "FAILED"                # Gagal inferensi / gambar rusak


class DiseaseCode(str, enum.Enum):
    """Kode standar penyakit daun singkong berdasarkan dataset."""
    CMD = "CMD"       # Cassava Mosaic Disease
    CBSD = "CBSD"     # Cassava Brown Streak Disease
    BLS = "BLS"       # Bacterial Blight / Bacterial Leaf Spot
    GMD = "GMD"       # Green Mite Damage
    RMD = "RMD"       # Red Mite Damage
    HEALTHY = "HEALTHY" # Tanaman Sehat


# ==============================================================================
# 1. SQLALCHEMY ORM MODELS
# ==============================================================================

class User(Base):
    """
    Model ORM untuk tabel 'users'.
    Menyimpan data identitas pengguna, kredensial hash, dan peran akses.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(SQLEnum(UserRole, name="user_role_enum"), nullable=False, default=UserRole.FARMER)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relasi
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class RefreshToken(Base):
    """
    Model ORM untuk tabel 'refresh_tokens'.
    Mengelola token JWT penyegaran untuk otentikasi stateless yang aman [ASUMSI-05].
    """
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    is_revoked = Column(Boolean, nullable=False, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relasi
    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, revoked={self.is_revoked})>"


class Disease(Base):
    """
    Model ORM untuk tabel 'diseases'.
    Katalog rujukan informasi penyakit, gejala, dan panduan penanganan daun singkong (FR-04).
    """
    __tablename__ = "diseases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    latin_name = Column(String(100), nullable=True)
    description = Column(Text, nullable=False)
    symptoms = Column(Text, nullable=False)
    treatment = Column(Text, nullable=False)
    prevention = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relasi
    predictions = relationship("Prediction", back_populates="disease")

    def __repr__(self):
        return f"<Disease(code='{self.code}', name='{self.name}')>"


class Prediction(Base):
    """
    Model ORM untuk tabel 'predictions'.
    Menyimpan transaksi riwayat inferensi AI diagnosa penyakit (FR-02, FR-03).
    """
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    disease_id = Column(UUID(as_uuid=True), ForeignKey("diseases.id", ondelete="SET NULL"), nullable=True)
    image_url = Column(String(512), nullable=False)
    predicted_label = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    status = Column(SQLEnum(PredictionStatus, name="prediction_status_enum"), nullable=False)
    
    # [ASUMSI-06]: Menamai atribut ORM 'metadata_json' untuk menghindari konflik nama dengan MetaData milik SQLAlchemy
    metadata_json = Column("metadata", JSONB, nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Index Komposit untuk optimasi kueri pagination riwayat per user (< 100ms)
    __table_args__ = (
        Index("idx_predictions_user_created", "user_id", created_at.desc()),
    )

    # Relasi
    user = relationship("User", back_populates="predictions")
    disease = relationship("Disease", back_populates="disease")

    def __repr__(self):
        return f"<Prediction(id={self.id}, label='{self.predicted_label}', confidence={self.confidence_score}, status='{self.status}')>"


# ==============================================================================
# 2. PYDANTIC V2 SCHEMAS (DTO & Request/Response Validation)
# ==============================================================================

# ------------------------------------------------------------------------------
# A. Generic & Common Schemas
# ------------------------------------------------------------------------------

class ResponseMeta(BaseModel):
    """Metadata standar untuk pembungkus respon API."""
    code: int = Field(..., example=200, description="Kode status HTTP")
    message: str = Field(..., example="Request processed successfully", description="Pesan deskriptif respon")


class PaginationMeta(BaseModel):
    """Metadata pagination untuk respon daftar berhalaman."""
    page: int = Field(..., example=1, ge=1)
    limit: int = Field(..., example=10, ge=1, le=100)
    total_items: int = Field(..., example=45, ge=0)
    total_pages: int = Field(..., example=5, ge=0)


class ErrorDetail(BaseModel):
    """Detail struktur kesalahan terstandar."""
    field: Optional[str] = Field(None, example="email", description="Nama field yang mengalami error jika ada")
    message: str = Field(..., example="Format email tidak valid", description="Detail rincian pesan error")


class ErrorResponse(BaseModel):
    """Format standar respon error API (HTTP 400, 401, 403, 404, 422, 500)."""
    meta: ResponseMeta
    errors: Optional[List[ErrorDetail]] = None


# ------------------------------------------------------------------------------
# B. Authentication Schemas (FR-01)
# ------------------------------------------------------------------------------

class UserSignUpRequest(BaseModel):
    """Schema input untuk registrasi akun baru."""
    email: str = Field(..., pattern=EMAIL_REGEX, example="petani@cassavacare.id", description="Alamat email valid")
    password: str = Field(..., min_length=8, max_length=64, example="P@ssw0rd2026!", description="Password minimal 8 karakter")
    full_name: str = Field(..., min_length=2, max_length=100, example="Budi Santoso", description="Nama lengkap pengguna")

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, value: str) -> str:
        """Validasi keamanan password dasar."""
        if not any(char.isdigit() for char in value):
            raise ValueError("Password harus mengandung minimal satu angka")
        if not any(char.isalpha() for char in value):
            raise ValueError("Password harus mengandung minimal satu huruf")
        return value


class UserLoginRequest(BaseModel):
    """Schema input untuk autentikasi login."""
    email: str = Field(..., pattern=EMAIL_REGEX, example="petani@cassavacare.id")
    password: str = Field(..., example="P@ssw0rd2026!")


class TokenData(BaseModel):
    """Struktur pasangan JWT Token."""
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    refresh_token: str = Field(..., example="d9b2a8f4-3c1e-4b5a-9a0d-2e4f6a8b1c3d")
    token_type: str = Field(default="Bearer", example="Bearer")
    expires_in: int = Field(..., example=3600, description="Masa berlaku access token dalam detik (1 jam)")


class UserResponseData(BaseModel):
    """Schema respon profil pengguna (DTO)."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., example="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
    email: str = Field(..., example="petani@cassavacare.id")
    full_name: str = Field(..., example="Budi Santoso")
    role: UserRole = Field(..., example=UserRole.FARMER)
    is_active: bool = Field(..., example=True)
    created_at: datetime


class AuthResponse(BaseModel):
    """Respon gabungan autentikasi (Token + User Data)."""
    meta: ResponseMeta
    data: Dict[str, Any]  # Berisi 'user' dan 'tokens'


class RefreshTokenRequest(BaseModel):
    """Schema input penyegaran token JWT."""
    refresh_token: str = Field(..., example="d9b2a8f4-3c1e-4b5a-9a0d-2e4f6a8b1c3d")


# ------------------------------------------------------------------------------
# C. Disease Catalogue Schemas (FR-04)
# ------------------------------------------------------------------------------

class DiseaseBase(BaseModel):
    """Properti dasar entitas penyakit."""
    code: str = Field(..., example="CMD", min_length=2, max_length=20)
    name: str = Field(..., example="Cassava Mosaic Disease", max_length=100)
    latin_name: Optional[str] = Field(None, example="Begomovirus", max_length=100)
    description: str = Field(..., example="Penyakit bercak kuning bergelombang pada daun...")
    symptoms: str = Field(..., example="Daun mengalami klorosis dan distorsi bentuk...")
    treatment: str = Field(..., example="Gunakan varietas tahan virus dan basmi kutu kebul...")
    prevention: str = Field(..., example="Gunakan bibit bebas virus dan rotasi tanaman...")


class DiseaseCreate(DiseaseBase):
    """Schema pembuatan data penyakit baru oleh ADMIN."""
    pass


class DiseaseResponse(DiseaseBase):
    """Schema respon detail penyakit."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., example="c39a2817-2109-4e12-8d76-123456789abc")
    created_at: datetime
    updated_at: datetime


class SingleDiseaseResponse(BaseModel):
    """Respon tunggal data penyakit."""
    meta: ResponseMeta
    data: DiseaseResponse


class ListDiseaseResponse(BaseModel):
    """Respon daftar katalog penyakit."""
    meta: ResponseMeta
    data: List[DiseaseResponse]


# ------------------------------------------------------------------------------
# D. AI Prediction Schemas (FR-02, FR-03, [★ AI])
# ------------------------------------------------------------------------------

class PredictionDetailData(BaseModel):
    """Schema detail data hasil diagnosa AI."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., example="f47ac10b-58cc-4372-a567-0e02b2c3d479")
    user_id: uuid.UUID = Field(..., example="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
    disease_id: Optional[uuid.UUID] = Field(None, example="c39a2817-2109-4e12-8d76-123456789abc", 
                                            description="NULL jika status LOW_CONFIDENCE [ASUMSI-04]")
    image_url: str = Field(..., example="https://storage.cassavacare.id/uploads/2026/10/img_9876.jpg")
    predicted_label: str = Field(..., example="CMD", description="Label kelas prediksi AI")
    confidence_score: float = Field(..., example=0.945, ge=0.0, le=1.0, description="Nilai kepastian AI (0.0 - 1.0)")
    status: PredictionStatus = Field(..., example=PredictionStatus.CONFIDENT)
    metadata_json: Optional[Dict[str, Any]] = Field(None, alias="metadata", example={"inference_time_ms": 142, "model_version": "v1.2.0"})
    created_at: datetime
    disease_info: Optional[DiseaseResponse] = Field(None, description="Objek detail penyakit jika status CONFIDENT")

    @field_validator("confidence_score")
    @classmethod
    def round_confidence(cls, value: float) -> float:
        """Membulatkan confidence score hingga 4 desimal."""
        return round(value, 4)


class FallbackWarning(BaseModel):
    """Informasi peringatan penanganan kondisi kepastian rendah AI (< 70%)."""
    threshold_applied: float = Field(default=0.70, example=0.70)
    user_message: str = Field(
        default="Hasil diagnosa memiliki tingkat kepastian di bawah 70%. Harap ambil ulang foto daun dengan pencahayaan terang dan fokus yang jelas.",
        example="Hasil diagnosa memiliki tingkat kepastian di bawah 70%. Harap ambil ulang foto daun dengan pencahayaan terang dan fokus yang jelas."
    )
    suggested_actions: List[str] = Field(
        default=[
            "Pastikan daun memenuhi 80% area foto",
            "Gunakan latar belakang netral dan cegah bayangan gelap",
            "Konsultasikan ke PPL/Pakar jika gejala terus meragukan"
        ]
    )


class PredictionResponse(BaseModel):
    """Respon utama API POST /predictions [★ AI]."""
    meta: ResponseMeta
    data: PredictionDetailData
    warning: Optional[FallbackWarning] = Field(
        None, 
        description="Hanya muncul jika status LOW_CONFIDENCE (< 0.70) [BR-01, AC-02]"
    )


class ListPredictionResponse(BaseModel):
    """Respon daftar riwayat diagnosa berhalaman (FR-03)."""
    meta: ResponseMeta
    data: List[PredictionDetailData]
    pagination: PaginationMeta


# ==============================================================================
# Selesai
# ==============================================================================
