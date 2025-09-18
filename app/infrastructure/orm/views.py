"""
Views PostgreSQL mapeadas como modelos SQLAlchemy read-only
"""

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# =====================================
# SPRINT 1: VIEWS DE AUTENTICAÇÃO
# =====================================


class UserCompleteView(Base):
    """View com dados completos de usuários - vw_users_complete"""

    __tablename__ = "vw_users_complete"
    __table_args__ = {"schema": "master"}

    # User fields
    user_id = Column(BigInteger, primary_key=True)
    user_person_id = Column(BigInteger)
    user_email = Column(String)
    user_email_verified_at = Column(DateTime)
    user_is_active = Column(Boolean)
    user_is_system_admin = Column(Boolean)
    user_preferences = Column(JSON)
    user_notification_settings = Column(JSON)
    user_two_factor_secret = Column(Text)
    user_two_factor_recovery_codes = Column(Text)
    user_last_login_at = Column(DateTime)
    user_password_changed_at = Column(DateTime)
    user_created_at = Column(DateTime)
    user_updated_at = Column(DateTime)
    user_deleted_at = Column(DateTime)

    # Person fields
    person_id = Column(BigInteger)
    person_type = Column(String)
    person_name = Column(String)
    person_trade_name = Column(String)
    person_tax_id = Column(String)
    person_secondary_tax_id = Column(String)
    person_birth_date = Column(DateTime)
    person_gender = Column(String)
    person_marital_status = Column(String)
    person_occupation = Column(String)
    person_incorporation_date = Column(DateTime)
    person_tax_regime = Column(String)
    person_legal_nature = Column(String)
    person_municipal_registration = Column(String)
    person_status = Column(String)
    person_is_active = Column(Boolean)
    person_metadata = Column(JSON)
    person_website = Column(Text)
    person_description = Column(Text)
    person_lgpd_consent_version = Column(String)
    person_lgpd_consent_given_at = Column(DateTime)
    person_lgpd_data_retention_expires_at = Column(DateTime)
    person_created_at = Column(DateTime)
    person_updated_at = Column(DateTime)
    person_deleted_at = Column(DateTime)

    # Company fields
    company_id = Column(BigInteger)
    company_person_id = Column(BigInteger)
    company_settings = Column(JSON)
    company_metadata = Column(JSON)
    company_display_order = Column(Integer)
    company_created_at = Column(DateTime)
    company_updated_at = Column(DateTime)
    company_deleted_at = Column(DateTime)

    # Establishment fields
    establishment_id = Column(BigInteger)
    establishment_person_id = Column(BigInteger)
    establishment_company_id = Column(BigInteger)
    establishment_code = Column(String)
    establishment_type = Column(String)
    establishment_category = Column(String)
    establishment_is_active = Column(Boolean)
    establishment_is_principal = Column(Boolean)
    establishment_settings = Column(JSON)
    establishment_operating_hours = Column(JSON)
    establishment_service_areas = Column(JSON)
    establishment_created_at = Column(DateTime)
    establishment_updated_at = Column(DateTime)
    establishment_deleted_at = Column(DateTime)

    # User Establishment relationship
    user_establishment_id = Column(BigInteger)
    user_establishment_role_id = Column(BigInteger)
    user_establishment_is_primary = Column(Boolean)
    user_establishment_status = Column(String)
    user_establishment_assigned_by_user_id = Column(BigInteger)
    user_establishment_assigned_at = Column(DateTime)
    user_establishment_expires_at = Column(DateTime)
    user_establishment_permissions = Column(JSON)
    user_establishment_created_at = Column(DateTime)
    user_establishment_updated_at = Column(DateTime)
    user_establishment_deleted_at = Column(DateTime)

    # Role fields
    role_id = Column(BigInteger)
    role_name = Column(String)
    role_display_name = Column(String)
    role_description = Column(Text)
    role_level = Column(Integer)
    role_context_type = Column(String)
    role_is_active = Column(Boolean)
    role_is_system_role = Column(Boolean)
    role_settings = Column(JSON)
    role_created_at = Column(DateTime)
    role_updated_at = Column(DateTime)

    # User Role relationship
    user_role_id = Column(BigInteger)
    user_role_context_type = Column(String)
    user_role_context_id = Column(BigInteger)
    user_role_status = Column(String)
    user_role_assigned_by_user_id = Column(BigInteger)
    user_role_assigned_at = Column(DateTime)
    user_role_expires_at = Column(DateTime)
    user_role_created_at = Column(DateTime)
    user_role_updated_at = Column(DateTime)
    user_role_deleted_at = Column(DateTime)

    # Desabilitar operações de escrita
    __mapper_args__ = {"confirm_deleted_rows": False}


class UserHierarchicalView(Base):
    """View com hierarquia organizacional de usuários - vw_users_hierarchical"""

    __tablename__ = "vw_users_hierarchical"
    __table_args__ = {"schema": "master"}

    user_id = Column(BigInteger, primary_key=True)
    user_email = Column(String)
    user_is_active = Column(Boolean)
    user_is_system_admin = Column(Boolean)

    person_name = Column(String)

    company_id = Column(BigInteger)
    establishment_code = Column(String)

    role_name = Column(String)
    role_display_name = Column(String)
    role_level = Column(Integer)

    __mapper_args__ = {"confirm_deleted_rows": False}


