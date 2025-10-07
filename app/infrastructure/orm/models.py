from typing import Any, Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class People(Base):
    __tablename__ = "people"
    __table_args__ = (
        CheckConstraint("person_type IN ('PF', 'PJ')", name="people_person_type_check"),
        CheckConstraint(
            "status IN ('active', 'inactive', 'pending', 'suspended', 'blocked')",
            name="people_status_check",
        ),
        UniqueConstraint("company_id", "tax_id", name="people_company_tax_id_unique"),
        Index("people_company_idx", "company_id"),
        Index("people_company_tax_id_idx", "company_id", "tax_id"),
        Index("people_tax_id_idx", "tax_id"),
        Index("people_name_idx", "name"),
        Index("people_status_idx", "status"),
        # Index("people_metadata_fulltext", "metadata", postgresql_using="gin"),  # Disabled due to GIN index issue
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(BigInteger, ForeignKey("master.companies.id"), nullable=False)
    person_type = Column(String(255), nullable=False)
    name = Column(String(200), nullable=False)
    trade_name = Column(String(200))
    tax_id = Column(String(14), nullable=False)
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
    status = Column(String(20), nullable=False, default="active")
    is_active = Column(Boolean, default=True)

    # LGPD fields
    lgpd_consent_version = Column(String(10))
    lgpd_consent_given_at = Column(DateTime)
    lgpd_data_retention_expires_at = Column(DateTime)

    # Metadata
    metadata_ = Column("metadata", JSON)

    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    deleted_at = Column(DateTime)

    # Relationships
    company = relationship(
        "Company",
        back_populates="people",
        foreign_keys="Company.person_id",
        uselist=False,
    )
    user = relationship("User", back_populates="person", uselist=False)
    phones = relationship(
        "Phone", back_populates="people", cascade="all, delete-orphan"
    )
    emails = relationship(
        "Email", back_populates="people", cascade="all, delete-orphan"
    )
    addresses = relationship(
        "Address", back_populates="people", cascade="all, delete-orphan"
    )


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        CheckConstraint(
            "access_status IN ('pending_contract', 'contract_signed', 'pending_user', 'active', 'suspended')",
            name="companies_access_status_check",
        ),
        UniqueConstraint("person_id", name="companies_person_id_unique"),
        Index("companies_person_id_idx", "person_id"),
        Index("companies_access_status_idx", "access_status"),
        Index("companies_contract_accepted_at_idx", "contract_accepted_at"),
        Index("companies_activated_at_idx", "activated_at"),
        Index("companies_activation_sent_at_idx", "activation_sent_at"),
        # Index("companies_metadata_fulltext", "metadata", postgresql_using="gin"),  # Disabled due to GIN index issue
        # Index("companies_settings_fulltext", "settings", postgresql_using="gin"),  # Disabled due to GIN index issue
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    person_id = Column(
        BigInteger, ForeignKey("master.people.id"), nullable=True, unique=True
    )
    settings = Column(JSON)
    metadata_ = Column("metadata", JSON)
    display_order = Column(Integer, default=0)

    # Company activation fields
    access_status = Column(String(20), default="pending_contract")
    contract_terms_version = Column(String(10), nullable=True)
    contract_accepted_at = Column(DateTime, nullable=True)
    contract_accepted_by = Column(String(255), nullable=True)
    contract_ip_address = Column(String(45), nullable=True)
    activation_sent_at = Column(DateTime, nullable=True)
    activation_sent_to = Column(String(255), nullable=True)
    activated_at = Column(DateTime, nullable=True)
    activated_by_user_id = Column(
        BigInteger, ForeignKey("master.users.id"), nullable=True
    )

    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    deleted_at = Column(DateTime)

    # Relationships
    people = relationship("People", back_populates="company", foreign_keys=[person_id])
    establishments = relationship("Establishments", back_populates="company")
    users = relationship(
        "User", back_populates="company", foreign_keys="[User.company_id]"
    )
    activated_by_user = relationship(
        "User", foreign_keys=[activated_by_user_id], uselist=False
    )

    # B2B Billing relationships
    subscriptions = relationship(
        "CompanySubscription", back_populates="company", cascade="all, delete-orphan"
    )
    proteamcare_invoices = relationship(
        "ProTeamCareInvoice", back_populates="company", cascade="all, delete-orphan"
    )


class Establishments(Base):
    __tablename__ = "establishments"
    __table_args__ = (
        CheckConstraint(
            "type IN ('matriz', 'filial', 'unidade', 'posto')",
            name="establishments_type_check",
        ),
        CheckConstraint(
            "category IN ('clinica', 'hospital', 'laboratorio', 'farmacia', 'consultorio', 'upa', 'ubs', 'outro')",
            name="establishments_category_check",
        ),
        UniqueConstraint(
            "company_id", "code", name="establishments_company_code_unique"
        ),
        UniqueConstraint(
            "company_id", "display_order", name="establishments_company_display_unique"
        ),
        Index("establishments_company_idx", "company_id"),
        Index("establishments_person_idx", "person_id"),
        Index("establishments_active_idx", "is_active"),
        Index("establishments_principal_idx", "is_principal"),
        Index("establishments_type_idx", "type"),
        Index("establishments_category_idx", "category"),
        Index("establishments_display_order_idx", "company_id", "display_order"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    person_id = Column(BigInteger, ForeignKey("master.people.id"), nullable=False)
    company_id = Column(BigInteger, ForeignKey("master.companies.id"), nullable=False)
    code = Column(String(50), nullable=False)
    type = Column(String(20), nullable=True)  # Corrigido: banco permite NULL
    category = Column(String(30), nullable=True)  # Corrigido: banco permite NULL
    is_active = Column(Boolean, nullable=False, default=True)
    is_principal = Column(Boolean, nullable=False, default=False)
    display_order = Column(Integer, nullable=False, default=0)
    settings = Column(JSON, nullable=True)
    meta_data = Column("metadata", JSON, nullable=True)
    operating_hours = Column(JSON, nullable=True)
    service_areas = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    person = relationship("People", foreign_keys=[person_id])
    company = relationship(
        "Company", back_populates="establishments", foreign_keys=[company_id]
    )


class Phone(Base):
    __tablename__ = "phones"
    __table_args__ = (
        CheckConstraint(
            "type IN ('landline', 'mobile', 'whatsapp', 'commercial', 'emergency', 'fax')",
            name="phones_type_check",
        ),
        CheckConstraint(
            "line_type IN ('prepaid', 'postpaid', 'corporate')",
            name="phones_line_type_check",
        ),
        CheckConstraint(
            "contact_priority >= 1 AND contact_priority <= 10",
            name="phones_contact_priority_check",
        ),
        Index("phones_phoneable_type_id_idx", "phoneable_type", "phoneable_id"),
        Index("phones_company_idx", "company_id"),
        Index("phones_whatsapp_idx", "is_whatsapp"),
        Index("phones_principal_idx", "is_principal"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    phoneable_type = Column(String(50), nullable=False, default="App\\Models\\People")
    phoneable_id = Column(BigInteger, ForeignKey("master.people.id"), nullable=False)
    company_id = Column(BigInteger, ForeignKey("master.companies.id"), nullable=False)

    # Phone details
    country_code = Column(String(3), default="55")
    number = Column(String(11), nullable=False)
    extension = Column(String(10))
    type = Column(String(20), nullable=False, default="mobile")
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
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    deleted_at = Column(DateTime)

    # Relationships
    people = relationship("People", back_populates="phones")


class Email(Base):
    __tablename__ = "emails"
    __table_args__ = (
        CheckConstraint(
            "type IN ('personal', 'work', 'billing', 'contact')",
            name="emails_type_check",
        ),
        Index("emails_emailable_type_id_idx", "emailable_type", "emailable_id"),
        Index("emails_email_address_idx", "email_address"),
        Index("emails_principal_idx", "is_principal"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    emailable_type = Column(String(50), nullable=False, default="App\\Models\\People")
    emailable_id = Column(BigInteger, ForeignKey("master.people.id"), nullable=False)

    # Email details
    email_address = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False, default="work")
    is_principal = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    verified_at = Column(DateTime)

    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    deleted_at = Column(DateTime)

    # Relationships
    people = relationship("People", back_populates="emails")


class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = (
        CheckConstraint(
            "type IN ('residential', 'commercial', 'correspondence', 'billing', 'delivery')",
            name="addresses_type_check",
        ),
        CheckConstraint(
            "access_difficulty IN ('easy', 'medium', 'hard', 'unknown')",
            name="addresses_access_difficulty_check",
        ),
        CheckConstraint(
            "quality_score >= 0 AND quality_score <= 100",
            name="addresses_quality_score_check",
        ),
        Index(
            "addresses_addressable_type_id_idx", "addressable_type", "addressable_id"
        ),
        Index("addresses_city_state_idx", "city", "state"),
        Index("addresses_zip_code_idx", "zip_code"),
        Index("addresses_coordinates_idx", "latitude", "longitude"),
        Index("addresses_principal_idx", "is_principal"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    addressable_type = Column(String(50), nullable=False, default="App\\Models\\People")
    addressable_id = Column(BigInteger, ForeignKey("master.people.id"), nullable=False)

    # Address details
    street = Column(String(255), nullable=False)
    number = Column(String(20), nullable=True)  # Permitir valores nulos
    details = Column(String(100))
    neighborhood = Column(String(100), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(2), nullable=False)
    zip_code = Column(String(10), nullable=False)
    country = Column(String(2), default="BR")
    type = Column(String(20), nullable=False, default="commercial")
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
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    deleted_at = Column(DateTime)

    # Relationships
    people = relationship("People", back_populates="addresses")


class Menu(Base):
    """Model ORM otimizado para Menus Dinâmicos"""

    __tablename__ = "menus"
    __table_args__ = (
        CheckConstraint(
            "menu_type IN ('folder', 'page', 'external_link', 'separator')",
            name="menus_type_check",
        ),
        CheckConstraint(
            "status IN ('active', 'inactive', 'draft')", name="menus_status_check"
        ),
        CheckConstraint("level >= 0 AND level <= 4", name="menus_level_check"),
        CheckConstraint("sort_order >= 0", name="menus_sort_order_check"),
        # Índices otimizados para performance
        Index("menus_parent_sort_idx", "parent_id", "sort_order"),
        Index("menus_hierarchy_idx", "level", "parent_id", "sort_order"),
        Index("menus_slug_parent_idx", "slug", "parent_id"),
        Index("menus_permission_idx", "permission_name"),
        Index("menus_status_visible_idx", "status", "is_visible", "visible_in_menu"),
        Index("menus_context_idx", "company_specific", "establishment_specific"),
        # Index("menus_fulltext_idx", "full_path_name", postgresql_using="gin"),  # Disabled due to GIN index issue
        # Constraint de slug único por nível
        UniqueConstraint("slug", "parent_id", name="menus_slug_parent_unique"),
        {"schema": "master"},
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
    menu_type = Column(String(20), nullable=False, default="page")
    status = Column(String(20), nullable=False, default="active")

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
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(
        BigInteger, nullable=True
    )  # FK para users será adicionada posteriormente
    updated_by = Column(
        BigInteger, nullable=True
    )  # FK para users será adicionada posteriormente

    # Relationships
    parent = relationship("Menu", remote_side=[id], back_populates="children")
    children = relationship(
        "Menu", back_populates="parent", cascade="all, delete-orphan"
    )


# =====================================
# SPRINT 1: FOUNDATION & SECURITY
# =====================================


class User(Base):
    """Modelo de usuários do sistema"""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "context_type IN ('company', 'establishment', 'client')",
            name="users_context_type_check",
        ),
        CheckConstraint(
            "status IN ('active', 'inactive', 'pending', 'suspended', 'blocked')",
            name="users_status_check",
        ),
        Index("users_person_id_idx", "person_id"),
        Index("users_company_idx", "company_id"),
        Index("users_establishment_id_idx", "establishment_id"),
        Index("users_company_email_idx", "company_id", "email_address"),
        Index("users_email_idx", "email_address"),
        Index("users_active_idx", "is_active"),
        Index("users_context_type_idx", "context_type"),
        Index("users_status_idx", "status"),
        Index("users_activation_token_idx", "activation_token"),
        Index("users_password_reset_token_idx", "password_reset_token"),
        Index("users_invited_by_idx", "invited_by_user_id"),
        UniqueConstraint(
            "company_id", "email_address", name="users_company_email_unique"
        ),
        {"schema": "master"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("master.people.id"), nullable=False
    )
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("master.companies.id"), nullable=False
    )
    establishment_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("master.establishments.id"), nullable=True
    )
    email_address: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime, nullable=True
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    remember_token: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, default=True
    )
    is_system_admin: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, default=False
    )

    # Novos campos para gestão de contexto e ativação
    context_type: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default="establishment"
    )
    status: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default="active"
    )
    activation_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    activation_expires_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime, nullable=True
    )
    password_reset_token: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    password_reset_expires_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime, nullable=True
    )
    invited_by_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("master.users.id"), nullable=True
    )
    invited_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    activated_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)

    preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    notification_settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    two_factor_secret: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    two_factor_recovery_codes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    last_login_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    password_changed_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime, nullable=True, default=func.now()
    )
    updated_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime, nullable=True, default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    person = relationship("People", back_populates="user")
    company = relationship("Company", back_populates="users", foreign_keys=[company_id])
    establishment = relationship("Establishments", foreign_keys=[establishment_id])
    invited_by = relationship(
        "User", remote_side=[id], foreign_keys=[invited_by_user_id]
    )
    user_roles = relationship(
        "UserRole",
        foreign_keys="[UserRole.user_id]",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Role(Base):
    """Modelo de perfis/roles do sistema"""

    __tablename__ = "roles"
    __table_args__ = (
        CheckConstraint(
            "context_type IN ('system', 'company', 'establishment')",
            name="roles_context_type_check",
        ),
        Index("roles_name_idx", "name"),
        Index("roles_level_idx", "level"),
        Index("roles_context_idx", "context_type"),
        UniqueConstraint("name", name="roles_name_unique"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(125), nullable=False, unique=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    level = Column(Integer, nullable=False, default=0)
    context_type = Column(String(255), nullable=False, default="establishment")
    is_active = Column(Boolean, nullable=True, default=True)
    is_system_role = Column(Boolean, nullable=True, default=False)
    settings = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=True, default=func.now())
    updated_at = Column(
        DateTime, nullable=True, default=func.now(), onupdate=func.now()
    )

    # Relationships
    role_permissions = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
    )
    user_roles = relationship("UserRole", back_populates="role")


class Permission(Base):
    """Modelo de permissões granulares"""

    __tablename__ = "permissions"
    __table_args__ = (
        CheckConstraint(
            "context_level IN ('system', 'company', 'establishment')",
            name="permissions_context_level_check",
        ),
        Index("permissions_name_idx", "name"),
        Index("permissions_module_idx", "module"),
        Index("permissions_context_idx", "context_level"),
        UniqueConstraint("name", name="permissions_name_unique"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(125), nullable=False, unique=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    module = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    resource = Column(String(50), nullable=False)
    context_level = Column(String(255), nullable=False, default="establishment")
    is_active = Column(Boolean, nullable=True, default=True)
    created_at = Column(DateTime, nullable=True, default=func.now())
    updated_at = Column(
        DateTime, nullable=True, default=func.now(), onupdate=func.now()
    )

    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission")


class UserRole(Base):
    """Relacionamento usuário-perfil com contexto"""

    __tablename__ = "user_roles"
    __table_args__ = (
        CheckConstraint(
            "context_type IN ('system', 'company', 'establishment')",
            name="user_roles_context_type_check",
        ),
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended', 'expired')",
            name="user_roles_status_check",
        ),
        Index("user_roles_user_idx", "user_id"),
        Index("user_roles_role_idx", "role_id"),
        Index("user_roles_context_idx", "context_type", "context_id"),
        Index("user_roles_status_idx", "status"),
        UniqueConstraint(
            "user_id", "role_id", "context_type", "context_id", name="user_roles_unique"
        ),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("master.users.id"), nullable=False)
    role_id = Column(BigInteger, ForeignKey("master.roles.id"), nullable=False)
    context_type = Column(String(255), nullable=False)
    context_id = Column(BigInteger, nullable=False)
    status = Column(String(255), nullable=False, default="active")
    assigned_by_user_id = Column(
        BigInteger, ForeignKey("master.users.id"), nullable=True
    )
    assigned_at = Column(DateTime, nullable=True, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True, default=func.now())
    updated_at = Column(
        DateTime, nullable=True, default=func.now(), onupdate=func.now()
    )
    deleted_at = Column(DateTime, nullable=True)

    # Relationships - especificar foreign_keys explicitamente
    user = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    assigned_by = relationship("User", foreign_keys=[assigned_by_user_id])


class RolePermission(Base):
    """Relacionamento perfil-permissão"""

    __tablename__ = "role_permissions"
    __table_args__ = (
        Index("role_permissions_role_idx", "role_id"),
        Index("role_permissions_permission_idx", "permission_id"),
        UniqueConstraint("role_id", "permission_id", name="role_permissions_unique"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    role_id = Column(BigInteger, ForeignKey("master.roles.id"), nullable=False)
    permission_id = Column(
        BigInteger, ForeignKey("master.permissions.id"), nullable=False
    )
    granted_by_user_id = Column(
        BigInteger, ForeignKey("master.users.id"), nullable=True
    )
    granted_at = Column(DateTime, nullable=True, default=func.now())

    # Relationships
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
    granted_by = relationship("User", foreign_keys=[granted_by_user_id])


# =====================================
# SPRINT 2: BUSINESS CORE
# =====================================


class Professional(Base):
    """Modelo de profissionais de saúde"""

    __tablename__ = "professionals"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended', 'terminated')",
            name="professionals_status_check",
        ),
        Index("professionals_pf_person_idx", "pf_person_id"),
        Index("professionals_pj_person_idx", "pj_person_id"),
        Index("professionals_establishment_idx", "establishment_id"),
        Index("professionals_status_idx", "status"),
        Index("professionals_code_idx", "professional_code"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    pf_person_id = Column(
        BigInteger, ForeignKey("master.people.id"), nullable=False
    )  # Pessoa física
    pj_person_id = Column(
        BigInteger, ForeignKey("master.people.id"), nullable=True
    )  # Pessoa jurídica (opcional)
    establishment_id = Column(
        BigInteger, ForeignKey("master.establishments.id"), nullable=False
    )
    professional_code = Column(String(50), nullable=True)
    status = Column(String(255), nullable=False, default="active")
    specialties = Column(JSON, nullable=True)  # Array de especialidades
    admission_date = Column(
        DateTime, nullable=True
    )  # Date no banco, mas DateTime funciona
    termination_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True, default=func.now())
    updated_at = Column(
        DateTime, nullable=True, default=func.now(), onupdate=func.now()
    )
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    pf_person = relationship("People", foreign_keys=[pf_person_id])
    pj_person = relationship("People", foreign_keys=[pj_person_id])
    establishment = relationship("Establishments")


class UserEstablishment(Base):
    """Relacionamento usuário-estabelecimento (contexto)"""

    __tablename__ = "user_establishments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended', 'expired')",
            name="user_establishments_status_check",
        ),
        Index("user_establishments_user_idx", "user_id"),
        Index("user_establishments_establishment_idx", "establishment_id"),
        Index("user_establishments_role_idx", "role_id"),
        Index("user_establishments_status_idx", "status"),
        Index("user_establishments_primary_idx", "is_primary"),
        UniqueConstraint(
            "user_id", "establishment_id", name="user_establishments_unique"
        ),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("master.users.id"), nullable=False)
    establishment_id = Column(
        BigInteger, ForeignKey("master.establishments.id"), nullable=False
    )
    role_id = Column(BigInteger, ForeignKey("master.roles.id"), nullable=True)
    is_primary = Column(Boolean, nullable=True, default=False)
    status = Column(String(255), nullable=False, default="active")
    assigned_by_user_id = Column(
        BigInteger, ForeignKey("master.users.id"), nullable=True
    )
    assigned_at = Column(DateTime, nullable=True, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    permissions = Column(
        JSON, nullable=True
    )  # Permissões específicas para este contexto
    created_at = Column(DateTime, nullable=True, default=func.now())
    updated_at = Column(
        DateTime, nullable=True, default=func.now(), onupdate=func.now()
    )
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    establishment = relationship("Establishments")
    role = relationship("Role")
    assigned_by = relationship("User", foreign_keys=[assigned_by_user_id])


class Session(Base):
    """Sessões do sistema"""

    __tablename__ = "sessions"
    __table_args__ = (
        Index("sessions_id_idx", "id"),
        Index("sessions_last_activity_idx", "last_activity"),
        {"schema": "master"},
    )

    id = Column(String(255), primary_key=True)  # Session ID como string
    user_id = Column(BigInteger, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(Text, nullable=True)
    payload = Column(Text, nullable=False)
    last_activity = Column(Integer, nullable=False)  # Unix timestamp


class UserSession(Base):
    """Sessões específicas por usuário com contexto"""

    __tablename__ = "user_sessions"
    __table_args__ = (
        Index("user_sessions_user_idx", "user_id"),
        Index("user_sessions_token_idx", "session_token"),
        Index("user_sessions_active_idx", "is_active"),
        Index("user_sessions_expires_idx", "expires_at"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("master.users.id"), nullable=False)
    session_token = Column(String(255), nullable=False, unique=True)

    # Context information
    active_context_type = Column(String(50), nullable=True, default="establishment")
    active_context_id = Column(BigInteger, nullable=True)
    active_role_id = Column(BigInteger, ForeignKey("master.roles.id"), nullable=True)

    # Impersonation support
    original_user_id = Column(BigInteger, ForeignKey("master.users.id"), nullable=True)
    impersonated_user_id = Column(
        BigInteger, ForeignKey("master.users.id"), nullable=True
    )
    impersonation_reason = Column(String(255), nullable=True)

    # Session management
    is_active = Column(Boolean, nullable=False, default=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    last_activity_at = Column(DateTime, nullable=True, default=func.now())
    expires_at = Column(DateTime, nullable=True)

    # Audit fields
    created_at = Column(DateTime, nullable=True, default=func.now())
    updated_at = Column(
        DateTime, nullable=True, default=func.now(), onupdate=func.now()
    )
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    active_role = relationship("Role")
    original_user = relationship("User", foreign_keys=[original_user_id])
    impersonated_user = relationship("User", foreign_keys=[impersonated_user_id])


class Client(Base):
    """Modelo de clientes"""

    __tablename__ = "clients"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'on_hold', 'archived')",
            name="clients_status_check",
        ),
        Index("clients_establishment_id_index", "establishment_id"),
        Index("clients_person_id_index", "person_id"),
        Index("clients_status_index", "status"),
        Index("clients_deleted_at_index", "deleted_at"),
        UniqueConstraint(
            "establishment_id",
            "client_code",
            name="clients_establishment_id_client_code_unique",
        ),
        UniqueConstraint(
            "establishment_id",
            "person_id",
            name="clients_establishment_id_person_id_unique",
        ),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    person_id = Column(BigInteger, ForeignKey("master.people.id"), nullable=False)
    establishment_id = Column(
        BigInteger, ForeignKey("master.establishments.id"), nullable=False
    )
    client_code = Column(String(50), nullable=True)
    status = Column(String(255), nullable=False, default="active")

    # Audit fields
    created_at = Column(DateTime, nullable=True, default=func.now())
    updated_at = Column(
        DateTime, nullable=True, default=func.now(), onupdate=func.now()
    )
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    person = relationship("People", back_populates="clients")
    establishment = relationship("Establishments", back_populates="clients")
    contracts = relationship("Contract", back_populates="client")


# Adicionar relacionamento inverso em People
People.user = relationship("User", back_populates="person", uselist=False)

# Adicionar novos relacionamentos
User.user_establishments = relationship(
    "UserEstablishment",
    foreign_keys="UserEstablishment.user_id",
    back_populates="user",
    cascade="all, delete-orphan",
)
User.sessions = relationship(
    "UserSession",
    foreign_keys="UserSession.user_id",
    back_populates="user",
    cascade="all, delete-orphan",
)
Establishments.professionals = relationship(
    "Professional", back_populates="establishment", cascade="all, delete-orphan"
)
Establishments.clients = relationship(
    "Client", back_populates="establishment", cascade="all, delete-orphan"
)
People.clients = relationship(
    "Client", back_populates="person", cascade="all, delete-orphan"
)
Establishments.user_establishments = relationship(
    "UserEstablishment", back_populates="establishment", cascade="all, delete-orphan"
)


# =============================
# HOME CARE CONTRACT MODELS
# =============================


class ServicesCatalog(Base):
    """Catálogo de serviços home care"""

    __tablename__ = "services_catalog"
    __table_args__ = (
        CheckConstraint(
            "service_category IN ('ENFERMAGEM', 'FISIOTERAPIA', 'MEDICINA', 'NUTRIÇÃO', 'PSICOLOGIA', 'FONOAUDIOLOGIA', 'TERAPIA_OCUPACIONAL', 'EQUIPAMENTO')",
            name="services_catalog_category_check",
        ),
        CheckConstraint(
            "service_type IN ('VISITA', 'PROCEDIMENTO', 'MEDICAÇÃO', 'EQUIPAMENTO', 'CONSULTA', 'TERAPIA', 'EXAME', 'LOCAÇÃO')",
            name="services_catalog_type_check",
        ),
        CheckConstraint(
            "billing_unit IN ('UNIT', 'HOUR', 'DAY', 'WEEK', 'MONTH', 'SESSION')",
            name="services_catalog_billing_unit_check",
        ),
        CheckConstraint(
            "status IN ('active', 'inactive', 'draft')",
            name="services_catalog_status_check",
        ),
        UniqueConstraint("service_code", name="services_catalog_code_unique"),
        Index("services_catalog_category_idx", "service_category"),
        Index("services_catalog_type_idx", "service_type"),
        Index("services_catalog_status_idx", "status"),
        Index("services_catalog_code_idx", "service_code"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_code = Column(String(20), nullable=False)
    service_name = Column(String(100), nullable=False)
    service_category = Column(String(50), nullable=False)
    service_type = Column(String(30), nullable=False)

    # Características do Serviço
    requires_prescription = Column(Boolean, default=False)
    requires_specialist = Column(Boolean, default=False)
    home_visit_required = Column(Boolean, default=True)

    # Valores e Controle
    default_unit_value = Column(Numeric(10, 2))
    billing_unit = Column(String(20), default="UNIT")

    # Regulamentações
    anvisa_regulated = Column(Boolean, default=False)
    requires_authorization = Column(Boolean, default=False)

    # Descrição e instruções
    description = Column(Text)
    instructions = Column(Text)
    contraindications = Column(Text)

    # Status
    status = Column(String(20), default="active")

    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )


class Contract(Base):
    """Contratos home care"""

    __tablename__ = "contracts"
    __table_args__ = (
        CheckConstraint(
            "contract_type IN ('INDIVIDUAL', 'CORPORATIVO', 'EMPRESARIAL')",
            name="contracts_type_check",
        ),
        CheckConstraint(
            "control_period IN ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY')",
            name="contracts_control_period_check",
        ),
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended', 'cancelled', 'expired')",
            name="contracts_status_check",
        ),
        UniqueConstraint("contract_number", name="contracts_number_unique"),
        Index("contracts_client_id_idx", "client_id"),
        Index("contracts_status_idx", "status"),
        Index("contracts_start_date_idx", "start_date"),
        Index("contracts_number_idx", "contract_number"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    client_id = Column(BigInteger, ForeignKey("master.clients.id"), nullable=False)
    contract_number = Column(String(50), nullable=False)
    contract_type = Column(String(20), nullable=False)

    # Controle de Vidas
    lives_contracted = Column(Integer, nullable=False, default=1)
    lives_minimum = Column(Integer)  # tolerância mínima
    lives_maximum = Column(Integer)  # tolerância máxima

    # Flexibilidade
    allows_substitution = Column(Boolean, default=False)
    control_period = Column(String(10), default="MONTHLY")

    # Dados do Contrato
    plan_name = Column(String(100), nullable=False)
    monthly_value = Column(Numeric(10, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)

    # Localização (múltiplos endereços)
    service_address_type = Column(String(10), default="PATIENT")
    service_addresses = Column(JSON)

    # Status
    status = Column(String(20), default="active")

    # Observações
    notes = Column(Text)  # Campo para observações do contrato

    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    created_by = Column(BigInteger, ForeignKey("master.users.id"))
    updated_by = Column(BigInteger, ForeignKey("master.users.id"))

    # Relationships
    client = relationship("Client", back_populates="contracts")
    lives = relationship(
        "ContractLive", back_populates="contract", overlaps="contract_lives"
    )
    services = relationship(
        "ContractService", back_populates="contract", overlaps="contract_services"
    )
    billing_schedule = relationship(
        "ContractBillingSchedule", back_populates="contract", uselist=False
    )
    invoices = relationship(
        "ContractInvoice", back_populates="contract", cascade="all, delete-orphan"
    )


class ContractLive(Base):
    """Vidas vinculadas aos contratos"""

    __tablename__ = "contract_lives"
    __table_args__ = (
        CheckConstraint(
            "relationship_type IN ('TITULAR', 'DEPENDENTE', 'FUNCIONARIO', 'BENEFICIARIO')",
            name="contract_lives_relationship_check",
        ),
        CheckConstraint(
            "status IN ('active', 'inactive', 'substituted', 'cancelled')",
            name="contract_lives_status_check",
        ),
        UniqueConstraint(
            "contract_id",
            "person_id",
            "start_date",
            name="contract_lives_unique_period",
        ),
        Index("contract_lives_contract_id_idx", "contract_id"),
        Index("contract_lives_person_id_idx", "person_id"),
        Index("contract_lives_status_idx", "status"),
        Index("contract_lives_date_range_idx", "start_date", "end_date"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contract_id = Column(BigInteger, ForeignKey("master.contracts.id"), nullable=False)
    person_id = Column(BigInteger, ForeignKey("master.people.id"), nullable=False)

    # Período de Vinculação
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)  # NULL = ativa

    # Tipo de Relação
    relationship_type = Column(String(20), nullable=False)

    # Status
    status = Column(String(20), default="active")
    substitution_reason = Column(String(100))

    # Localização Específica
    primary_service_address = Column(JSON)

    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    created_by = Column(BigInteger, ForeignKey("master.users.id"))

    # Relationships
    contract = relationship("Contract", back_populates="lives")


class ContractService(Base):
    """Serviços permitidos no contrato"""

    __tablename__ = "contract_services"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended')",
            name="contract_services_status_check",
        ),
        UniqueConstraint(
            "contract_id",
            "service_id",
            "start_date",
            name="contract_services_unique_period",
        ),
        Index("contract_services_contract_id_idx", "contract_id"),
        Index("contract_services_service_id_idx", "service_id"),
        Index("contract_services_status_idx", "status"),
        Index("contract_services_date_range_idx", "start_date", "end_date"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contract_id = Column(BigInteger, ForeignKey("master.contracts.id"), nullable=False)
    service_id = Column(
        BigInteger, ForeignKey("master.services_catalog.id"), nullable=False
    )

    # Limites e Controles do Contrato
    monthly_limit = Column(Integer)  # quantidade máxima por mês por vida
    daily_limit = Column(Integer)  # quantidade máxima por dia por vida
    annual_limit = Column(Integer)  # limite anual por vida

    # Valores Específicos do Contrato
    unit_value = Column(Numeric(10, 2))  # valor específico para este contrato
    requires_pre_authorization = Column(Boolean, default=False)

    # Período de Validade
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)

    # Status
    status = Column(String(20), default="active")

    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_by = Column(BigInteger, ForeignKey("master.users.id"))

    # Relationships
    contract = relationship("Contract", back_populates="services")


class ContractLifeService(Base):
    """Serviços específicos por vida"""

    __tablename__ = "contract_life_services"
    __table_args__ = (
        CheckConstraint(
            "priority_level IN ('URGENT', 'HIGH', 'NORMAL', 'LOW')",
            name="contract_life_services_priority_check",
        ),
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended')",
            name="contract_life_services_status_check",
        ),
        UniqueConstraint(
            "contract_life_id",
            "service_id",
            "start_date",
            name="contract_life_services_unique_period",
        ),
        Index("contract_life_services_contract_life_id_idx", "contract_life_id"),
        Index("contract_life_services_service_id_idx", "service_id"),
        Index("contract_life_services_status_idx", "status"),
        Index("contract_life_services_authorized_idx", "is_authorized"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contract_life_id = Column(
        BigInteger, ForeignKey("master.contract_lives.id"), nullable=False
    )
    service_id = Column(
        BigInteger, ForeignKey("master.services_catalog.id"), nullable=False
    )

    # Autorização Individual
    is_authorized = Column(Boolean, default=True)
    authorization_date = Column(Date)
    authorized_by = Column(
        BigInteger, ForeignKey("master.users.id")
    )  # médico responsável

    # Limites Individuais (sobrepõem os do contrato)
    monthly_limit_override = Column(Integer)
    daily_limit_override = Column(Integer)
    annual_limit_override = Column(Integer)

    # Dados Médicos
    medical_indication = Column(Text)
    contraindications = Column(Text)
    special_instructions = Column(Text)
    priority_level = Column(String(20), default="NORMAL")

    # Período de Autorização
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)

    # Status
    status = Column(String(20), default="active")

    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    created_by = Column(BigInteger, ForeignKey("master.users.id"))


# Classe ServiceExecution removida - definição duplicada existe mais abaixo


# =============================
# RELATIONSHIPS FOR CONTRACT MODELS
# =============================

# Contract relationships
Contract.client = relationship("Client", back_populates="contracts")
Contract.contract_lives = relationship(
    "ContractLive", back_populates="contract", cascade="all, delete-orphan"
)
Contract.contract_services = relationship(
    "ContractService", back_populates="contract", cascade="all, delete-orphan"
)

# ContractLive relationships
ContractLive.contract = relationship("Contract", back_populates="contract_lives")
ContractLive.person = relationship("People", back_populates="contract_lives")
ContractLive.life_services = relationship(
    "ContractLifeService", back_populates="contract_life", cascade="all, delete-orphan"
)
# ContractLive.service_executions = relationship("ServiceExecution", back_populates="contract_life", cascade="all, delete-orphan")  # Comentado - ServiceExecution antiga removida

# ContractService relationships
ContractService.contract = relationship("Contract", back_populates="contract_services")
ContractService.service = relationship(
    "ServicesCatalog", back_populates="contract_services"
)

# ContractLifeService relationships
ContractLifeService.contract_life = relationship(
    "ContractLive", back_populates="life_services"
)
ContractLifeService.service = relationship(
    "ServicesCatalog", back_populates="life_services"
)

# ServiceExecution relationships - COMENTADO: ServiceExecution antiga foi removida, nova definição existe mais abaixo
# ServiceExecution.contract_life = relationship("ContractLive", back_populates="service_executions")
# ServiceExecution.service = relationship("ServicesCatalog", back_populates="service_executions")
# ServiceExecution.professional = relationship("User", foreign_keys=[ServiceExecution.professional_id])

# ServicesCatalog relationships
ServicesCatalog.contract_services = relationship(
    "ContractService", back_populates="service"
)
ServicesCatalog.life_services = relationship(
    "ContractLifeService", back_populates="service"
)
# ServicesCatalog.service_executions = relationship("ServiceExecution", back_populates="service")  # Comentado - ServiceExecution antiga removida


# Medical Authorization Models
class MedicalAuthorization(Base):
    """Autorizações médicas para serviços"""

    __tablename__ = "medical_authorizations"
    __table_args__ = {"schema": "master"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contract_life_id = Column(
        BigInteger, ForeignKey("master.contract_lives.id"), nullable=False
    )
    service_id = Column(
        BigInteger, ForeignKey("master.services_catalog.id"), nullable=False
    )
    doctor_id = Column(BigInteger, ForeignKey("master.users.id"), nullable=False)
    authorization_code = Column(String(50), nullable=False, unique=True)
    authorization_date = Column(Date, nullable=False)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=False)

    # Session limits
    sessions_authorized = Column(Integer)
    sessions_remaining = Column(Integer)
    monthly_limit = Column(Integer)
    weekly_limit = Column(Integer)
    daily_limit = Column(Integer)

    # Medical information
    medical_indication = Column(Text, nullable=False)
    contraindications = Column(Text)
    special_instructions = Column(Text)
    urgency_level = Column(String(20), default="NORMAL")
    requires_supervision = Column(Boolean, default=False)
    supervision_notes = Column(Text)
    diagnosis_cid = Column(String(10))
    diagnosis_description = Column(Text)
    treatment_goals = Column(Text)
    expected_duration_days = Column(Integer)

    # Renewal
    renewal_allowed = Column(Boolean, default=True)
    renewal_conditions = Column(Text)

    # Status
    status = Column(String(20), default="active")
    cancellation_reason = Column(Text)
    cancelled_at = Column(DateTime)
    cancelled_by = Column(BigInteger, ForeignKey("master.users.id"))

    # Audit
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    created_by = Column(BigInteger, ForeignKey("master.users.id"))
    updated_by = Column(BigInteger, ForeignKey("master.users.id"))

    # Relationships
    contract_life = relationship(
        "ContractLive", back_populates="medical_authorizations"
    )
    service = relationship("ServicesCatalog", back_populates="medical_authorizations")
    doctor = relationship("User", foreign_keys=[doctor_id])
    cancelled_by_user = relationship("User", foreign_keys=[cancelled_by])
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    renewals_as_original = relationship(
        "AuthorizationRenewal",
        foreign_keys="AuthorizationRenewal.original_authorization_id",
        back_populates="original_authorization",
    )
    renewals_as_new = relationship(
        "AuthorizationRenewal",
        foreign_keys="AuthorizationRenewal.new_authorization_id",
        back_populates="new_authorization",
    )
    history = relationship("AuthorizationHistory", back_populates="authorization")


class AuthorizationRenewal(Base):
    """Renovações de autorizações médicas"""

    __tablename__ = "authorization_renewals"
    __table_args__ = {"schema": "master"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    original_authorization_id = Column(
        BigInteger, ForeignKey("master.medical_authorizations.id"), nullable=False
    )
    new_authorization_id = Column(
        BigInteger, ForeignKey("master.medical_authorizations.id"), nullable=False
    )
    renewal_date = Column(Date, nullable=False)
    renewal_reason = Column(Text)
    changes_made = Column(Text)
    approved_by = Column(BigInteger, ForeignKey("master.users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    original_authorization = relationship(
        "MedicalAuthorization",
        foreign_keys=[original_authorization_id],
        back_populates="renewals_as_original",
    )
    new_authorization = relationship(
        "MedicalAuthorization",
        foreign_keys=[new_authorization_id],
        back_populates="renewals_as_new",
    )
    approved_by_user = relationship("User")


class AuthorizationHistory(Base):
    """Histórico de mudanças em autorizações"""

    __tablename__ = "authorization_history"
    __table_args__ = {"schema": "master"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    authorization_id = Column(
        BigInteger, ForeignKey("master.medical_authorizations.id"), nullable=False
    )
    action = Column(String(50), nullable=False)
    field_changed = Column(String(100))
    old_value = Column(Text)
    new_value = Column(Text)
    reason = Column(Text)
    performed_by = Column(BigInteger, ForeignKey("master.users.id"), nullable=False)
    performed_at = Column(DateTime, nullable=False, default=func.now())
    ip_address = Column(String(45))
    user_agent = Column(Text)

    # Relationships
    authorization = relationship("MedicalAuthorization", back_populates="history")
    performed_by_user = relationship("User")


# Add reverse relationships to existing models
Client.contracts = relationship(
    "Contract", back_populates="client", cascade="all, delete-orphan"
)
People.contract_lives = relationship(
    "ContractLive", back_populates="person", cascade="all, delete-orphan"
)

# Update ContractLive to include medical authorizations
ContractLive.medical_authorizations = relationship(
    "MedicalAuthorization", back_populates="contract_life", cascade="all, delete-orphan"
)

# Update ServicesCatalog to include medical authorizations
ServicesCatalog.medical_authorizations = relationship(
    "MedicalAuthorization", back_populates="service"
)


# === LIMITS CONTROL MODELS ===


class LimitsConfiguration(Base):
    """Configuração de limites automáticos"""

    __tablename__ = "limits_configuration"
    __table_args__ = {"schema": "master"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    limit_type = Column(String(20), nullable=False)  # sessions, financial, frequency
    entity_type = Column(
        String(20), nullable=False
    )  # authorization, contract, service, global
    entity_id = Column(BigInteger)  # ID da entidade (pode ser null para globais)
    limit_value = Column(Numeric(15, 2), nullable=False)
    limit_period = Column(String(20))  # daily, weekly, monthly
    description = Column(Text)
    override_allowed = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ServiceUsageTracking(Base):
    """Rastreamento de uso de serviços"""

    __tablename__ = "service_usage_tracking"
    __table_args__ = {"schema": "master"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    authorization_id = Column(
        BigInteger, ForeignKey("master.medical_authorizations.id"), nullable=False
    )
    sessions_used = Column(Integer, nullable=False)
    execution_date = Column(Date, nullable=False)
    executed_by = Column(BigInteger, ForeignKey("master.users.id"), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    authorization = relationship("MedicalAuthorization")
    executed_by_user = relationship("User")


class LimitsViolation(Base):
    """Violações de limites"""

    __tablename__ = "limits_violations"
    __table_args__ = {"schema": "master"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    authorization_id = Column(
        BigInteger, ForeignKey("master.medical_authorizations.id"), nullable=False
    )
    violation_type = Column(
        String(50), nullable=False
    )  # sessions_exceeded, financial_exceeded, etc
    attempted_value = Column(Numeric(15, 2), nullable=False)
    limit_value = Column(Numeric(15, 2), nullable=False)
    description = Column(Text, nullable=False)
    detected_by = Column(BigInteger, ForeignKey("master.users.id"), nullable=False)
    detected_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    authorization = relationship("MedicalAuthorization")
    detected_by_user = relationship("User")


class AlertsConfiguration(Base):
    """Configuração de alertas"""

    __tablename__ = "alerts_configuration"
    __table_args__ = {"schema": "master"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    alert_type = Column(
        String(30), nullable=False
    )  # limit_warning, expiry_warning, etc
    entity_type = Column(
        String(20), nullable=False
    )  # authorization, contract, service, global
    entity_id = Column(BigInteger)  # ID da entidade (pode ser null para globais)
    threshold_value = Column(Numeric(15, 2))
    threshold_percentage = Column(Numeric(5, 2))
    message_template = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AlertsLog(Base):
    """Log de alertas disparados"""

    __tablename__ = "alerts_log"
    __table_args__ = {"schema": "master"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    alert_config_id = Column(
        BigInteger, ForeignKey("master.alerts_configuration.id"), nullable=False
    )
    entity_id = Column(BigInteger, nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(
        String(20), nullable=False, default="medium"
    )  # low, medium, high, critical
    data = Column(JSON)  # Dados contextuais do alerta
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    alert_config = relationship("AlertsConfiguration")


# === SERVICE EXECUTION MODELS ===


class ServiceExecution(Base):
    """Execução de serviços home care"""

    __tablename__ = "service_executions"
    __table_args__ = {"schema": "master"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    authorization_id = Column(
        BigInteger, ForeignKey("master.medical_authorizations.id"), nullable=False
    )
    professional_id = Column(BigInteger, ForeignKey("master.users.id"), nullable=False)
    patient_id = Column(BigInteger, ForeignKey("master.users.id"), nullable=False)
    service_id = Column(
        BigInteger, ForeignKey("master.services_catalog.id"), nullable=False
    )
    execution_code = Column(String(30), nullable=False, unique=True)
    execution_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time)
    duration_minutes = Column(Integer)
    sessions_consumed = Column(Integer, nullable=False, default=1)
    location_type = Column(
        String(20), nullable=False
    )  # home, clinic, hospital, telemedicine
    address_id = Column(BigInteger, ForeignKey("master.addresses.id"))
    coordinates = Column(String(50))  # GPS coordinates
    status = Column(
        String(20), nullable=False, default="scheduled"
    )  # scheduled, in_progress, completed, cancelled, no_show
    pre_execution_notes = Column(Text)
    execution_notes = Column(Text)
    post_execution_notes = Column(Text)
    patient_signature = Column(Text)  # Base64 signature
    professional_signature = Column(Text)  # Base64 signature
    materials_used = Column(JSON)
    equipment_used = Column(JSON)
    complications = Column(Text)
    next_session_recommended = Column(Date)
    satisfaction_rating = Column(Integer)  # 1-5 scale
    satisfaction_comments = Column(Text)
    photos = Column(JSON)  # Array of photo metadata
    documents = Column(JSON)  # Array of document metadata
    billing_amount = Column(Numeric(10, 2))
    billing_status = Column(
        String(20), default="pending"
    )  # pending, approved, rejected, paid
    cancelled_reason = Column(Text)
    cancelled_by = Column(BigInteger, ForeignKey("master.users.id"))
    cancelled_at = Column(DateTime)
    created_by = Column(BigInteger, ForeignKey("master.users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_by = Column(BigInteger, ForeignKey("master.users.id"))
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    authorization = relationship("MedicalAuthorization")
    professional = relationship("User", foreign_keys=[professional_id])
    patient = relationship("User", foreign_keys=[patient_id])
    service = relationship("ServicesCatalog")
    address = relationship("Address")
    cancelled_by_user = relationship("User", foreign_keys=[cancelled_by])
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    checklists = relationship(
        "ExecutionChecklist", back_populates="execution", cascade="all, delete-orphan"
    )


class ProfessionalSchedule(Base):
    """Agenda dos profissionais"""

    __tablename__ = "professional_schedules"
    __table_args__ = {"schema": "master"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    professional_id = Column(BigInteger, ForeignKey("master.users.id"), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_available = Column(Boolean, nullable=False, default=True)
    location_preference = Column(String(20))  # home, clinic, any
    max_distance_km = Column(Integer)
    notes = Column(Text)
    created_by = Column(BigInteger, ForeignKey("master.users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_by = Column(BigInteger, ForeignKey("master.users.id"))
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    professional = relationship("User", foreign_keys=[professional_id])
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])


class ExecutionChecklist(Base):
    """Checklist de execução de serviços"""

    __tablename__ = "execution_checklists"
    __table_args__ = {"schema": "master"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    execution_id = Column(
        BigInteger, ForeignKey("master.service_executions.id"), nullable=False
    )
    checklist_type = Column(
        String(30), nullable=False
    )  # pre_execution, during_execution, post_execution
    item_code = Column(String(50), nullable=False)
    item_description = Column(String(200), nullable=False)
    is_required = Column(Boolean, nullable=False, default=True)
    is_completed = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime)
    completed_by = Column(BigInteger, ForeignKey("master.users.id"))
    notes = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.now())

    # Relationships
    execution = relationship("ServiceExecution", back_populates="checklists")
    completed_by_user = relationship("User")


# === AUTOMATED REPORTS MODELS ===


class AutomatedReport(Base):
    """Relatórios automáticos gerados"""

    __tablename__ = "automated_reports"
    __table_args__ = {"schema": "master"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    report_type = Column(
        String(30), nullable=False
    )  # monthly_contract, monthly_company, annual_summary
    company_id = Column(BigInteger, ForeignKey("master.companies.id"))
    contract_id = Column(BigInteger, ForeignKey("master.contracts.id"))
    report_year = Column(Integer, nullable=False)
    report_month = Column(Integer)  # NULL para relatórios anuais
    generated_at = Column(DateTime, nullable=False)
    report_data = Column(JSON, nullable=False)  # Dados completos do relatório
    file_path = Column(String(500))  # Caminho para arquivo PDF/Excel se gerado
    email_sent = Column(Boolean, default=False)  # Flag se foi enviado por email
    email_sent_at = Column(DateTime)
    recipients = Column(JSON)  # Lista de destinatários do email
    status = Column(
        String(20), default="generated"
    )  # generated, sent, archived, failed
    error_message = Column(Text)  # Mensagem de erro se falhou
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company")
    contract = relationship("Contract")


class ReportSchedule(Base):
    """Agendamentos para geração automática de relatórios"""

    __tablename__ = "report_schedules"
    __table_args__ = {"schema": "master"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    schedule_name = Column(String(100), nullable=False)
    schedule_type = Column(String(20), nullable=False)  # monthly, quarterly, annual
    company_id = Column(
        BigInteger, ForeignKey("master.companies.id")
    )  # NULL = todas as empresas
    contract_id = Column(
        BigInteger, ForeignKey("master.contracts.id")
    )  # NULL = todos os contratos da empresa
    report_types = Column(JSON, nullable=False)  # Tipos de relatório a gerar
    recipients = Column(JSON, nullable=False)  # Lista de emails destinatários
    is_active = Column(Boolean, nullable=False, default=True)
    next_execution = Column(DateTime, nullable=False)
    last_execution = Column(DateTime)
    execution_day = Column(Integer)  # Dia do mês para execução (1-31)
    execution_hour = Column(Integer, default=8)  # Hora de execução (0-23)
    timezone = Column(String(50), default="America/Sao_Paulo")
    created_by = Column(BigInteger, ForeignKey("master.users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_by = Column(BigInteger, ForeignKey("master.users.id"))
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company")
    contract = relationship("Contract")
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])


class ReportExecutionLog(Base):
    """Log de execução de relatórios"""

    __tablename__ = "report_execution_log"
    __table_args__ = {"schema": "master"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    schedule_id = Column(
        BigInteger, ForeignKey("master.report_schedules.id")
    )  # NULL para execuções manuais
    execution_type = Column(String(20), nullable=False)  # scheduled, manual, api
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    status = Column(String(20), nullable=False)  # running, completed, failed
    total_reports = Column(Integer, default=0)
    successful_reports = Column(Integer, default=0)
    failed_reports = Column(Integer, default=0)
    execution_summary = Column(JSON)  # Resumo detalhado da execução
    error_details = Column(Text)
    triggered_by = Column(
        BigInteger, ForeignKey("master.users.id")
    )  # User que iniciou execução manual

    # Relationships
    schedule = relationship("ReportSchedule")
    triggered_by_user = relationship("User")


# === BILLING SYSTEM MODELS ===


class ContractBillingSchedule(Base):
    """Agenda de faturamento para contratos"""

    __tablename__ = "contract_billing_schedules"
    __table_args__ = (
        CheckConstraint(
            "billing_cycle IN ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'SEMI_ANNUAL', 'ANNUAL')",
            name="contract_billing_schedules_cycle_check",
        ),
        CheckConstraint(
            "billing_day >= 1 AND billing_day <= 31",
            name="contract_billing_schedules_day_check",
        ),
        CheckConstraint(
            "billing_method IN ('recurrent', 'manual')",
            name="billing_method_check",
        ),
        UniqueConstraint(
            "contract_id", name="contract_billing_schedules_contract_unique"
        ),
        Index("contract_billing_schedules_contract_id_idx", "contract_id"),
        Index("contract_billing_schedules_next_billing_idx", "next_billing_date"),
        Index("contract_billing_schedules_is_active_idx", "is_active"),
        Index("contract_billing_schedules_billing_method_idx", "billing_method"),
        Index(
            "contract_billing_schedules_pagbank_subscription_idx",
            "pagbank_subscription_id",
        ),
        Index("contract_billing_schedules_pagbank_customer_idx", "pagbank_customer_id"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contract_id = Column(
        BigInteger,
        ForeignKey("master.contracts.id", ondelete="CASCADE"),
        nullable=False,
    )
    billing_cycle = Column(String(20), nullable=False, default="MONTHLY")
    billing_day = Column(Integer, nullable=False, default=1)
    next_billing_date = Column(Date, nullable=False)
    amount_per_cycle = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)

    # PagBank integration fields
    billing_method = Column(String(20), default="manual")
    pagbank_subscription_id = Column(String(100))
    pagbank_customer_id = Column(String(100))
    auto_fallback_enabled = Column(Boolean, default=True)
    last_attempt_date = Column(Date)
    attempt_count = Column(Integer, default=0)

    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    created_by = Column(BigInteger, ForeignKey("master.users.id"))

    # Relationships
    contract = relationship("Contract", back_populates="billing_schedule")
    created_by_user = relationship("User")


class ContractInvoice(Base):
    """Faturas de contratos"""

    __tablename__ = "contract_invoices"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pendente', 'enviada', 'paga', 'vencida', 'cancelada', 'em_atraso')",
            name="contract_invoices_status_check",
        ),
        CheckConstraint(
            "lives_count >= 0",
            name="contract_invoices_lives_count_check",
        ),
        CheckConstraint(
            "base_amount >= 0",
            name="contract_invoices_base_amount_check",
        ),
        CheckConstraint(
            "total_amount >= 0",
            name="contract_invoices_total_amount_check",
        ),
        UniqueConstraint("invoice_number", name="contract_invoices_number_unique"),
        Index("contract_invoices_contract_id_idx", "contract_id"),
        Index("contract_invoices_status_idx", "status"),
        Index("contract_invoices_due_date_idx", "due_date"),
        Index("contract_invoices_issued_date_idx", "issued_date"),
        Index(
            "contract_invoices_billing_period_idx",
            "billing_period_start",
            "billing_period_end",
        ),
        Index("contract_invoices_number_idx", "invoice_number"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    contract_id = Column(
        BigInteger,
        ForeignKey("master.contracts.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_number = Column(String(50), nullable=False)
    billing_period_start = Column(Date, nullable=False)
    billing_period_end = Column(Date, nullable=False)
    lives_count = Column(Integer, nullable=False)
    base_amount = Column(Numeric(10, 2), nullable=False)
    additional_services_amount = Column(Numeric(10, 2), default=0.00)
    discounts = Column(Numeric(10, 2), default=0.00)
    taxes = Column(Numeric(10, 2), default=0.00)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), nullable=False, default="pendente")
    due_date = Column(Date, nullable=False)
    issued_date = Column(Date, nullable=False, default=func.current_date())
    paid_date = Column(Date)
    payment_method = Column(String(50))
    payment_reference = Column(String(100))
    payment_notes = Column(Text)
    observations = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )
    created_by = Column(BigInteger, ForeignKey("master.users.id"))
    updated_by = Column(BigInteger, ForeignKey("master.users.id"))

    # Relationships
    contract = relationship("Contract", back_populates="invoices")
    receipts = relationship(
        "PaymentReceipt", back_populates="invoice", cascade="all, delete-orphan"
    )
    pagbank_transactions = relationship(
        "PagBankTransaction", back_populates="invoice", cascade="all, delete-orphan"
    )
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])


class PaymentReceipt(Base):
    """Comprovantes de pagamento"""

    __tablename__ = "payment_receipts"
    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('pendente', 'aprovado', 'rejeitado')",
            name="payment_receipts_verification_status_check",
        ),
        CheckConstraint(
            "file_size >= 0",
            name="payment_receipts_file_size_check",
        ),
        Index("payment_receipts_invoice_id_idx", "invoice_id"),
        Index("payment_receipts_verification_status_idx", "verification_status"),
        Index("payment_receipts_upload_date_idx", "upload_date"),
        Index("payment_receipts_uploaded_by_idx", "uploaded_by"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id = Column(
        BigInteger,
        ForeignKey("master.contract_invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(10))
    file_size = Column(BigInteger)
    upload_date = Column(DateTime, nullable=False, default=func.now())
    verification_status = Column(String(20), default="pendente")
    verified_by = Column(BigInteger, ForeignKey("master.users.id"))
    verified_at = Column(DateTime)
    notes = Column(Text)
    uploaded_by = Column(BigInteger, ForeignKey("master.users.id"))

    # Relationships
    invoice = relationship("ContractInvoice", back_populates="receipts")
    uploaded_by_user = relationship("User", foreign_keys=[uploaded_by])
    verified_by_user = relationship("User", foreign_keys=[verified_by])


class BillingAuditLog(Base):
    """Log de auditoria para operações de faturamento"""

    __tablename__ = "billing_audit_log"
    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('invoice', 'receipt', 'schedule')",
            name="billing_audit_log_entity_type_check",
        ),
        CheckConstraint(
            "action IN ('created', 'updated', 'deleted', 'status_changed')",
            name="billing_audit_log_action_check",
        ),
        Index("billing_audit_log_entity_idx", "entity_type", "entity_id"),
        Index("billing_audit_log_timestamp_idx", "timestamp"),
        Index("billing_audit_log_user_id_idx", "user_id"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(BigInteger, nullable=False)
    action = Column(String(20), nullable=False)
    old_values = Column(JSON)
    new_values = Column(JSON)
    user_id = Column(BigInteger, ForeignKey("master.users.id"))
    timestamp = Column(DateTime, nullable=False, default=func.now())
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    # Relationships
    user = relationship("User")


class PagBankTransaction(Base):
    """Transações PagBank para billing"""

    __tablename__ = "pagbank_transactions"
    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('recurrent', 'checkout')",
            name="pagbank_trans_type_check",
        ),
        CheckConstraint(
            "status IN ('pending', 'approved', 'declined', 'failed', 'cancelled')",
            name="pagbank_status_check",
        ),
        CheckConstraint(
            "amount >= 0",
            name="pagbank_amount_check",
        ),
        Index("pagbank_transactions_invoice_id_idx", "invoice_id"),
        Index("pagbank_transactions_status_idx", "status"),
        Index("pagbank_transactions_type_idx", "transaction_type"),
        Index(
            "pagbank_transactions_pagbank_transaction_id_idx", "pagbank_transaction_id"
        ),
        Index("pagbank_transactions_pagbank_charge_id_idx", "pagbank_charge_id"),
        Index("pagbank_transactions_created_at_idx", "created_at"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    invoice_id = Column(
        BigInteger,
        ForeignKey("master.contract_invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    transaction_type = Column(String(20), nullable=False)
    pagbank_transaction_id = Column(String(100))
    pagbank_charge_id = Column(String(100))
    status = Column(String(20), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(20))
    error_message = Column(Text)
    webhook_data = Column(JSON)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(
        DateTime, nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    invoice = relationship("ContractInvoice", back_populates="pagbank_transactions")


# =============================
# B2B BILLING MODELS (Pro Team Care)
# =============================


class SubscriptionPlan(Base):
    """Planos de assinatura do Pro Team Care"""

    __tablename__ = "subscription_plans"
    __table_args__ = (
        CheckConstraint(
            "monthly_price >= 0",
            name="subscription_plans_price_check",
        ),
        Index("subscription_plans_name_idx", "name"),
        Index("subscription_plans_is_active_idx", "is_active"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    description = Column(Text)
    monthly_price = Column(Numeric(10, 2), nullable=False)
    features = Column(JSON)
    max_users = Column(Integer)
    max_establishments = Column(Integer)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=True)

    # Relationships
    company_subscriptions = relationship("CompanySubscription", back_populates="plan")


class CompanySubscription(Base):
    """Assinaturas das empresas clientes"""

    __tablename__ = "company_subscriptions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'cancelled', 'suspended', 'expired')",
            name="company_subscriptions_status_check",
        ),
        CheckConstraint(
            "payment_method IN ('manual', 'recurrent')",
            name="company_subscriptions_payment_method_check",
        ),
        CheckConstraint(
            "billing_day >= 1 AND billing_day <= 31",
            name="company_subscriptions_billing_day_check",
        ),
        Index("company_subscriptions_company_id_idx", "company_id"),
        Index("company_subscriptions_plan_id_idx", "plan_id"),
        Index("company_subscriptions_status_idx", "status"),
        Index("company_subscriptions_payment_method_idx", "payment_method"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(
        BigInteger,
        ForeignKey("master.companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    plan_id = Column(
        BigInteger, ForeignKey("master.subscription_plans.id"), nullable=False
    )
    status = Column(String(20), nullable=False, default="active")
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    billing_day = Column(Integer, nullable=False, default=1)
    payment_method = Column(String(20), nullable=False, default="manual")
    pagbank_subscription_id = Column(String(100))
    auto_renew = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime)

    # Relationships
    company = relationship("Company", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="company_subscriptions")
    invoices = relationship("ProTeamCareInvoice", back_populates="subscription")


class ProTeamCareInvoice(Base):
    """Faturas do Pro Team Care para empresas clientes"""

    __tablename__ = "proteamcare_invoices"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'paid', 'overdue', 'cancelled')",
            name="proteamcare_invoices_status_check",
        ),
        CheckConstraint(
            "payment_method IN ('manual', 'recurrent')",
            name="proteamcare_invoices_payment_method_check",
        ),
        CheckConstraint(
            "amount >= 0",
            name="proteamcare_invoices_amount_check",
        ),
        UniqueConstraint("invoice_number", name="proteamcare_invoices_number_unique"),
        Index("proteamcare_invoices_company_id_idx", "company_id"),
        Index("proteamcare_invoices_subscription_id_idx", "subscription_id"),
        Index("proteamcare_invoices_status_idx", "status"),
        Index("proteamcare_invoices_due_date_idx", "due_date"),
        Index("proteamcare_invoices_invoice_number_idx", "invoice_number"),
        {"schema": "master"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(
        BigInteger,
        ForeignKey("master.companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    subscription_id = Column(
        BigInteger,
        ForeignKey("master.company_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_number = Column(String(50), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    billing_period_start = Column(Date, nullable=False)
    billing_period_end = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    payment_method = Column(String(20), nullable=False, default="manual")
    paid_at = Column(DateTime)
    pagbank_checkout_url = Column(Text)
    pagbank_session_id = Column(String(100))
    pagbank_transaction_id = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime)

    # Relationships
    company = relationship("Company", back_populates="proteamcare_invoices")
    subscription = relationship("CompanySubscription", back_populates="invoices")
