from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date, time
from enum import Enum


class PersonType(str, Enum):
    PF = "PF"
    PJ = "PJ"


class PersonStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"


class PhoneType(str, Enum):
    LANDLINE = "landline"
    MOBILE = "mobile"
    WHATSAPP = "whatsapp"
    COMMERCIAL = "commercial"
    EMERGENCY = "emergency"
    FAX = "fax"


class LineType(str, Enum):
    PREPAID = "prepaid"
    POSTPAID = "postpaid"
    CORPORATE = "corporate"


class EmailType(str, Enum):
    PERSONAL = "personal"
    WORK = "work"
    BILLING = "billing"
    CONTACT = "contact"


class AddressType(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    CORRESPONDENCE = "correspondence"
    BILLING = "billing"
    DELIVERY = "delivery"


class AccessDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    UNKNOWN = "unknown"


# Base models for Phone
class PhoneBase(BaseModel):
    country_code: str = Field(default="55", max_length=3)
    number: str = Field(..., max_length=11)
    extension: Optional[str] = Field(None, max_length=10)
    type: PhoneType = PhoneType.MOBILE
    is_principal: bool = False
    is_active: bool = True
    phone_name: Optional[str] = Field(None, max_length=100)
    is_whatsapp: bool = False
    whatsapp_verified: bool = False
    whatsapp_business: bool = False
    whatsapp_name: Optional[str] = Field(None, max_length=100)
    accepts_whatsapp_marketing: bool = True
    accepts_whatsapp_notifications: bool = True
    whatsapp_preferred_time_start: Optional[time] = None
    whatsapp_preferred_time_end: Optional[time] = None
    carrier: Optional[str] = Field(None, max_length=30)
    line_type: Optional[LineType] = None
    contact_priority: int = Field(default=5, ge=1, le=10)
    can_receive_calls: bool = True
    can_receive_sms: bool = True


class PhoneCreate(PhoneBase):
    pass


class PhoneUpdate(BaseModel):
    country_code: Optional[str] = Field(None, max_length=3)
    number: Optional[str] = Field(None, max_length=11)
    extension: Optional[str] = Field(None, max_length=10)
    type: Optional[PhoneType] = None
    is_principal: Optional[bool] = None
    is_active: Optional[bool] = None
    phone_name: Optional[str] = Field(None, max_length=100)
    is_whatsapp: Optional[bool] = None
    whatsapp_verified: Optional[bool] = None
    whatsapp_business: Optional[bool] = None
    whatsapp_name: Optional[str] = Field(None, max_length=100)
    accepts_whatsapp_marketing: Optional[bool] = None
    accepts_whatsapp_notifications: Optional[bool] = None
    whatsapp_preferred_time_start: Optional[time] = None
    whatsapp_preferred_time_end: Optional[time] = None
    carrier: Optional[str] = Field(None, max_length=30)
    line_type: Optional[LineType] = None
    contact_priority: Optional[int] = Field(None, ge=1, le=10)
    can_receive_calls: Optional[bool] = None
    can_receive_sms: Optional[bool] = None


class Phone(PhoneBase):
    id: int
    whatsapp_formatted: Optional[str] = None
    whatsapp_verified_at: Optional[datetime] = None
    last_contact_attempt: Optional[datetime] = None
    last_contact_success: Optional[datetime] = None
    contact_attempts_count: int = 0
    verified_at: Optional[datetime] = None
    verification_method: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Base models for Email
class EmailBase(BaseModel):
    email_address: str = Field(..., max_length=255)
    type: EmailType = EmailType.WORK
    is_principal: bool = False
    is_active: bool = True


class EmailCreate(EmailBase):
    pass


class EmailUpdate(BaseModel):
    email_address: Optional[str] = Field(None, max_length=255)
    type: Optional[EmailType] = None
    is_principal: Optional[bool] = None
    is_active: Optional[bool] = None


class Email(EmailBase):
    id: int
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Base models for Address
class AddressBase(BaseModel):
    street: str = Field(..., max_length=255)
    number: str = Field(..., max_length=20)
    details: Optional[str] = Field(None, max_length=100)
    neighborhood: str = Field(..., max_length=100)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=2)
    zip_code: str = Field(..., max_length=10)
    country: str = Field(default="BR", max_length=2)
    type: AddressType = AddressType.COMMERCIAL
    is_principal: bool = False


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    street: Optional[str] = Field(None, max_length=255)
    number: Optional[str] = Field(None, max_length=20)
    details: Optional[str] = Field(None, max_length=100)
    neighborhood: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=2)
    zip_code: Optional[str] = Field(None, max_length=10)
    country: Optional[str] = Field(None, max_length=2)
    type: Optional[AddressType] = None
    is_principal: Optional[bool] = None