class RolePermissionView(Base):
    """View com mapeamento completo permissões×roles - vw_role_permissions"""

    __tablename__ = "vw_role_permissions"
    __table_args__ = {"schema": "master"}

    role_id = Column(BigInteger, primary_key=True)
    role_name = Column(String)
    role_display_name = Column(String)
    role_level = Column(Integer)
    role_context = Column(String)

    permission_id = Column(BigInteger)
    permission_name = Column(String)
    permission_display_name = Column(String)
    permission_module = Column(String)
    permission_action = Column(String)
    permission_resource = Column(String)
    permission_context_level = Column(String)

    # Metadata
    granted_by_user_id = Column(BigInteger)
    granted_at = Column(DateTime)

    __mapper_args__ = {"confirm_deleted_rows": False}


class ActiveSessionView(Base):
    """View com sessões ativas e contexto - vw_active_sessions"""

    __tablename__ = "vw_active_sessions"
    __table_args__ = {"schema": "master"}

    session_id = Column(BigInteger, primary_key=True)
    session_token = Column(String)

    user_email = Column(String)
    impersonated_email = Column(String)

    active_role = Column(String)
    active_context_type = Column(String)
    active_context_id = Column(BigInteger)
    active_context_name = Column(String)

    session_created_at = Column(DateTime)
    session_last_activity = Column(DateTime)
    session_expires_at = Column(DateTime)

    is_impersonation = Column(Boolean)
    original_user_id = Column(BigInteger)
    current_user_id = Column(BigInteger)

    __mapper_args__ = {"confirm_deleted_rows": False}


# =====================================
# SPRINT 2: VIEWS DE GESTÃO
# =====================================


class MenuHierarchyView(Base):
    """View com estrutura hierárquica de menus - vw_menu_hierarchy"""

    __tablename__ = "vw_menu_hierarchy"
    __table_args__ = {"schema": "master"}

    id = Column(BigInteger, primary_key=True)
    parent_id = Column(BigInteger)
    name = Column(String)
    slug = Column(String)
    path = Column(Text)  # TEXT no banco
    level = Column(Integer)
    sort_order = Column(Integer)
    url = Column(String)
    route_name = Column(String)
    route_params = Column(JSON)  # JSONB no banco
    menu_type = Column(String)
    status = Column(String)
    is_visible = Column(Boolean)
    visible_in_menu = Column(Boolean)
    permission_name = Column(String)
    company_specific = Column(Boolean)
    establishment_specific = Column(Boolean)
    icon = Column(String)
    badge_text = Column(String)
    badge_color = Column(String)
    css_class = Column(String)
    description = Column(String)
    help_text = Column(Text)
    keywords = Column(JSON)
    full_path_name = Column(String)
    id_path = Column(JSON)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    deleted_at = Column(DateTime)
    created_by = Column(BigInteger)
    updated_by = Column(BigInteger)

    __mapper_args__ = {"confirm_deleted_rows": False}


class UserAdminView(Base):
    """View para painel administrativo de usuários - vw_users_admin"""

    __tablename__ = "vw_users_admin"
    __table_args__ = {"schema": "master"}

    user_id = Column(BigInteger, primary_key=True)
    user_email = Column(String)
    user_is_active = Column(Boolean)
    user_is_system_admin = Column(Boolean)
    user_2fa_status = Column(Text)  # Computed field
    user_2fa_recovery_status = Column(Text)  # Computed field
    user_last_login_at = Column(DateTime)
    user_created_at = Column(DateTime)

    person_name = Column(String)
    person_type = Column(String)
    person_tax_id = Column(String)
    person_status = Column(String)

    __mapper_args__ = {"confirm_deleted_rows": False}


# =====================================
# SPRINT 3: VIEWS DE NEGÓCIO
# =====================================


class AddressGeoView(Base):
    """View com endereços e geolocalização - vw_addresses_with_geolocation"""

    __tablename__ = "vw_addresses_with_geolocation"
    __table_args__ = {"schema": "master"}

    id = Column(BigInteger, primary_key=True)
    addressable_type = Column(String)
    addressable_id = Column(BigInteger)
    type = Column(String)

    # Endereço formatado
    full_address = Column(String)

    # Coordenadas
    latitude = Column(String)  # Numeric no banco
    longitude = Column(String)  # Numeric no banco

    # Qualidade e validação
    quality_score = Column(Integer)
    is_validated = Column(Boolean)
    geocoding_accuracy = Column(String)

    # Informações adicionais
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)

    __mapper_args__ = {"confirm_deleted_rows": False}


class WhatsAppNumberView(Base):
    """View com números WhatsApp formatados - vw_whatsapp_numbers"""

    __tablename__ = "vw_whatsapp_numbers"
    __table_args__ = {"schema": "master"}

    id = Column(BigInteger, primary_key=True)
    phoneable_type = Column(String)
    phoneable_id = Column(BigInteger)

    phone_name = Column(String)
    whatsapp_formatted = Column(String)
    whatsapp_business = Column(Boolean)
    whatsapp_name = Column(String)

    accepts_whatsapp_marketing = Column(Boolean)
    accepts_whatsapp_notifications = Column(Boolean)

    whatsapp_preferred_time_start = Column(String)  # Time no banco
    whatsapp_preferred_time_end = Column(String)  # Time no banco

    is_verified = Column(Boolean)
    last_contact_success = Column(DateTime)

    __mapper_args__ = {"confirm_deleted_rows": False}
