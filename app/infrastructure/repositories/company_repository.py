from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.orm import selectinload, joinedload
from structlog import get_logger
from app.infrastructure.orm.models import People, Company, Phone, Email, Address
# ✅ Infrastructure deve usar entidades domain ao invés de schemas presentation
from app.domain.entities.company import CompanyEntity
from app.presentation.schemas.company import AddressCreate, CompanyCreate, CompanyDetailed, CompanyList, CompanyUpdate
from typing import Dict, Any
from app.utils.validators import validate_contacts_quality
from app.infrastructure.services.address_enrichment_service import address_enrichment_service


class CompanyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = get_logger()
    
    def _to_naive_datetime(self, dt):
        """Convert timezone-aware datetime to naive datetime"""
        if dt is None:
            return None
        if isinstance(dt, datetime) and dt.tzinfo is not None:
            return dt.replace(tzinfo=None)
        return dt

    async def _enrich_addresses_automatically(self, addresses: List[AddressCreate]) -> List[dict]:
        """
        Hook para enriquecimento automático de endereços antes de salvar
        
        Args:
            addresses: Lista de endereços a serem enriquecidos
            
        Returns:
            Lista de endereços enriquecidos como dicionários
        """
        if not addresses:
            return []
            
        self.logger.info(f"Starting automatic address enrichment for {len(addresses)} addresses")
        
        # Converter AddressCreate para dicionários para o serviço
        addresses_dict = []
        for addr in addresses:
            addr_dict = addr.model_dump()
            addresses_dict.append(addr_dict)
        
        # Enriquecer endereços
        enriched_addresses = await address_enrichment_service.enrich_multiple_addresses(addresses_dict)
        
        self.logger.info(f"Address enrichment completed", 
                        original_count=len(addresses), 
                        enriched_count=len(enriched_addresses))
        
        return enriched_addresses

    async def create_company(self, company_data: CompanyCreate) -> CompanyDetailed:
        """Create a new company with related entities in a transaction"""
        try:
            self.logger.info("Iniciando criação de empresa", company_data=company_data.model_dump())

            # Validate contact data quality
            phones_data = [phone.model_dump() for phone in (company_data.phones or [])]
            emails_data = [email.model_dump() for email in (company_data.emails or [])]
            addresses_data = [address.model_dump() for address in (company_data.addresses or [])]

            self.logger.info("Dados de endereços recebidos", addresses=addresses_data)

            is_valid, error_message = validate_contacts_quality(phones_data, emails_data, addresses_data)
            if not is_valid:
                raise ValueError(error_message)
            # Create people record first
            people_db = People(
                person_type=company_data.people.person_type,
                name=company_data.people.name,
                trade_name=company_data.people.trade_name,
                tax_id=company_data.people.tax_id,
                secondary_tax_id=company_data.people.secondary_tax_id,
                incorporation_date=company_data.people.incorporation_date,
                tax_regime=company_data.people.tax_regime,
                legal_nature=company_data.people.legal_nature,
                municipal_registration=company_data.people.municipal_registration,
                website=company_data.people.website,
                description=company_data.people.description,
                status=company_data.people.status
            )
            self.db.add(people_db)
            await self.db.flush()  # Get the ID but don't commit yet
            
            # Create company record
            company_db = Company(
                person_id=people_db.id,
                settings=company_data.company.settings,
                metadata_=company_data.company.metadata,
                display_order=company_data.company.display_order
            )
            self.db.add(company_db)
            await self.db.flush()
            
            # Create related phones
            for phone_data in company_data.phones or []:
                phone_db = Phone(
                    phoneable_id=people_db.id,
                    country_code=phone_data.country_code,
                    number=phone_data.number,
                    extension=phone_data.extension,
                    type=phone_data.type,
                    is_principal=phone_data.is_principal,
                    is_active=phone_data.is_active,
                    phone_name=phone_data.phone_name,
                    is_whatsapp=phone_data.is_whatsapp,
                    whatsapp_verified=phone_data.whatsapp_verified,
                    whatsapp_business=phone_data.whatsapp_business,
                    whatsapp_name=phone_data.whatsapp_name,
                    accepts_whatsapp_marketing=phone_data.accepts_whatsapp_marketing,
                    accepts_whatsapp_notifications=phone_data.accepts_whatsapp_notifications,
                    whatsapp_preferred_time_start=phone_data.whatsapp_preferred_time_start,
                    whatsapp_preferred_time_end=phone_data.whatsapp_preferred_time_end,
                    carrier=phone_data.carrier,
                    line_type=phone_data.line_type,
                    contact_priority=phone_data.contact_priority,
                    can_receive_calls=phone_data.can_receive_calls,
                    can_receive_sms=phone_data.can_receive_sms
                )
                self.db.add(phone_db)
            
            # Create related emails
            for email_data in company_data.emails or []:
                email_db = Email(
                    emailable_id=people_db.id,
                    email_address=email_data.email_address,
                    type=email_data.type,
                    is_principal=email_data.is_principal,
                    is_active=email_data.is_active
                )
                self.db.add(email_db)
            
            # Create related addresses with automatic enrichment
            if company_data.addresses:
                # 🚀 HOOK: Enriquecimento automático de endereços
                enriched_addresses = await self._enrich_addresses_automatically(company_data.addresses)
                
                for address_dict in enriched_addresses:
                    self.logger.info("Criando endereço enriquecido", address_data=address_dict)

                    address_db = Address(
                        addressable_id=people_db.id,
                        street=address_dict.get('street'),
                        number=address_dict.get('number'),
                        details=address_dict.get('details'),
                        neighborhood=address_dict.get('neighborhood'),
                        city=address_dict.get('city'),
                        state=address_dict.get('state'),
                        zip_code=address_dict.get('zip_code'),
                        country=address_dict.get('country', 'BR'),
                        type=address_dict.get('type', 'commercial'),
                        is_principal=address_dict.get('is_principal', False),
                        # Geocoding fields (enriquecidos automaticamente)
                        latitude=address_dict.get('latitude'),
                        longitude=address_dict.get('longitude'),
                        google_place_id=address_dict.get('google_place_id'),
                        formatted_address=address_dict.get('formatted_address'),
                        geocoding_accuracy=address_dict.get('geocoding_accuracy'),
                        geocoding_source=address_dict.get('geocoding_source'),
                        coordinates_source=address_dict.get('coordinates_source'),
                        # Validation fields (enriquecidos automaticamente)
                        is_validated=address_dict.get('is_validated', False),
                        validation_source=address_dict.get('validation_source'),
                        # IBGE codes (enriquecidos automaticamente)
                        ibge_city_code=address_dict.get('ibge_city_code'),
                        ibge_state_code=address_dict.get('ibge_state_code'),
                        gia_code=address_dict.get('gia_code'),
                        siafi_code=address_dict.get('siafi_code'),
                        area_code=address_dict.get('area_code'),
                        # Enrichment metadata
                        enrichment_source=address_dict.get('enrichment_source'),
                        # API data
                        api_data=address_dict.get('api_data')
                    )

                self.logger.info("Endereço criado no banco", address_db_data={
                    'latitude': address_db.latitude,
                    'longitude': address_db.longitude,
                    'geocoding_accuracy': address_db.geocoding_accuracy,
                    'geocoding_source': address_db.geocoding_source,
                    'ibge_city_code': address_db.ibge_city_code,
                    'gia_code': address_db.gia_code,
                    'siafi_code': address_db.siafi_code,
                    'area_code': address_db.area_code
                })

                self.db.add(address_db)
            
            await self.db.commit()
            
            # Return the complete company data
            return await self.get_company(company_db.id)
            
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_company(self, company_id: int) -> Optional[CompanyDetailed]:
        """Get a company with all related data"""
        query = (
            select(Company)
            .options(
                joinedload(Company.people).selectinload(People.phones),
                joinedload(Company.people).selectinload(People.emails),
                joinedload(Company.people).selectinload(People.addresses)
            )
            .where(and_(Company.id == company_id, Company.deleted_at.is_(None)))
        )
        
        result = await self.db.execute(query)
        company_db = result.scalars().first()
        
        if not company_db:
            return None
        
        # Convert to dict and fix metadata field mapping
        company_dict = {
            'id': company_db.id,
            'person_id': company_db.person_id,
            'settings': company_db.settings,
            'metadata': company_db.metadata_,  # Map metadata_ to metadata
            'display_order': company_db.display_order,
            'created_at': company_db.created_at,
            'updated_at': company_db.updated_at,
            'deleted_at': company_db.deleted_at,
            'people': {
                'id': company_db.people.id,
                'person_type': company_db.people.person_type,
                'name': company_db.people.name,
                'trade_name': company_db.people.trade_name,
                'tax_id': company_db.people.tax_id,
                'secondary_tax_id': company_db.people.secondary_tax_id,
                'birth_date': company_db.people.birth_date,
                'incorporation_date': company_db.people.incorporation_date,
                'gender': company_db.people.gender,
                'marital_status': company_db.people.marital_status,
                'occupation': company_db.people.occupation,
                'tax_regime': company_db.people.tax_regime,
                'legal_nature': company_db.people.legal_nature,
                'municipal_registration': company_db.people.municipal_registration,
                'website': company_db.people.website,
                'description': company_db.people.description,
                'status': company_db.people.status,
                'is_active': company_db.people.is_active,
                'lgpd_consent_version': company_db.people.lgpd_consent_version,
                'lgpd_consent_given_at': company_db.people.lgpd_consent_given_at,
                'lgpd_data_retention_expires_at': company_db.people.lgpd_data_retention_expires_at,
                'created_at': company_db.people.created_at,
                'updated_at': company_db.people.updated_at,
                'deleted_at': company_db.people.deleted_at
            },
            'phones': [
                {
                    'id': phone.id,
                    'country_code': phone.country_code,
                    'number': phone.number,
                    'extension': phone.extension,
                    'type': phone.type,
                    'is_principal': phone.is_principal,
                    'is_active': phone.is_active,
                    'phone_name': phone.phone_name,
                    'is_whatsapp': phone.is_whatsapp,
                    'whatsapp_formatted': phone.whatsapp_formatted,
                    'whatsapp_verified': phone.whatsapp_verified,
                    'whatsapp_verified_at': phone.whatsapp_verified_at,
                    'whatsapp_business': phone.whatsapp_business,
                    'whatsapp_name': phone.whatsapp_name,
                    'accepts_whatsapp_marketing': phone.accepts_whatsapp_marketing,
                    'accepts_whatsapp_notifications': phone.accepts_whatsapp_notifications,
                    'whatsapp_preferred_time_start': phone.whatsapp_preferred_time_start,
                    'whatsapp_preferred_time_end': phone.whatsapp_preferred_time_end,
                    'carrier': phone.carrier,
                    'line_type': phone.line_type,
                    'contact_priority': phone.contact_priority,
                    'can_receive_calls': phone.can_receive_calls,
                    'can_receive_sms': phone.can_receive_sms,
                    'last_contact_attempt': phone.last_contact_attempt,
                    'last_contact_success': phone.last_contact_success,
                    'contact_attempts_count': phone.contact_attempts_count,
                    'verified_at': phone.verified_at,
                    'verification_method': phone.verification_method,
                    'created_at': phone.created_at,
                    'updated_at': phone.updated_at
                } for phone in company_db.people.phones
            ],
            'emails': [
                {
                    'id': email.id,
                    'email_address': email.email_address,
                    'type': email.type,
                    'is_principal': email.is_principal,
                    'is_active': email.is_active,
                    'verified_at': email.verified_at,
                    'created_at': email.created_at,
                    'updated_at': email.updated_at
                } for email in company_db.people.emails
            ],
            'addresses': [
                {
                    'id': addr.id,
                    'street': addr.street,
                    'number': addr.number,
                    'details': addr.details,
                    'neighborhood': addr.neighborhood,
                    'city': addr.city,
                    'state': addr.state,
                    'zip_code': addr.zip_code,
                    'country': addr.country,
                    'type': addr.type,
                    'is_principal': addr.is_principal,
                    'latitude': addr.latitude,
                    'longitude': addr.longitude,
                    'google_place_id': addr.google_place_id,
                    'formatted_address': addr.formatted_address,
                    'geocoding_accuracy': addr.geocoding_accuracy,
                    'geocoding_source': addr.geocoding_source,
                    'ibge_city_code': addr.ibge_city_code,
                    'ibge_state_code': addr.ibge_state_code,
                    'gia_code': addr.gia_code,
                    'siafi_code': addr.siafi_code,
                    'area_code': addr.area_code,
                    'region': addr.region,
                    'microregion': addr.microregion,
                    'mesoregion': addr.mesoregion,
                    'within_coverage': addr.within_coverage,
                    'distance_to_establishment': addr.distance_to_establishment,
                    'estimated_travel_time': addr.estimated_travel_time,
                    'access_difficulty': addr.access_difficulty,
                    'access_notes': addr.access_notes,
                    'quality_score': addr.quality_score,
                    'is_validated': addr.is_validated,
                    'last_validated_at': addr.last_validated_at,
                    'validation_source': addr.validation_source,
                    'api_data': addr.api_data,
                    'created_at': addr.created_at,
                    'updated_at': addr.updated_at
                } for addr in company_db.people.addresses
            ]
        }
        
        return CompanyDetailed.model_validate(company_dict)

    async def get_companies(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[CompanyList]:
        """Get list of companies with summary information"""
        query = (
            select(
                Company.id,
                Company.person_id,
                People.name,
                People.trade_name,
                People.tax_id,
                People.status,
                func.count(Phone.id).label('phones_count'),
                func.count(Email.id).label('emails_count'),
                func.count(Address.id).label('addresses_count'),
                Company.created_at,
                Company.updated_at
            )
            .join(People, Company.person_id == People.id)
            .outerjoin(Phone, and_(Phone.phoneable_id == People.id, Phone.deleted_at.is_(None)))
            .outerjoin(Email, and_(Email.emailable_id == People.id, Email.deleted_at.is_(None)))
            .outerjoin(Address, and_(Address.addressable_id == People.id, Address.deleted_at.is_(None)))
            .where(and_(Company.deleted_at.is_(None), People.deleted_at.is_(None)))
            .group_by(Company.id, People.id)
            .order_by(Company.id.desc())
        )
        
        # Add search filter
        if search:
            search_filter = or_(
                People.name.ilike(f"%{search}%"),
                People.trade_name.ilike(f"%{search}%"),
                People.tax_id.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
        
        # Add status filter
        if status:
            query = query.where(People.status == status)
        
        # Add pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        companies = []
        for row in rows:
            companies.append(CompanyList(
                id=row.id,
                person_id=row.person_id,
                name=row.name,
                trade_name=row.trade_name,
                tax_id=row.tax_id,
                status=row.status,
                phones_count=row.phones_count or 0,
                emails_count=row.emails_count or 0,
                addresses_count=row.addresses_count or 0,
                created_at=row.created_at,
                updated_at=row.updated_at
            ))
        
        return companies

    async def update_company(self, company_id: int, company_data: CompanyUpdate) -> Optional[CompanyDetailed]:
        """Update a company and related people data with business rules validation"""
        try:
            # Business rule validation: Company must have at least one contact of each type
            if company_data.phones is not None and len(company_data.phones) == 0:
                raise ValueError("Empresa deve ter pelo menos um telefone")
            if company_data.emails is not None and len(company_data.emails) == 0:
                raise ValueError("Empresa deve ter pelo menos um email")
            if company_data.addresses is not None and len(company_data.addresses) == 0:
                raise ValueError("Empresa deve ter pelo menos um endereço")
            
            # Validate contact data quality if provided
            if company_data.phones:
                phones_data = [phone.model_dump() for phone in company_data.phones]
                emails_data = [email.model_dump() for email in (company_data.emails or [])]
                addresses_data = [address.model_dump() for address in (company_data.addresses or [])]
                
                # Validate only if we have all contact types in the update
                if company_data.phones and company_data.emails and company_data.addresses:
                    is_valid, error_message = validate_contacts_quality(phones_data, emails_data, addresses_data)
                    if not is_valid:
                        raise ValueError(error_message)
            # Get existing company
            query = select(Company).where(and_(Company.id == company_id, Company.deleted_at.is_(None)))
            result = await self.db.execute(query)
            company_db = result.scalars().first()
            
            if not company_db:
                return None
            
            # Update company fields if provided
            if company_data.company:
                if company_data.company.settings is not None:
                    company_db.settings = company_data.company.settings
                if company_data.company.metadata is not None:
                    company_db.metadata_ = company_data.company.metadata
                if company_data.company.display_order is not None:
                    company_db.display_order = company_data.company.display_order
            
            # Update people fields if provided
            if company_data.people:
                people_query = select(People).where(People.id == company_db.person_id)
                people_result = await self.db.execute(people_query)
                people_db = people_result.scalars().first()
                
                if people_db:
                    for field, value in company_data.people.model_dump(exclude_unset=True).items():
                        if hasattr(people_db, field):
                            setattr(people_db, field, value)
            
            # Update phones if provided
            if company_data.phones is not None:
                # Remove existing phones (hard delete for updates)
                await self.db.execute(delete(Phone).where(Phone.phoneable_id == company_db.person_id))
                
                # Add new phones
                for phone_data in company_data.phones:
                    phone_db = Phone(
                        phoneable_id=company_db.person_id,
                        country_code=phone_data.country_code,
                        number=phone_data.number,
                        extension=phone_data.extension,
                        type=phone_data.type,
                        is_principal=phone_data.is_principal,
                        is_active=phone_data.is_active,
                        phone_name=phone_data.phone_name,
                        is_whatsapp=phone_data.is_whatsapp,
                        whatsapp_verified=phone_data.whatsapp_verified,
                        whatsapp_business=phone_data.whatsapp_business,
                        whatsapp_name=phone_data.whatsapp_name,
                        accepts_whatsapp_marketing=phone_data.accepts_whatsapp_marketing,
                        accepts_whatsapp_notifications=phone_data.accepts_whatsapp_notifications,
                        whatsapp_preferred_time_start=phone_data.whatsapp_preferred_time_start,
                        whatsapp_preferred_time_end=phone_data.whatsapp_preferred_time_end,
                        carrier=phone_data.carrier,
                        line_type=phone_data.line_type,
                        contact_priority=phone_data.contact_priority,
                        can_receive_calls=phone_data.can_receive_calls,
                        can_receive_sms=phone_data.can_receive_sms
                    )
                    self.db.add(phone_db)
            
            # Update emails if provided
            if company_data.emails is not None:
                # Remove existing emails (hard delete for updates)
                await self.db.execute(delete(Email).where(Email.emailable_id == company_db.person_id))
                
                # Add new emails
                for email_data in company_data.emails:
                    email_db = Email(
                        emailable_id=company_db.person_id,
                        email_address=email_data.email_address,
                        type=email_data.type,
                        is_principal=email_data.is_principal,
                        is_active=email_data.is_active
                    )
                    self.db.add(email_db)
            
            # Update addresses if provided
            if company_data.addresses is not None:
                # Buscar endereços existentes para preservar dados de geocoding
                existing_addresses = await self.db.execute(
                    select(Address).where(Address.addressable_id == company_db.person_id)
                )
                existing_addresses_dict = {addr.id: addr for addr in existing_addresses.scalars().all()}
                
                # Remove todos os endereços existentes (será recriado com merge de dados)
                await self.db.execute(delete(Address).where(Address.addressable_id == company_db.person_id))
                
                # Add new addresses com merge inteligente de geocoding
                for i, address_data in enumerate(company_data.addresses):
                    self.logger.info("Atualizando endereço", address_data=address_data.model_dump())
                    
                    # Buscar endereço existente correspondente (por ordem ou principal)
                    existing_addr = None
                    if existing_addresses_dict:
                        # Tentar matchear por endereço principal ou primeira ocorrência
                        existing_addr = list(existing_addresses_dict.values())[0] if i == 0 else None
                    
                    # Merge inteligente: usar coordenadas do payload OU preservar existentes
                    merged_latitude = getattr(address_data, 'latitude', None)
                    merged_longitude = getattr(address_data, 'longitude', None)
                    merged_accuracy = getattr(address_data, 'geocoding_accuracy', None)
                    merged_source = getattr(address_data, 'geocoding_source', None)
                    
                    # Se não tem coordenadas no payload MAS tinha no endereço existente, preservar
                    if not merged_latitude and existing_addr and existing_addr.latitude:
                        merged_latitude = existing_addr.latitude
                        merged_longitude = existing_addr.longitude
                        merged_accuracy = existing_addr.geocoding_accuracy
                        merged_source = existing_addr.geocoding_source
                        self.logger.info("🔄 Preservando geocoding existente", 
                            lat=merged_latitude, lng=merged_longitude, source=merged_source)
                    
                    # Debug: verificar campos finais
                    self.logger.info("DEBUG: Campos de geocoding finais", 
                        latitude=merged_latitude or 'AUSENTE',
                        longitude=merged_longitude or 'AUSENTE',
                        geocoding_accuracy=merged_accuracy or 'AUSENTE',
                        geocoding_source=merged_source or 'AUSENTE'
                    )

                    address_db = Address(
                        addressable_id=company_db.person_id,
                        street=address_data.street,
                        number=getattr(address_data, 'number', None),
                        details=address_data.details,
                        neighborhood=address_data.neighborhood,
                        city=address_data.city,
                        state=address_data.state,
                        zip_code=address_data.zip_code,
                        country=address_data.country,
                        type=address_data.type,
                        is_principal=address_data.is_principal,
                        # Geocoding fields com merge inteligente
                        latitude=merged_latitude,
                        longitude=merged_longitude,
                        google_place_id=getattr(address_data, 'google_place_id', None),
                        formatted_address=getattr(address_data, 'formatted_address', None),
                        geocoding_accuracy=merged_accuracy,
                        geocoding_source=merged_source,
                        # Validation fields
                        is_validated=getattr(address_data, 'is_validated', False),
                        validation_source=getattr(address_data, 'validation_source', None),
                        last_validated_at=self._to_naive_datetime(getattr(address_data, 'last_validated_at', None)),
                        # IBGE codes - usar acesso direto e preservar existentes se não fornecidos
                        ibge_city_code=(address_data.ibge_city_code if hasattr(address_data, 'ibge_city_code') else None) or (existing_addr.ibge_city_code if existing_addr else None),
                        ibge_state_code=(address_data.ibge_state_code if hasattr(address_data, 'ibge_state_code') else None) or (existing_addr.ibge_state_code if existing_addr else None),
                        gia_code=(address_data.gia_code if hasattr(address_data, 'gia_code') else None) or (existing_addr.gia_code if existing_addr else None),
                        siafi_code=(address_data.siafi_code if hasattr(address_data, 'siafi_code') else None) or (existing_addr.siafi_code if existing_addr else None),
                        area_code=(address_data.area_code if hasattr(address_data, 'area_code') else None) or (existing_addr.area_code if existing_addr else None),
                        # API data
                        api_data=getattr(address_data, 'api_data', None)
                    )

                    self.logger.info("✅ Endereço salvo com geocoding preservado", address_db_data={
                        'latitude': address_db.latitude,
                        'longitude': address_db.longitude,
                        'geocoding_accuracy': address_db.geocoding_accuracy,
                        'geocoding_source': address_db.geocoding_source,
                        'ibge_city_code': address_db.ibge_city_code,
                        'gia_code': address_db.gia_code,
                        'siafi_code': address_db.siafi_code,
                        'area_code': address_db.area_code
                    })

                    self.db.add(address_db)
            
            await self.db.commit()
            
            # Return updated company
            return await self.get_company(company_id)
            
        except Exception as e:
            await self.db.rollback()
            raise e

    async def delete_company(self, company_id: int) -> bool:
        """
        Inactivate company instead of deleting (business rule: companies cannot be deleted)
        Changes status to 'inactive' but preserves all data and relationships
        """
        try:
            # Get existing company
            query = select(Company).where(and_(Company.id == company_id, Company.deleted_at.is_(None)))
            result = await self.db.execute(query)
            company_db = result.scalars().first()
            
            if not company_db:
                return False
            
            # Get related people record
            people_query = select(People).where(People.id == company_db.person_id)
            people_result = await self.db.execute(people_query)
            people_db = people_result.scalars().first()
            
            if people_db:
                # Change status to inactive instead of soft delete
                people_db.status = 'inactive'
                # Do NOT set deleted_at - preserve data for relationships
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            raise e

    async def get_company_by_cnpj(self, cnpj: str) -> Optional[CompanyDetailed]:
        """Get a company by CNPJ with all related data"""
        # Remove formatação do CNPJ
        clean_cnpj = cnpj.replace(".", "").replace("/", "").replace("-", "")

        query = (
            select(Company)
            .options(
                joinedload(Company.people).selectinload(People.phones),
                joinedload(Company.people).selectinload(People.emails),
                joinedload(Company.people).selectinload(People.addresses)
            )
            .join(People, Company.person_id == People.id)
            .where(and_(
                Company.deleted_at.is_(None),
                People.deleted_at.is_(None),
                People.tax_id == clean_cnpj
            ))
        )

        result = await self.db.execute(query)
        company_db = result.scalars().first()

        if not company_db:
            return None

        # Convert to dict and fix metadata field mapping (same as get_company)
        company_dict = {
            'id': company_db.id,
            'person_id': company_db.person_id,
            'settings': company_db.settings,
            'metadata': company_db.metadata_,  # Map metadata_ to metadata
            'display_order': company_db.display_order,
            'created_at': company_db.created_at,
            'updated_at': company_db.updated_at,
            'deleted_at': company_db.deleted_at,
            'people': {
                'id': company_db.people.id,
                'person_type': company_db.people.person_type,
                'name': company_db.people.name,
                'trade_name': company_db.people.trade_name,
                'tax_id': company_db.people.tax_id,
                'secondary_tax_id': company_db.people.secondary_tax_id,
                'birth_date': company_db.people.birth_date,
                'incorporation_date': company_db.people.incorporation_date,
                'gender': company_db.people.gender,
                'marital_status': company_db.people.marital_status,
                'occupation': company_db.people.occupation,
                'tax_regime': company_db.people.tax_regime,
                'legal_nature': company_db.people.legal_nature,
                'municipal_registration': company_db.people.municipal_registration,
                'website': company_db.people.website,
                'description': company_db.people.description,
                'status': company_db.people.status,
                'is_active': company_db.people.is_active,
                'lgpd_consent_version': company_db.people.lgpd_consent_version,
                'lgpd_consent_given_at': company_db.people.lgpd_consent_given_at,
                'lgpd_data_retention_expires_at': company_db.people.lgpd_data_retention_expires_at,
                'created_at': company_db.people.created_at,
                'updated_at': company_db.people.updated_at,
                'deleted_at': company_db.people.deleted_at
            },
            'phones': [
                {
                    'id': phone.id,
                    'country_code': phone.country_code,
                    'number': phone.number,
                    'extension': phone.extension,
                    'type': phone.type,
                    'is_principal': phone.is_principal,
                    'is_active': phone.is_active,
                    'phone_name': phone.phone_name,
                    'is_whatsapp': phone.is_whatsapp,
                    'whatsapp_formatted': phone.whatsapp_formatted,
                    'whatsapp_verified': phone.whatsapp_verified,
                    'whatsapp_verified_at': phone.whatsapp_verified_at,
                    'whatsapp_business': phone.whatsapp_business,
                    'whatsapp_name': phone.whatsapp_name,
                    'accepts_whatsapp_marketing': phone.accepts_whatsapp_marketing,
                    'accepts_whatsapp_notifications': phone.accepts_whatsapp_notifications,
                    'whatsapp_preferred_time_start': phone.whatsapp_preferred_time_start,
                    'whatsapp_preferred_time_end': phone.whatsapp_preferred_time_end,
                    'carrier': phone.carrier,
                    'line_type': phone.line_type,
                    'contact_priority': phone.contact_priority,
                    'can_receive_calls': phone.can_receive_calls,
                    'can_receive_sms': phone.can_receive_sms,
                    'last_contact_attempt': phone.last_contact_attempt,
                    'last_contact_success': phone.last_contact_success,
                    'contact_attempts_count': phone.contact_attempts_count,
                    'verified_at': phone.verified_at,
                    'verification_method': phone.verification_method,
                    'created_at': phone.created_at,
                    'updated_at': phone.updated_at
                } for phone in company_db.people.phones
            ],
            'emails': [
                {
                    'id': email.id,
                    'email_address': email.email_address,
                    'type': email.type,
                    'is_principal': email.is_principal,
                    'is_active': email.is_active,
                    'verified_at': email.verified_at,
                    'created_at': email.created_at,
                    'updated_at': email.updated_at
                } for email in company_db.people.emails
            ],
            'addresses': [
                {
                    'id': addr.id,
                    'street': addr.street,
                    'number': addr.number,
                    'details': addr.details,
                    'neighborhood': addr.neighborhood,
                    'city': addr.city,
                    'state': addr.state,
                    'zip_code': addr.zip_code,
                    'country': addr.country,
                    'type': addr.type,
                    'is_principal': addr.is_principal,
                    'latitude': addr.latitude,
                    'longitude': addr.longitude,
                    'google_place_id': addr.google_place_id,
                    'formatted_address': addr.formatted_address,
                    'geocoding_accuracy': addr.geocoding_accuracy,
                    'geocoding_source': addr.geocoding_source,
                    'ibge_city_code': addr.ibge_city_code,
                    'ibge_state_code': addr.ibge_state_code,
                    'gia_code': addr.gia_code,
                    'siafi_code': addr.siafi_code,
                    'area_code': addr.area_code,
                    'region': addr.region,
                    'microregion': addr.microregion,
                    'mesoregion': addr.mesoregion,
                    'within_coverage': addr.within_coverage,
                    'distance_to_establishment': addr.distance_to_establishment,
                    'estimated_travel_time': addr.estimated_travel_time,
                    'access_difficulty': addr.access_difficulty,
                    'access_notes': addr.access_notes,
                    'quality_score': addr.quality_score,
                    'is_validated': addr.is_validated,
                    'last_validated_at': addr.last_validated_at,
                    'validation_source': addr.validation_source,
                    'api_data': addr.api_data,
                    'created_at': addr.created_at,
                    'updated_at': addr.updated_at
                } for addr in company_db.people.addresses
            ]
        }

        return CompanyDetailed.model_validate(company_dict)

    async def count_companies(self, search: Optional[str] = None, status: Optional[str] = None) -> int:
        """Count total companies with optional filters"""
        query = (
            select(func.count(Company.id))
            .join(People, Company.person_id == People.id)
            .where(and_(Company.deleted_at.is_(None), People.deleted_at.is_(None)))
        )

        # Add search filter
        if search:
            search_filter = or_(
                People.name.ilike(f"%{search}%"),
                People.trade_name.ilike(f"%{search}%"),
                People.tax_id.ilike(f"%{search}%")
            )
            query = query.where(search_filter)

        # Add status filter
        if status:
            query = query.where(People.status == status)

        result = await self.db.execute(query)
        return result.scalar() or 0