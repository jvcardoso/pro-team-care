from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, DateTime, Date, Time,
    Numeric, JSON, ForeignKey, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class People(Base):
    __tablename__ = "people"
    __table_args__ = (
        CheckConstraint("person_type IN ('PF', 'PJ')", name="people_person_type_check"),
        CheckConstraint("status IN ('active', 'inactive', 'pending', 'suspended', 'blocked')", name="people_status_check"),
        UniqueConstraint("tax_id", name="people_tax_id_unique"),
        Index("people_tax_id_idx", "tax_id"),
        Index("people_name_idx", "name"),
        Index("people_status_idx", "status"),
        Index("people_metadata_fulltext", "metadata", postgresql_using="gin"),
        {"schema": "master"}
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    person_type = Column(String(255), nullable=False)
    name = Column(String(200), nullable=False)
    trade_name = Column(String(200))
    tax_id = Column(String(14), nullable=False, unique=True)
    secondary_tax_id = Column(String(20))
    birth_date = Column(Date)
    incorporation_date = Column(Date)
    gender = Column(String(20))
    marital_status = Column(String(50))
    occupation = Column(String(100))
    tax_regime = Column(String(50))
    legal_nature = Column(String(100))
    municipal_registration = Column(String(20))
    website = Column(Text)
    description = Column(Text)
    status = Column(String(20), nullable=False, default='active')
    is_active = Column(Boolean, default=True)
    
    # LGPD fields
    lgpd_consent_version = Column(String(10))
    lgpd_consent_given_at = Column(DateTime)
    lgpd_data_retention_expires_at = Column(DateTime)
    
    # Metadata
    metadata_ = Column("metadata", JSON)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)

    # Relationships
    company = relationship("Company", back_populates="people", uselist=False)
    phones = relationship("Phone", back_populates="people", cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="people", cascade="all, delete-orphan")
    addresses = relationship("Address", back_populates="people", cascade="all, delete-orphan")


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("person_id", name="companies_person_id_unique"),
        Index("companies_person_id_idx", "person_id"),
        Index("companies_metadata_fulltext", "metadata", postgresql_using="gin"),
        Index("companies_settings_fulltext", "settings", postgresql_using="gin"),
        {"schema": "master"}
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    person_id = Column(BigInteger, ForeignKey("master.people.id"), nullable=False, unique=True)
    settings = Column(JSON)
    metadata_ = Column("metadata", JSON)
    display_order = Column(Integer, default=0)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)

    # Relationships
    people = relationship("People", back_populates="company")


