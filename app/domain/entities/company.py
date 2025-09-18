"""
Company Domain Entities - Entidades de domínio puras
Sem dependências externas (Pydantic, SQLAlchemy, etc.)
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import Enum
from typing import Any, Dict, List, Optional


class PersonType(Enum):
    PF = "PF"
    PJ = "PJ"


class PersonStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"


class PhoneType(Enum):
    LANDLINE = "landline"
    MOBILE = "mobile"
    WHATSAPP = "whatsapp"
    COMMERCIAL = "commercial"
    EMERGENCY = "emergency"
    FAX = "fax"


class LineType(Enum):
    PREPAID = "prepaid"
    POSTPAID = "postpaid"
    CORPORATE = "corporate"


class EmailType(Enum):
    PERSONAL = "personal"
    WORK = "work"
    BILLING = "billing"
    CONTACT = "contact"


class AddressType(Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    CORRESPONDENCE = "correspondence"
    BILLING = "billing"
    DELIVERY = "delivery"


class AccessDifficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    UNKNOWN = "unknown"


@dataclass
class PhoneEntity:
    """Entidade de domínio para Telefone"""

    id: Optional[int] = None
    country_code: str = "55"
    number: str = ""
    extension: Optional[str] = None
    type: PhoneType = PhoneType.MOBILE
    is_principal: bool = False
    is_active: bool = True
    phone_name: Optional[str] = None
    is_whatsapp: bool = False
    whatsapp_verified: bool = False
    whatsapp_business: bool = False
    whatsapp_name: Optional[str] = None
    accepts_whatsapp_marketing: bool = True
    accepts_whatsapp_notifications: bool = True
    whatsapp_preferred_time_start: Optional[time] = None
    whatsapp_preferred_time_end: Optional[time] = None
    carrier: Optional[str] = None
    line_type: Optional[LineType] = None
    contact_priority: int = 5
    can_receive_calls: bool = True
    can_receive_sms: bool = True
    whatsapp_formatted: Optional[str] = None
    whatsapp_verified_at: Optional[datetime] = None
    last_contact_attempt: Optional[datetime] = None
    last_contact_success: Optional[datetime] = None
    contact_attempts_count: int = 0
    verified_at: Optional[datetime] = None
    verification_method: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_valid_mobile(self) -> bool:
        """Verifica se é um celular válido no Brasil"""
        if not self.number or len(self.number) != 11:
            return False
        return self.number[2] == "9"

    def format_whatsapp(self) -> str:
        """Formata número para WhatsApp"""
        if not self.number:
            return ""
        return f"{self.country_code}{self.number}"


@dataclass
class EmailEntity:
    """Entidade de domínio para Email"""

    id: Optional[int] = None
    email_address: str = ""
    type: EmailType = EmailType.WORK
    is_principal: bool = False
    is_active: bool = True
    verified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def is_valid_email(self) -> bool:
        """Validação básica de email"""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, self.email_address))


@dataclass
class AddressEntity:
    """Entidade de domínio para Endereço"""

    id: Optional[int] = None
    street: str = ""
    number: Optional[str] = None
    details: Optional[str] = None
    neighborhood: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = "BR"
    type: AddressType = AddressType.COMMERCIAL
    is_principal: bool = False

    # Geocoding fields
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    google_place_id: Optional[str] = None
    geocoding_accuracy: Optional[str] = None
    geocoding_source: Optional[str] = None
    formatted_address: Optional[str] = None
    coordinates_added_at: Optional[datetime] = None
    coordinates_source: Optional[str] = None

    # Enrichment metadata
    enriched_at: Optional[datetime] = None
    enrichment_source: Optional[str] = None
    validation_source: Optional[str] = None
    last_validated_at: Optional[datetime] = None
    is_validated: bool = False

    # Códigos oficiais brasileiros (ViaCEP)
    ibge_city_code: Optional[int] = None
    ibge_state_code: Optional[int] = None
    gia_code: Optional[str] = None
    siafi_code: Optional[str] = None
    area_code: Optional[str] = None
    region: Optional[str] = None
    microregion: Optional[str] = None
    mesoregion: Optional[str] = None
    within_coverage: Optional[bool] = None
    distance_to_establishment: Optional[int] = None
    estimated_travel_time: Optional[int] = None
    access_difficulty: Optional[AccessDifficulty] = None
    access_notes: Optional[str] = None
    quality_score: Optional[int] = None
    api_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def has_coordinates(self) -> bool:
        """Verifica se o endereço tem coordenadas"""
        return self.latitude is not None and self.longitude is not None

    def is_complete(self) -> bool:
        """Verifica se o endereço está completo"""
        return bool(self.street and self.city and self.state and self.zip_code)


@dataclass
class PeopleEntity:
    """Entidade de domínio para Pessoa"""

    id: Optional[int] = None
    person_type: PersonType = PersonType.PJ
    name: str = ""
    trade_name: Optional[str] = None
    tax_id: str = ""
    secondary_tax_id: Optional[str] = None
    incorporation_date: Optional[date] = None
    tax_regime: Optional[str] = None
    legal_nature: Optional[str] = None
    municipal_registration: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    status: PersonStatus = PersonStatus.ACTIVE
    lgpd_consent_version: Optional[str] = None
    lgpd_consent_given_at: Optional[datetime] = None
    lgpd_data_retention_expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    def is_active(self) -> bool:
        """Verifica se a pessoa está ativa"""
        return self.status == PersonStatus.ACTIVE and self.deleted_at is None

    def is_company(self) -> bool:
        """Verifica se é pessoa jurídica"""
        return self.person_type == PersonType.PJ

    def validate_tax_id(self) -> bool:
        """Validação básica do documento"""
        if not self.tax_id:
            return False

        # Remove caracteres não numéricos
        clean_tax_id = "".join(filter(str.isdigit, self.tax_id))

        if self.person_type == PersonType.PJ:
            return len(clean_tax_id) == 14  # CNPJ
        else:
            return len(clean_tax_id) == 11  # CPF


@dataclass
class CompanyEntity:
    """Entidade de domínio para Empresa"""

    id: Optional[int] = None
    person_id: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    display_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    # Relacionamentos
    people: Optional[PeopleEntity] = None
    phones: List[PhoneEntity] = field(default_factory=list)
    emails: List[EmailEntity] = field(default_factory=list)
    addresses: List[AddressEntity] = field(default_factory=list)

    def __post_init__(self):
        """Inicializa listas vazias se None"""
        if self.phones is None:
            self.phones = []
        if self.emails is None:
            self.emails = []
        if self.addresses is None:
            self.addresses = []
        if self.settings is None:
            self.settings = {}
        if self.metadata is None:
            self.metadata = {}

    def is_active(self) -> bool:
        """Verifica se a empresa está ativa"""
        return (
            self.deleted_at is None
            and self.people is not None
            and self.people.is_active()
        )

    def get_principal_phone(self) -> Optional[PhoneEntity]:
        """Obtém o telefone principal"""
        for phone in self.phones:
            if phone.is_principal and phone.is_active:
                return phone
        return self.phones[0] if self.phones else None

    def get_principal_email(self) -> Optional[EmailEntity]:
        """Obtém o email principal"""
        for email in self.emails:
            if email.is_principal and email.is_active:
                return email
        return self.emails[0] if self.emails else None

    def get_principal_address(self) -> Optional[AddressEntity]:
        """Obtém o endereço principal"""
        for address in self.addresses:
            if address.is_principal:
                return address
        return self.addresses[0] if self.addresses else None

    def has_valid_contacts(self) -> bool:
        """Verifica se tem contatos válidos"""
        has_phone = any(phone.is_active for phone in self.phones)
        has_email = any(email.is_active for email in self.emails)
        return has_phone and has_email
