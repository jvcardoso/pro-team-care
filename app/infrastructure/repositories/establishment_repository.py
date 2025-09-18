from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.orm import joinedload

from app.infrastructure.orm.models import Address, Company, Email
from app.infrastructure.orm.models import Establishments as EstablishmentEntity
from app.infrastructure.orm.models import People, Phone
from app.presentation.schemas.company import Address as AddressSchema
from app.presentation.schemas.company import Email as EmailSchema
from app.presentation.schemas.company import Phone as PhoneSchema
from app.presentation.schemas.establishment import (
    EstablishmentCreate,
    EstablishmentDetailed,
    EstablishmentListParams,
    EstablishmentReorderRequest,
    EstablishmentSimple,
    EstablishmentUpdateComplete,
    PersonDetailed,
)

logger = structlog.get_logger()


class EstablishmentRepository:
    def __init__(self, db):
        self.db = db

    def _to_naive_datetime(self, dt):
        """Convert timezone-aware datetime to naive datetime"""
        if dt is None:
            return None
        if hasattr(dt, "replace"):
            return dt.replace(tzinfo=None)
        return dt

    async def create(
        self, establishment_data: EstablishmentCreate
    ) -> EstablishmentDetailed:
        """Criar estabelecimento completo com pessoa e relacionamentos"""
        try:
            # 1. Determinar person_id (existente ou criar novo)
            person_id = None

            if establishment_data.existing_person_id:
                # Reutilizar pessoa existente
                logger.info(
                    f"Reutilizando pessoa existente: {establishment_data.existing_person_id}"
                )

                # Validar se pessoa existe
                existing_person_query = select(People).where(
                    and_(
                        People.id == establishment_data.existing_person_id,
                        People.deleted_at.is_(None),
                    )
                )
                existing_person_result = await self.db.execute(existing_person_query)
                existing_person = existing_person_result.scalar_one_or_none()

                if not existing_person:
                    raise ValueError(
                        f"Pessoa com ID {establishment_data.existing_person_id} não encontrada"
                    )

                person_id = existing_person.id
                tax_id_for_validation = existing_person.tax_id

            elif establishment_data.person:
                # Criar nova pessoa
                logger.info("Criando nova pessoa para o estabelecimento")
                tax_id_for_validation = establishment_data.person.tax_id

            else:
                raise ValueError(
                    "É necessário fornecer 'person' ou 'existing_person_id'"
                )

            # 2. Validar se pode criar establishment
            allow_existing_tax_id = bool(establishment_data.existing_person_id)
            validation = await self.validate_creation(
                establishment_data.company_id,
                establishment_data.code,
                establishment_data.is_principal,
                tax_id_for_validation,
                allow_existing_tax_id,
            )

            if not validation["is_valid"]:
                raise ValueError(validation["error_message"])

            # 3. Criar pessoa se necessário
            if not person_id and establishment_data.person:
                person_entity = People(
                    name=establishment_data.person.name,
                    tax_id=establishment_data.person.tax_id,
                    person_type=establishment_data.person.person_type,
                    status=establishment_data.person.status,
                    description=establishment_data.person.description,
                )
                self.db.add(person_entity)
                await self.db.flush()
                person_id = person_entity.id

            # 4. Criar establishment
            establishment_entity = EstablishmentEntity(
                person_id=person_id,
                company_id=establishment_data.company_id,
                code=establishment_data.code,
                type=establishment_data.type,
                category=establishment_data.category,
                is_active=establishment_data.is_active,
                is_principal=establishment_data.is_principal,
                display_order=validation["suggested_display_order"],
                settings=establishment_data.settings,
                meta_data=establishment_data.metadata,
                operating_hours=establishment_data.operating_hours,
                service_areas=establishment_data.service_areas,
            )
            self.db.add(establishment_entity)
            await self.db.flush()

            await self.db.commit()

            return await self.get_by_id(establishment_entity.id)

        except Exception as e:
            await self.db.rollback()
            logger.error("Error creating establishment", error=str(e))
            raise

    async def get_by_id(self, establishment_id: int) -> Optional[EstablishmentDetailed]:
        """Buscar estabelecimento por ID com todos os relacionamentos"""
        try:
            query = (
                select(EstablishmentEntity)
                .options(
                    joinedload(EstablishmentEntity.person),
                    joinedload(EstablishmentEntity.company).joinedload(Company.people),
                )
                .where(
                    and_(
                        EstablishmentEntity.id == establishment_id,
                        EstablishmentEntity.deleted_at.is_(None),
                    )
                )
            )

            result = await self.db.execute(query)
            establishment_entity = result.scalar_one_or_none()

            if not establishment_entity:
                return None

            return await self._entity_to_detailed_schema(establishment_entity)

        except Exception as e:
            logger.error(
                "Error fetching establishment by ID",
                establishment_id=establishment_id,
                error=str(e),
            )
            raise

    async def get_by_company_and_code(
        self, company_id: int, code: str
    ) -> Optional[EstablishmentSimple]:
        """Buscar estabelecimento por company_id e code"""
        try:
            query = select(EstablishmentEntity).where(
                and_(
                    EstablishmentEntity.company_id == company_id,
                    EstablishmentEntity.code == code,
                    EstablishmentEntity.deleted_at.is_(None),
                )
            )

            result = await self.db.execute(query)
            establishment_entity = result.scalar_one_or_none()

            if not establishment_entity:
                return None

            return EstablishmentSimple(
                id=establishment_entity.id,
                person_id=establishment_entity.person_id,
                company_id=establishment_entity.company_id,
                code=establishment_entity.code,
                type=establishment_entity.type,
                category=establishment_entity.category,
                is_active=establishment_entity.is_active,
                is_principal=establishment_entity.is_principal,
                display_order=establishment_entity.display_order,
                created_at=self._to_naive_datetime(establishment_entity.created_at),
            )

        except Exception as e:
            logger.error(
                "Error fetching establishment by company and code",
                company_id=company_id,
                code=code,
                error=str(e),
            )
            raise

    async def list_establishments(
        self, params: EstablishmentListParams
    ) -> List[EstablishmentDetailed]:
        """Listar estabelecimentos com filtros e paginação"""
        try:
            query = (
                select(EstablishmentEntity)
                .options(
                    joinedload(EstablishmentEntity.person),
                    joinedload(EstablishmentEntity.company).joinedload(Company.people),
                )
                .where(EstablishmentEntity.deleted_at.is_(None))
            )

            # Aplicar filtros
            if params.company_id:
                query = query.where(EstablishmentEntity.company_id == params.company_id)

            if params.is_active is not None:
                query = query.where(EstablishmentEntity.is_active == params.is_active)

            if params.is_principal is not None:
                query = query.where(
                    EstablishmentEntity.is_principal == params.is_principal
                )

            if params.type:
                query = query.where(EstablishmentEntity.type == params.type)

            if params.category:
                query = query.where(EstablishmentEntity.category == params.category)

            if params.search:
                search_filter = or_(
                    People.name.ilike(f"%{params.search}%"),
                    People.tax_id.ilike(f"%{params.search}%"),
                    EstablishmentEntity.code.ilike(f"%{params.search}%"),
                )
                query = query.join(
                    People, EstablishmentEntity.person_id == People.id
                ).where(search_filter)

            # Ordenação
            query = query.order_by(
                EstablishmentEntity.company_id,
                EstablishmentEntity.display_order,
                EstablishmentEntity.code,
            )

            # Paginação
            offset = (params.page - 1) * params.size
            query = query.offset(offset).limit(params.size)

            result = await self.db.execute(query)
            establishment_entities = result.scalars().all()

            establishments = []
            for entity in establishment_entities:
                detailed = await self._entity_to_detailed_schema(entity)
                establishments.append(detailed)

            return establishments

        except Exception as e:
            logger.error("Error listing establishments", error=str(e))
            raise

    async def count_establishments(self, params: EstablishmentListParams) -> int:
        """Contar total de estabelecimentos com filtros"""
        try:
            query = select(func.count(EstablishmentEntity.id)).where(
                EstablishmentEntity.deleted_at.is_(None)
            )

            # Aplicar mesmos filtros da listagem
            if params.company_id:
                query = query.where(EstablishmentEntity.company_id == params.company_id)

            if params.is_active is not None:
                query = query.where(EstablishmentEntity.is_active == params.is_active)

            if params.is_principal is not None:
                query = query.where(
                    EstablishmentEntity.is_principal == params.is_principal
                )

            if params.type:
                query = query.where(EstablishmentEntity.type == params.type)

            if params.category:
                query = query.where(EstablishmentEntity.category == params.category)

            if params.search:
                search_filter = or_(
                    People.name.ilike(f"%{params.search}%"),
                    People.tax_id.ilike(f"%{params.search}%"),
                    EstablishmentEntity.code.ilike(f"%{params.search}%"),
                )
                query = query.join(
                    People, EstablishmentEntity.person_id == People.id
                ).where(search_filter)

            result = await self.db.execute(query)
            return result.scalar() or 0

        except Exception as e:
            logger.error("Error counting establishments", error=str(e))
            raise

    async def update(
        self, establishment_id: int, establishment_data: EstablishmentUpdateComplete
    ) -> EstablishmentDetailed:
        """Atualizar estabelecimento e pessoa relacionada"""
        try:
            # Buscar establishment existente
            query = (
                select(EstablishmentEntity)
                .options(joinedload(EstablishmentEntity.person))
                .where(
                    and_(
                        EstablishmentEntity.id == establishment_id,
                        EstablishmentEntity.deleted_at.is_(None),
                    )
                )
            )

            result = await self.db.execute(query)
            establishment_entity = result.scalar_one_or_none()

            if not establishment_entity:
                raise ValueError(
                    f"Establishment com ID {establishment_id} não encontrado"
                )

            # Validações específicas
            if (
                establishment_data.code
                and establishment_data.code != establishment_entity.code
            ):
                existing = await self.get_by_company_and_code(
                    establishment_entity.company_id, establishment_data.code
                )
                if existing and existing.id != establishment_id:
                    raise ValueError(
                        f"Code '{establishment_data.code}' já existe nesta empresa"
                    )

            if (
                establishment_data.is_principal
                and not establishment_entity.is_principal
            ):
                # Verificar se já existe principal na empresa
                principal_query = select(EstablishmentEntity).where(
                    and_(
                        EstablishmentEntity.company_id
                        == establishment_entity.company_id,
                        EstablishmentEntity.is_principal == True,
                        EstablishmentEntity.deleted_at.is_(None),
                        EstablishmentEntity.id != establishment_id,
                    )
                )
                existing_principal = await self.db.execute(principal_query)
                if existing_principal.scalar_one_or_none():
                    raise ValueError(
                        "Já existe um establishment principal nesta empresa"
                    )

            # Atualizar campos do establishment
            update_fields = establishment_data.dict(
                exclude={"person"}, exclude_none=True
            )
            for field, value in update_fields.items():
                if hasattr(establishment_entity, field):
                    setattr(establishment_entity, field, value)

            # Atualizar pessoa relacionada se fornecida
            if establishment_data.person:
                person_update = establishment_data.person.dict(exclude_none=True)
                for field, value in person_update.items():
                    if hasattr(establishment_entity.person, field):
                        setattr(establishment_entity.person, field, value)

            await self.db.commit()

            return await self.get_by_id(establishment_id)

        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Error updating establishment",
                establishment_id=establishment_id,
                error=str(e),
            )
            raise

    async def delete(self, establishment_id: int) -> bool:
        """Soft delete de estabelecimento"""
        try:
            query = select(EstablishmentEntity).where(
                and_(
                    EstablishmentEntity.id == establishment_id,
                    EstablishmentEntity.deleted_at.is_(None),
                )
            )

            result = await self.db.execute(query)
            establishment_entity = result.scalar_one_or_none()

            if not establishment_entity:
                return False

            # Verificar dependências (users, professionals, clients)
            dependencies = await self._check_dependencies(establishment_id)
            if dependencies:
                raise ValueError(
                    f"Não é possível excluir. Establishment possui: {', '.join(dependencies)}"
                )

            # Soft delete
            establishment_entity.deleted_at = func.now()
            await self.db.commit()

            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Error deleting establishment",
                establishment_id=establishment_id,
                error=str(e),
            )
            raise

    async def reorder(self, reorder_data: EstablishmentReorderRequest) -> bool:
        """Reordenar establishments dentro da empresa"""
        try:
            # Implementação simples: atualizar display_order de cada establishment
            for order_item in reorder_data.establishment_orders:
                establishment_id = order_item["id"]
                new_order = order_item["order"]

                # Atualizar display_order
                update_query = select(EstablishmentEntity).where(
                    and_(
                        EstablishmentEntity.id == establishment_id,
                        EstablishmentEntity.company_id == reorder_data.company_id,
                        EstablishmentEntity.deleted_at.is_(None),
                    )
                )

                result = await self.db.execute(update_query)
                establishment = result.scalar_one_or_none()

                if establishment:
                    establishment.display_order = new_order
                else:
                    logger.warning(
                        f"Establishment {establishment_id} not found for reordering"
                    )

            await self.db.commit()
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error("Error reordering establishments", error=str(e))
            raise

    async def validate_creation(
        self,
        company_id: int,
        code: str,
        is_principal: bool = False,
        tax_id: str = None,
        allow_existing_tax_id: bool = False,
    ) -> Dict[str, Any]:
        """Validar se é possível criar establishment"""
        try:
            # 1. Verificar se empresa existe
            company_query = select(Company).where(
                and_(Company.id == company_id, Company.deleted_at.is_(None))
            )
            company_result = await self.db.execute(company_query)
            company = company_result.scalar_one_or_none()

            if not company:
                return {
                    "is_valid": False,
                    "error_message": f"Empresa com ID {company_id} não encontrada",
                    "suggested_display_order": 1,
                }

            # 1.5. Verificar se CNPJ já existe (apenas se não permitido reutilizar)
            if tax_id and not allow_existing_tax_id:
                existing_person_query = select(People).where(
                    and_(People.tax_id == tax_id, People.deleted_at.is_(None))
                )
                existing_person_result = await self.db.execute(existing_person_query)
                existing_person = existing_person_result.scalar_one_or_none()

                if existing_person:
                    return {
                        "is_valid": False,
                        "error_message": f"CNPJ {tax_id} já existe no sistema",
                        "suggested_display_order": 1,
                    }

            # 2. Verificar se code já existe na empresa
            existing_code_query = select(EstablishmentEntity).where(
                and_(
                    EstablishmentEntity.company_id == company_id,
                    EstablishmentEntity.code == code,
                    EstablishmentEntity.deleted_at.is_(None),
                )
            )
            existing_code_result = await self.db.execute(existing_code_query)
            existing_code = existing_code_result.scalar_one_or_none()

            if existing_code:
                return {
                    "is_valid": False,
                    "error_message": f"Código '{code}' já existe nesta empresa",
                    "suggested_display_order": 1,
                }

            # 3. Se is_principal=True, verificar se já existe principal na empresa
            if is_principal:
                principal_query = select(EstablishmentEntity).where(
                    and_(
                        EstablishmentEntity.company_id == company_id,
                        EstablishmentEntity.is_principal == True,
                        EstablishmentEntity.deleted_at.is_(None),
                    )
                )
                principal_result = await self.db.execute(principal_query)
                existing_principal = principal_result.scalar_one_or_none()

                if existing_principal:
                    return {
                        "is_valid": False,
                        "error_message": "Já existe um estabelecimento principal nesta empresa",
                        "suggested_display_order": 1,
                    }

            # 4. Sugerir próximo display_order
            max_order_query = select(
                func.coalesce(func.max(EstablishmentEntity.display_order), 0)
            ).where(
                and_(
                    EstablishmentEntity.company_id == company_id,
                    EstablishmentEntity.deleted_at.is_(None),
                )
            )
            max_order_result = await self.db.execute(max_order_query)
            max_order = max_order_result.scalar() or 0
            suggested_display_order = max_order + 1

            return {
                "is_valid": True,
                "error_message": "",
                "suggested_display_order": suggested_display_order,
            }

        except Exception as e:
            logger.error("Error validating establishment creation", error=str(e))
            return {
                "is_valid": False,
                "error_message": f"Erro na validação: {str(e)}",
                "suggested_display_order": 1,
            }

    async def _check_dependencies(self, establishment_id: int) -> List[str]:
        """Verificar se establishment possui dependências"""
        dependencies = []

        try:
            # Verificar users
            user_count_query = (
                select(func.count("*"))
                .select_from(text("master.user_establishments"))
                .where(
                    and_(
                        text("establishment_id = :establishment_id"),
                        text("deleted_at IS NULL"),
                    )
                )
            )

            user_result = await self.db.execute(
                user_count_query, {"establishment_id": establishment_id}
            )
            user_count = user_result.scalar() or 0

            if user_count > 0:
                dependencies.append(f"{user_count} usuários")

            # Verificar professionals
            prof_count_query = (
                select(func.count("*"))
                .select_from(text("master.professionals"))
                .where(
                    and_(
                        text("establishment_id = :establishment_id"),
                        text("deleted_at IS NULL"),
                    )
                )
            )

            prof_result = await self.db.execute(
                prof_count_query, {"establishment_id": establishment_id}
            )
            prof_count = prof_result.scalar() or 0

            if prof_count > 0:
                dependencies.append(f"{prof_count} profissionais")

            # Verificar clients
            client_count_query = (
                select(func.count("*"))
                .select_from(text("master.clients"))
                .where(
                    and_(
                        text("establishment_id = :establishment_id"),
                        text("deleted_at IS NULL"),
                    )
                )
            )

            client_result = await self.db.execute(
                client_count_query, {"establishment_id": establishment_id}
            )
            client_count = client_result.scalar() or 0

            if client_count > 0:
                dependencies.append(f"{client_count} clientes")

        except Exception as e:
            logger.error(
                "Error checking dependencies",
                establishment_id=establishment_id,
                error=str(e),
            )

        return dependencies

    async def _get_person_contacts(self, person_id: int) -> Dict[str, List]:
        """Carregar contatos (phones, emails, addresses) de uma pessoa"""
        try:
            # Carregar phones
            phones_query = (
                select(Phone)
                .where(
                    and_(Phone.phoneable_id == person_id, Phone.deleted_at.is_(None))
                )
                .order_by(Phone.is_principal.desc(), Phone.id)
            )
            phones_result = await self.db.execute(phones_query)
            phone_entities = phones_result.scalars().all()

            # Carregar emails
            emails_query = (
                select(Email)
                .where(
                    and_(Email.emailable_id == person_id, Email.deleted_at.is_(None))
                )
                .order_by(Email.is_principal.desc(), Email.id)
            )
            emails_result = await self.db.execute(emails_query)
            email_entities = emails_result.scalars().all()

            # Carregar addresses
            addresses_query = (
                select(Address)
                .where(
                    and_(
                        Address.addressable_id == person_id,
                        Address.deleted_at.is_(None),
                    )
                )
                .order_by(Address.is_principal.desc(), Address.id)
            )
            addresses_result = await self.db.execute(addresses_query)
            address_entities = addresses_result.scalars().all()

            # Converter para schemas
            phones = [PhoneSchema.model_validate(phone) for phone in phone_entities]
            emails = [EmailSchema.model_validate(email) for email in email_entities]
            addresses = [
                AddressSchema.model_validate(address) for address in address_entities
            ]

            return {"phones": phones, "emails": emails, "addresses": addresses}

        except Exception as e:
            logger.error(
                "Error loading person contacts", person_id=person_id, error=str(e)
            )
            return {"phones": [], "emails": [], "addresses": []}

    async def _entity_to_detailed_schema(
        self, establishment_entity: EstablishmentEntity
    ) -> EstablishmentDetailed:
        """Convert EstablishmentEntity to EstablishmentDetailed schema"""

        # Person data
        person_data = None
        if establishment_entity.person:
            person_data = PersonDetailed(
                id=establishment_entity.person.id,
                name=establishment_entity.person.name,
                tax_id=establishment_entity.person.tax_id,
                person_type=establishment_entity.person.person_type,
                status=establishment_entity.person.status,
                description=establishment_entity.person.description,
                created_at=self._to_naive_datetime(
                    establishment_entity.person.created_at
                ),
                updated_at=self._to_naive_datetime(
                    establishment_entity.person.updated_at
                ),
            )

        # Company info
        company_name = None
        company_tax_id = None
        if establishment_entity.company:
            # Try to get company people info, but don't fail if not loaded
            try:
                if (
                    hasattr(establishment_entity.company, "people")
                    and establishment_entity.company.people
                ):
                    company_name = establishment_entity.company.people.name
                    company_tax_id = establishment_entity.company.people.tax_id
            except:
                # If company.people is not loaded, just leave as None
                pass

        # Get counters (simplified for now)
        user_count = 0
        professional_count = 0
        client_count = 0

        # Carregar contatos da pessoa relacionada
        contacts = await self._get_person_contacts(establishment_entity.person_id)

        return EstablishmentDetailed(
            id=establishment_entity.id,
            person_id=establishment_entity.person_id,
            company_id=establishment_entity.company_id,
            code=establishment_entity.code,
            type=establishment_entity.type,
            category=establishment_entity.category,
            is_active=establishment_entity.is_active,
            is_principal=establishment_entity.is_principal,
            display_order=establishment_entity.display_order or 0,
            settings=establishment_entity.settings,
            metadata=establishment_entity.meta_data,
            operating_hours=establishment_entity.operating_hours,
            service_areas=establishment_entity.service_areas,
            created_at=self._to_naive_datetime(establishment_entity.created_at),
            updated_at=self._to_naive_datetime(establishment_entity.updated_at),
            person=person_data,
            company_name=company_name,
            company_tax_id=company_tax_id,
            user_count=user_count,
            professional_count=professional_count,
            client_count=client_count,
            phones=contacts["phones"],
            emails=contacts["emails"],
            addresses=contacts["addresses"],
        )