class Establishments(Base):
    __tablename__ = "establishments"
    __table_args__ = (
        CheckConstraint("type IN ('matriz', 'filial', 'unidade', 'posto')", name="establishments_type_check"),
        CheckConstraint("category IN ('clinica', 'hospital', 'laboratorio', 'farmacia', 'consultorio', 'upa', 'ubs', 'outro')", name="establishments_category_check"),
        UniqueConstraint("company_id", "code", name="establishments_company_code_unique"),
        UniqueConstraint("company_id", "display_order", name="establishments_company_display_unique"),
        Index("establishments_company_idx", "company_id"),
        Index("establishments_person_idx", "person_id"),
        Index("establishments_active_idx", "is_active"),
        Index("establishments_principal_idx", "is_principal"),
        Index("establishments_type_idx", "type"),
        Index("establishments_category_idx", "category"),
        Index("establishments_display_order_idx", "company_id", "display_order"),
        {"schema": "master"}
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    person_id = Column(BigInteger, ForeignKey("master.people.id"), nullable=False)
    company_id = Column(BigInteger, ForeignKey("master.companies.id"), nullable=False)
    code = Column(String(50), nullable=False)
    type = Column(String(20), nullable=False)
    category = Column(String(30), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    is_principal = Column(Boolean, nullable=False, default=False)
    display_order = Column(Integer, nullable=False, default=0)
    settings = Column(JSON, nullable=True)
    meta_data = Column('metadata', JSON, nullable=True)
    operating_hours = Column(JSON, nullable=True)
    service_areas = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    person = relationship("People", foreign_keys=[person_id])
    company = relationship("Company", foreign_keys=[company_id])


class Phone(Base):
    __tablename__ = "phones"
    __table_args__ = (
        CheckConstraint("type IN ('landline', 'mobile', 'whatsapp', 'commercial', 'emergency', 'fax')", name="phones_type_check"),
        CheckConstraint("line_type IN ('prepaid', 'postpaid', 'corporate')", name="phones_line_type_check"),
        CheckConstraint("contact_priority >= 1 AND contact_priority <= 10", name="phones_contact_priority_check"),
        Index("phones_phoneable_type_id_idx", "phoneable_type", "phoneable_id"),
        Index("phones_whatsapp_idx", "is_whatsapp"),
        Index("phones_principal_idx", "is_principal"),
        {"schema": "master"}
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    phoneable_type = Column(String(50), nullable=False, default='App\\Models\\People')
    phoneable_id = Column(BigInteger, ForeignKey("master.people.id"), nullable=False)
    
    # Phone details
    country_code = Column(String(3), default='55')
    number = Column(String(11), nullable=False)
    extension = Column(String(10))
    type = Column(String(20), nullable=False, default='mobile')
    is_principal = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    phone_name = Column(String(100))
    
    # WhatsApp fields
    is_whatsapp = Column(Boolean, default=False)
    whatsapp_formatted = Column(String(15))
    whatsapp_verified = Column(Boolean, default=False)
    whatsapp_verified_at = Column(DateTime)
    whatsapp_business = Column(Boolean, default=False)
    whatsapp_name = Column(String(100))
    accepts_whatsapp_marketing = Column(Boolean, default=True)
    accepts_whatsapp_notifications = Column(Boolean, default=True)
    whatsapp_preferred_time_start = Column(Time)
    whatsapp_preferred_time_end = Column(Time)
    
    # Contact management
    carrier = Column(String(30))
    line_type = Column(String(20))
    contact_priority = Column(Integer, default=5)
    last_contact_attempt = Column(DateTime)
    last_contact_success = Column(DateTime)
    contact_attempts_count = Column(Integer, default=0)
    can_receive_calls = Column(Boolean, default=True)
    can_receive_sms = Column(Boolean, default=True)
    
    # Verification fields
    verified_at = Column(DateTime)
    verification_method = Column(String(50))
    
    # Additional data
    api_data = Column(JSON)
    
    # Audit user fields
    created_by_user_id = Column(BigInteger)
    updated_by_user_id = Column(BigInteger)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)

    # Relationships
    people = relationship("People", back_populates="phones")


class Email(Base):
    __tablename__ = "emails"
    __table_args__ = (
        CheckConstraint("type IN ('personal', 'work', 'billing', 'contact')", name="emails_type_check"),
        Index("emails_emailable_type_id_idx", "emailable_type", "emailable_id"),
        Index("emails_email_address_idx", "email_address"),
        Index("emails_principal_idx", "is_principal"),
        {"schema": "master"}
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    emailable_type = Column(String(50), nullable=False, default='App\\Models\\People')
    emailable_id = Column(BigInteger, ForeignKey("master.people.id"), nullable=False)
    
    # Email details
    email_address = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False, default='work')
    is_principal = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    verified_at = Column(DateTime)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)

    # Relationships
    people = relationship("People", back_populates="emails")


class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = (
        CheckConstraint("type IN ('residential', 'commercial', 'correspondence', 'billing', 'delivery')", name="addresses_type_check"),
        CheckConstraint("access_difficulty IN ('easy', 'medium', 'hard', 'unknown')", name="addresses_access_difficulty_check"),
        CheckConstraint("quality_score >= 0 AND quality_score <= 100", name="addresses_quality_score_check"),
        Index("addresses_addressable_type_id_idx", "addressable_type", "addressable_id"),
        Index("addresses_city_state_idx", "city", "state"),
        Index("addresses_zip_code_idx", "zip_code"),
        Index("addresses_coordinates_idx", "latitude", "longitude"),
        Index("addresses_principal_idx", "is_principal"),
        {"schema": "master"}
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    addressable_type = Column(String(50), nullable=False, default='App\\Models\\People')
    addressable_id = Column(BigInteger, ForeignKey("master.people.id"), nullable=False)
    
    # Address details
    street = Column(String(255), nullable=False)
    number = Column(String(20), nullable=True)  # Permitir valores nulos
    details = Column(String(100))
    neighborhood = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(2), nullable=False)
    zip_code = Column(String(10), nullable=False)
    country = Column(String(2), default='BR')
    type = Column(String(20), nullable=False, default='commercial')
    is_principal = Column(Boolean, default=False)
    
    # Geocoding fields
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    google_place_id = Column(String(255))
    formatted_address = Column(Text)
    geocoding_accuracy = Column(String(50))
    geocoding_source = Column(String(50))
    coordinates_added_at = Column(DateTime)
    coordinates_source = Column(String(50))

    # Enrichment metadata
    enriched_at = Column(DateTime)
    enrichment_source = Column(String(50))
    ibge_city_code = Column(Integer)
    ibge_state_code = Column(Integer)
    gia_code = Column(String(10))
    siafi_code = Column(String(10))
    area_code = Column(String(5))
    region = Column(String(100))
    microregion = Column(String(100))
    mesoregion = Column(String(100))
    
    # Coverage analysis fields
    within_coverage = Column(Boolean)
    distance_to_establishment = Column(Integer)
    estimated_travel_time = Column(Integer)
    access_difficulty = Column(String(20))
    access_notes = Column(Text)
    
    # Quality fields
    quality_score = Column(Integer)
    is_validated = Column(Boolean, default=False)
    last_validated_at = Column(DateTime)
    validation_source = Column(String(100))
    api_data = Column(JSON)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)

    # Relationships
    people = relationship("People", back_populates="addresses")


