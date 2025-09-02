from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class UserEntity(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "master"}

    id = Column(BigInteger, primary_key=True, index=True)
    person_id = Column(BigInteger, nullable=False)
    email_address = Column(String, unique=True, index=True, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)
    password = Column(String, nullable=False)  # hashed password
    remember_token = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_system_admin = Column(Boolean, default=False)
    preferences = Column(JSONB, nullable=True)
    notification_settings = Column(JSONB, nullable=True)
    two_factor_secret = Column(Text, nullable=True)
    two_factor_recovery_codes = Column(Text, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)