class Address(AddressBase):
    id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    google_place_id: Optional[str] = None
    formatted_address: Optional[str] = None
    ibge_city_code: Optional[int] = None
    ibge_state_code: Optional[int] = None
    region: Optional[str] = None
    microregion: Optional[str] = None
    mesoregion: Optional[str] = None
    within_coverage: Optional[bool] = None
    distance_to_establishment: Optional[int] = None
    estimated_travel_time: Optional[int] = None
    access_difficulty: Optional[AccessDifficulty] = None
    access_notes: Optional[str] = None
    quality_score: Optional[int] = Field(None, ge=0, le=100)
    is_validated: bool = False
    last_validated_at: Optional[datetime] = None
    validation_source: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Base models for People
class PeopleBase(BaseModel):
    person_type: PersonType = PersonType.PJ
    name: str = Field(..., max_length=200)
    trade_name: Optional[str] = Field(None, max_length=200)
    tax_id: str = Field(..., max_length=14)
    secondary_tax_id: Optional[str] = Field(None, max_length=20)
    incorporation_date: Optional[date] = None
    tax_regime: Optional[str] = Field(None, max_length=50)
    legal_nature: Optional[str] = Field(None, max_length=100)
    municipal_registration: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = None
    description: Optional[str] = None
    status: PersonStatus = PersonStatus.ACTIVE


class PeopleCreate(PeopleBase):
    pass


class PeopleUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    trade_name: Optional[str] = Field(None, max_length=200)
    secondary_tax_id: Optional[str] = Field(None, max_length=20)
    incorporation_date: Optional[date] = None
    tax_regime: Optional[str] = Field(None, max_length=50)
    legal_nature: Optional[str] = Field(None, max_length=100)
    municipal_registration: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = None
    description: Optional[str] = None
    status: Optional[PersonStatus] = None


class People(PeopleBase):
    id: int
    lgpd_consent_version: Optional[str] = None
    lgpd_consent_given_at: Optional[datetime] = None
    lgpd_data_retention_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Base models for Company
class CompanyBase(BaseModel):
    settings: Optional[dict] = None
    metadata: Optional[dict] = None
    display_order: int = 0


class CompanyCreate(BaseModel):
    people: PeopleCreate
    company: CompanyBase
    phones: Optional[List[PhoneCreate]] = []
    emails: Optional[List[EmailCreate]] = []
    addresses: Optional[List[AddressCreate]] = []


class CompanyUpdate(BaseModel):
    people: Optional[PeopleUpdate] = None
    company: Optional[CompanyBase] = None


class Company(CompanyBase):
    id: int
    person_id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CompanyDetailed(Company):
    people: People
    phones: List[Phone] = []
    emails: List[Email] = []
    addresses: List[Address] = []

    model_config = ConfigDict(from_attributes=True)


class CompanyList(BaseModel):
    id: int
    person_id: int
    name: str
    trade_name: Optional[str]
    tax_id: str
    status: PersonStatus
    phones_count: int = 0
    emails_count: int = 0
    addresses_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)