class Menu(Base):
    """Model ORM otimizado para Menus Dinâmicos"""
    __tablename__ = "menus"
    __table_args__ = (
        CheckConstraint("menu_type IN ('folder', 'page', 'external_link', 'separator')", name="menus_type_check"),
        CheckConstraint("status IN ('active', 'inactive', 'draft')", name="menus_status_check"),
        CheckConstraint("level >= 0 AND level <= 4", name="menus_level_check"),
        CheckConstraint("sort_order >= 0", name="menus_sort_order_check"),
        
        # Índices otimizados para performance
        Index("menus_parent_sort_idx", "parent_id", "sort_order"),
        Index("menus_hierarchy_idx", "level", "parent_id", "sort_order"),
        Index("menus_slug_parent_idx", "slug", "parent_id"),
        Index("menus_permission_idx", "permission_name"),
        Index("menus_status_visible_idx", "status", "is_visible", "visible_in_menu"),
        Index("menus_context_idx", "company_specific", "establishment_specific"),
        Index("menus_fulltext_idx", "full_path_name", postgresql_using="gin"),
        
        # Constraint de slug único por nível
        UniqueConstraint("slug", "parent_id", name="menus_slug_parent_unique"),
        
        {"schema": "master"}
    )

    # Identificação
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    parent_id = Column(BigInteger, ForeignKey("master.menus.id"), nullable=True)
    
    # Dados principais
    name = Column(String(100), nullable=False)
    slug = Column(String(50), nullable=False)
    url = Column(String(255), nullable=True)
    route_name = Column(String(100), nullable=True)
    route_params = Column(Text, nullable=True)
    
    # Hierarquia e ordenação
    level = Column(Integer, nullable=False, default=0)
    sort_order = Column(Integer, nullable=False, default=0)
    
    # Tipo e status
    menu_type = Column(String(20), nullable=False, default='page')
    status = Column(String(20), nullable=False, default='active')
    
    # Visibilidade
    is_visible = Column(Boolean, nullable=False, default=True)
    visible_in_menu = Column(Boolean, nullable=False, default=True)
    
    # Permissões e contexto
    permission_name = Column(String(100), nullable=True)
    company_specific = Column(Boolean, nullable=False, default=False)
    establishment_specific = Column(Boolean, nullable=False, default=False)
    
    # Customização visual
    icon = Column(String(50), nullable=True)
    badge_text = Column(String(20), nullable=True)
    badge_color = Column(String(20), nullable=True)
    css_class = Column(String(100), nullable=True)
    
    # Metadados
    description = Column(String(255), nullable=True)
    help_text = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True)  # Array de strings
    
    # Hierarquia computada (para performance)
    full_path_name = Column(String(500), nullable=True)
    id_path = Column(JSON, nullable=True)  # Array de IDs do caminho
    
    # Auditoria
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(BigInteger, nullable=True)  # FK para users será adicionada posteriormente
    updated_by = Column(BigInteger, nullable=True)  # FK para users será adicionada posteriormente
    
    # Relationships
    parent = relationship("Menu", remote_side=[id], back_populates="children")
    children = relationship("Menu", back_populates="parent", cascade="all, delete-orphan")