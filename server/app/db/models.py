from __future__ import annotations
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, UniqueConstraint, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    sessions: Mapped[list["Session"]] = relationship(back_populates="user")
    license_codes: Mapped[list["LicenseCode"]] = relationship(back_populates="redeemed_by")

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # e.g., demo_paid
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    license_codes: Mapped[list["LicenseCode"]] = relationship(back_populates="product")

class LicenseCode(Base):
    __tablename__ = "license_codes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)  # full printable code

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    product: Mapped["Product"] = relationship(back_populates="license_codes")

    # 서명된 payload의 만료일(옵션)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    redeemed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    redeemed_by: Mapped["User | None"] = relationship(back_populates="license_codes")

    redeemed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # HWID 해시 바인딩 (한 번 bind되면 변경 시 무효/재인증 요구)
    bound_hwid_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # hex sha256

    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoke_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    user: Mapped["User"] = relationship(back_populates="sessions")

    # DB에는 토큰 해시만 저장
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)  # hex sha256
    hwid_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoke_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_sessions_user_active", "user_id", "is_active"),
    )
