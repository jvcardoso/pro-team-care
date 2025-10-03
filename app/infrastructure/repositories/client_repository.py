from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import Integer, and_, func, or_, select, text
from sqlalchemy.orm import joinedload, selectinload

from app.infrastructure.orm.models import Address
from app.infrastructure.orm.models import Client as ClientEntity
from app.infrastructure.orm.models import Company, Email
from app.infrastructure.orm.models import Establishments as EstablishmentEntity
from app.infrastructure.orm.models import People, Phone
from app.infrastructure.services.tenant_context_service import get_tenant_context
from app.presentation.schemas.client import (
    ClientCreate,
    ClientDetailed,
    ClientListParams,
    ClientSimple,
    ClientUpdateComplete,
    PersonDetailed,
)
from app.presentation.schemas.company import Address as AddressSchema
from app.presentation.schemas.company import Email as EmailSchema
from app.presentation.schemas.company import Phone as PhoneSchema

logger = structlog.get_logger()


class ClientRepository:
    def __init__(self, db):
        self.db = db

    def _to_naive_datetime(self, dt):
        """Convert timezone-aware datetime to naive datetime"""
        if dt is None:
            return None
        if hasattr(dt, "replace"):
            return dt.replace(tzinfo=None)
        return dt

    async def _generate_client_code(self, establishment_id: int) -> str:
        """Gerar código único do cliente no formato {establishment_code}-{sequential}"""
        try:
            # 1. Obter código do estabelecimento
            establishment_query = select(EstablishmentEntity.code).where(
                and_(
                    EstablishmentEntity.id == establishment_id,
                    EstablishmentEntity.deleted_at.is_(None),
                )
            )
            establishment_result = await self.db.execute(establishment_query)
            establishment = establishment_result.scalar_one_or_none()

            if not establishment:
                raise ValueError(
                    f"Estabelecimento com ID {establishment_id} não encontrado"
                )

            establishment_code = establishment

            # 2. Encontrar o próximo número sequencial para este estabelecimento
            # Buscar todos os códigos existentes e processar em Python
            codes_query = select(ClientEntity.client_code).where(
                and_(
                    ClientEntity.establishment_id == establishment_id,
                    ClientEntity.client_code.like(f"{establishment_code}-%"),
                    ClientEntity.deleted_at.is_(None),
                )
            )
            codes_result = await self.db.execute(codes_query)
            existing_codes = codes_result.scalars().all()

            max_sequential = 0
            for code in existing_codes:
                if code and "-" in code:
                    try:
                        sequential_part = code.split("-")[1]
                        sequential = int(sequential_part)
                        if sequential > max_sequential:
                            max_sequential = sequential
                    except (IndexError, ValueError):
                        continue

            # 3. Gerar novo código sequencial
            next_sequential = max_sequential + 1

            return f"{establishment_code}-{next_sequential:03d}"  # Formato: EST001-001

        except Exception as e:
            logger.error(
                "Error generating client code",
                error=str(e),
                establishment_id=establishment_id,
            )
            raise ValueError(f"Erro ao gerar código do cliente: {str(e)}")

    async def create(self, client_data: ClientCreate) -> ClientDetailed:
        """Criar cliente completo com pessoa e relacionamentos"""
        try:
            # 1. Determinar person_id (existente ou criar novo)
            person_id = None

            if client_data.existing_person_id:
                # Reutilizar pessoa existente
                logger.info(
                    f"Reutilizando pessoa existente: {client_data.existing_person_id}"
                )

                # Validar se pessoa existe
                existing_person_query = select(People).where(
                    and_(
                        People.id == client_data.existing_person_id,
                        People.deleted_at.is_(None),
                    )
                )
                existing_person_result = await self.db.execute(existing_person_query)
                existing_person = existing_person_result.scalar_one_or_none()

                if not existing_person:
                    raise ValueError(
                        f"Pessoa com ID {client_data.existing_person_id} não encontrada"
                    )

                person_id = existing_person.id
                tax_id_for_validation = existing_person.tax_id

            elif client_data.person:
                # Criar nova pessoa
                logger.info("Criando nova pessoa para o cliente")
                tax_id_for_validation = client_data.person.tax_id

            else:
                raise ValueError(
                    "É necessário fornecer 'person' ou 'existing_person_id'"
                )

            # 2. Gerar client_code se não fornecido
            final_client_code = client_data.client_code
            if not final_client_code:
                final_client_code = await self._generate_client_code(
                    client_data.establishment_id
                )
                logger.info(f"Generated client code: {final_client_code}")

            # 3. Validar se pode criar client
            allow_existing_tax_id = bool(client_data.existing_person_id)
            validation = await self.validate_creation(
                client_data.establishment_id,
                final_client_code,
                tax_id_for_validation,
                allow_existing_tax_id,
            )

            if not validation["is_valid"]:
                raise ValueError(validation["error_message"])

            # 3. Criar pessoa se necessário
            if not person_id and client_data.person:
                # 🔍 Obter company_id do establishment primeiro
                establishment_query = select(EstablishmentEntity).where(
                    EstablishmentEntity.id == client_data.establishment_id
                )
                establishment_result = await self.db.execute(establishment_query)
                establishment = establishment_result.scalar_one_or_none()

                if not establishment:
                    raise ValueError(
                        f"Estabelecimento ID {client_data.establishment_id} não encontrado"
                    )

                company_id = establishment.company_id
                logger.info(
                    f"Using company_id: {company_id} from establishment: {establishment.id}"
                )

                # 🛡️ Limpar tax_id defensivamente (garantir que está apenas com números)
                import re

                clean_tax_id = (
                    re.sub(r"\D", "", client_data.person.tax_id)
                    if client_data.person.tax_id
                    else ""
                )
                logger.info(
                    f"Tax ID: '{client_data.person.tax_id}' -> '{clean_tax_id}' (cleaned)"
                )

                person_entity = People(
                    company_id=company_id,  # 🔑 Campo obrigatório para multi-tenancy
                    name=client_data.person.name,
                    trade_name=client_data.person.trade_name,
                    tax_id=clean_tax_id,  # Use tax_id limpo
                    secondary_tax_id=client_data.person.secondary_tax_id,
                    person_type=client_data.person.person_type,
                    birth_date=client_data.person.birth_date,
                    gender=client_data.person.gender,
                    marital_status=client_data.person.marital_status,
                    occupation=client_data.person.occupation,
                    incorporation_date=client_data.person.incorporation_date,
                    tax_regime=client_data.person.tax_regime,
                    legal_nature=client_data.person.legal_nature,
                    municipal_registration=client_data.person.municipal_registration,
                    website=client_data.person.website,
                    status=client_data.person.status,
                    description=client_data.person.description,
                    lgpd_consent_version=client_data.person.lgpd_consent_version,
                    metadata=client_data.person.metadata,
                )
                self.db.add(person_entity)
                await self.db.flush()
                person_id = person_entity.id

            # 4. Criar client
            client_entity = ClientEntity(
                person_id=person_id,
                establishment_id=client_data.establishment_id,
                client_code=final_client_code,
                status=client_data.status,
            )
            self.db.add(client_entity)
            await self.db.flush()

            await self.db.commit()

            return await self.get_by_id(client_entity.id)

        except Exception as e:
            await self.db.rollback()
            logger.error("Error creating client", error=str(e))
            raise

    async def get_by_id(self, client_id: int) -> Optional[ClientDetailed]:
        """Buscar cliente por ID com todos os relacionamentos"""
        try:
            query = (
                select(ClientEntity)
                .options(
                    joinedload(ClientEntity.person),
                    joinedload(ClientEntity.establishment).joinedload(
                        EstablishmentEntity.person
                    ),
                )
                .where(
                    and_(
                        ClientEntity.id == client_id,
                        ClientEntity.deleted_at.is_(None),
                    )
                )
            )

            result = await self.db.execute(query)
            client_entity = result.scalar_one_or_none()

            if not client_entity:
                return None

            return await self._entity_to_detailed_schema(client_entity)

        except Exception as e:
            logger.error(
                "Error fetching client by ID",
                client_id=client_id,
                error=str(e),
            )
            raise

    async def get_by_establishment_and_person(
        self, establishment_id: int, person_id: int
    ) -> Optional[ClientSimple]:
        """Buscar cliente por establishment_id e person_id"""
        try:
            query = (
                select(ClientEntity)
                .options(joinedload(ClientEntity.person))
                .where(
                    and_(
                        ClientEntity.establishment_id == establishment_id,
                        ClientEntity.person_id == person_id,
                        ClientEntity.deleted_at.is_(None),
                    )
                )
            )

            result = await self.db.execute(query)
            client_entity = result.scalar_one_or_none()

            if not client_entity:
                return None

            return ClientSimple(
                id=client_entity.id,
                person_id=client_entity.person_id,
                establishment_id=client_entity.establishment_id,
                client_code=client_entity.client_code,
                status=client_entity.status,
                created_at=self._to_naive_datetime(client_entity.created_at),
                name=client_entity.person.name,
                tax_id=client_entity.person.tax_id,
                person_type=client_entity.person.person_type,
            )

        except Exception as e:
            logger.error(
                "Error fetching client by establishment and person",
                establishment_id=establishment_id,
                person_id=person_id,
                error=str(e),
            )
            raise

    async def get_by_establishment_and_code(
        self, establishment_id: int, client_code: str
    ) -> Optional[ClientSimple]:
        """Buscar cliente por establishment_id e client_code"""
        try:
            query = (
                select(ClientEntity)
                .options(joinedload(ClientEntity.person))
                .where(
                    and_(
                        ClientEntity.establishment_id == establishment_id,
                        ClientEntity.client_code == client_code,
                        ClientEntity.deleted_at.is_(None),
                    )
                )
            )

            result = await self.db.execute(query)
            client_entity = result.scalar_one_or_none()

            if not client_entity:
                return None

            return ClientSimple(
                id=client_entity.id,
                person_id=client_entity.person_id,
                establishment_id=client_entity.establishment_id,
                client_code=client_entity.client_code,
                status=client_entity.status,
                created_at=self._to_naive_datetime(client_entity.created_at),
                name=client_entity.person.name,
                tax_id=client_entity.person.tax_id,
                person_type=client_entity.person.person_type,
            )

        except Exception as e:
            logger.error(
                "Error fetching client by establishment and code",
                establishment_id=establishment_id,
                client_code=client_code,
                error=str(e),
            )
            raise

    async def list_clients(self, params: ClientListParams) -> List[ClientDetailed]:
        """Listar clientes com filtros e paginação"""
        try:
            query = (
                select(ClientEntity)
                .options(
                    joinedload(ClientEntity.person),
                    joinedload(ClientEntity.establishment).joinedload(
                        EstablishmentEntity.person
                    ),
                )
                .where(ClientEntity.deleted_at.is_(None))
            )

            # Aplicar filtros
            if params.establishment_id:
                query = query.where(
                    ClientEntity.establishment_id == params.establishment_id
                )

            if params.status:
                query = query.where(ClientEntity.status == params.status)

            if params.person_type:
                query = query.join(People, ClientEntity.person_id == People.id).where(
                    People.person_type == params.person_type
                )

            if params.search:
                search_filter = or_(
                    People.name.ilike(f"%{params.search}%"),
                    People.tax_id.ilike(f"%{params.search}%"),
                    ClientEntity.client_code.ilike(f"%{params.search}%"),
                )
                query = query.join(People, ClientEntity.person_id == People.id).where(
                    search_filter
                )

            # Ordenação
            query = query.order_by(
                ClientEntity.establishment_id,
                ClientEntity.created_at.desc(),
            )

            # Paginação
            offset = (params.page - 1) * params.size
            query = query.offset(offset).limit(params.size)

            result = await self.db.execute(query)
            client_entities = result.scalars().all()

            clients = []
            for entity in client_entities:
                detailed = await self._entity_to_detailed_schema(entity)
                clients.append(detailed)

            return clients

        except Exception as e:
            logger.error("Error listing clients", error=str(e), exc_info=True)
            raise

    async def count_clients(self, params: ClientListParams) -> int:
        """Contar total de clientes com filtros"""
        try:
            query = select(func.count(ClientEntity.id)).where(
                ClientEntity.deleted_at.is_(None)
            )

            # Aplicar mesmos filtros da listagem
            if params.establishment_id:
                query = query.where(
                    ClientEntity.establishment_id == params.establishment_id
                )

            if params.status:
                query = query.where(ClientEntity.status == params.status)

            if params.person_type:
                query = query.join(People, ClientEntity.person_id == People.id).where(
                    People.person_type == params.person_type
                )

            if params.search:
                search_filter = or_(
                    People.name.ilike(f"%{params.search}%"),
                    People.tax_id.ilike(f"%{params.search}%"),
                    ClientEntity.client_code.ilike(f"%{params.search}%"),
                )
                query = query.join(People, ClientEntity.person_id == People.id).where(
                    search_filter
                )

            result = await self.db.execute(query)
            return result.scalar() or 0

        except Exception as e:
            logger.error("Error counting clients", error=str(e))
            raise

    async def list_clients_by_company(
        self, params: ClientListParams, company_id: int
    ) -> List[ClientDetailed]:
        """Listar clientes filtrados por empresa (via establishments)"""
        try:
            query = (
                select(ClientEntity)
                .options(
                    joinedload(ClientEntity.person),
                    joinedload(ClientEntity.establishment).joinedload(
                        EstablishmentEntity.person
                    ),
                )
                .join(
                    EstablishmentEntity,
                    ClientEntity.establishment_id == EstablishmentEntity.id,
                )
                .where(
                    and_(
                        ClientEntity.deleted_at.is_(None),
                        EstablishmentEntity.company_id == company_id,
                        EstablishmentEntity.deleted_at.is_(None),
                    )
                )
            )

            # Aplicar filtros adicionais
            if params.status:
                query = query.where(ClientEntity.status == params.status)

            if params.person_type:
                query = query.join(People, ClientEntity.person_id == People.id).where(
                    People.person_type == params.person_type
                )

            if params.search:
                search_filter = or_(
                    People.name.ilike(f"%{params.search}%"),
                    People.tax_id.ilike(f"%{params.search}%"),
                    ClientEntity.client_code.ilike(f"%{params.search}%"),
                )
                if not query._legacy_facade_select_state._setup_joins:
                    query = query.join(People, ClientEntity.person_id == People.id)
                query = query.where(search_filter)

            # Ordenação (usar alias correto da tabela People)
            query = query.order_by(
                EstablishmentEntity.company_id,
                ClientEntity.establishment_id,
                ClientEntity.id,  # Usar ID do cliente ao invés do nome para evitar conflitos de alias
            )

            # Paginação
            offset = (params.page - 1) * params.size
            query = query.offset(offset).limit(params.size)

            result = await self.db.execute(query)
            client_entities = result.scalars().all()

            clients = []
            for entity in client_entities:
                detailed = await self._entity_to_detailed_schema(entity)
                clients.append(detailed)

            return clients

        except Exception as e:
            logger.error(
                "Error listing clients by company", error=str(e), company_id=company_id
            )
            raise

    async def count_clients_by_company(
        self, params: ClientListParams, company_id: int
    ) -> int:
        """Contar clientes filtrados por empresa (via establishments)"""
        try:
            query = (
                select(func.count(ClientEntity.id))
                .join(
                    EstablishmentEntity,
                    ClientEntity.establishment_id == EstablishmentEntity.id,
                )
                .where(
                    and_(
                        ClientEntity.deleted_at.is_(None),
                        EstablishmentEntity.company_id == company_id,
                        EstablishmentEntity.deleted_at.is_(None),
                    )
                )
            )

            # Aplicar filtros adicionais
            if params.status:
                query = query.where(ClientEntity.status == params.status)

            if params.person_type:
                query = query.join(People, ClientEntity.person_id == People.id).where(
                    People.person_type == params.person_type
                )

            if params.search:
                search_filter = or_(
                    People.name.ilike(f"%{params.search}%"),
                    People.tax_id.ilike(f"%{params.search}%"),
                    ClientEntity.client_code.ilike(f"%{params.search}%"),
                )
                query = query.join(People, ClientEntity.person_id == People.id).where(
                    search_filter
                )

            result = await self.db.execute(query)
            return result.scalar() or 0

        except Exception as e:
            logger.error(
                "Error counting clients by company", error=str(e), company_id=company_id
            )
            raise

    async def update(
        self, client_id: int, client_data: ClientUpdateComplete
    ) -> ClientDetailed:
        """Atualizar cliente e pessoa relacionada"""
        try:
            # Buscar client existente
            query = (
                select(ClientEntity)
                .options(joinedload(ClientEntity.person))
                .where(
                    and_(
                        ClientEntity.id == client_id,
                        ClientEntity.deleted_at.is_(None),
                    )
                )
            )

            result = await self.db.execute(query)
            client_entity = result.scalar_one_or_none()

            if not client_entity:
                raise ValueError(f"Client com ID {client_id} não encontrado")

            # Validações específicas
            if (
                client_data.client_code
                and client_data.client_code != client_entity.client_code
            ):
                existing = await self.get_by_establishment_and_code(
                    client_entity.establishment_id, client_data.client_code
                )
                if existing and existing.id != client_id:
                    raise ValueError(
                        f"Client code '{client_data.client_code}' já existe neste estabelecimento"
                    )

            # Atualizar campos do client
            update_fields = client_data.dict(exclude={"person"}, exclude_none=True)
            for field, value in update_fields.items():
                if hasattr(client_entity, field):
                    setattr(client_entity, field, value)

            # Atualizar pessoa relacionada se fornecida
            if client_data.person:
                person_update = client_data.person.dict(exclude_none=True)
                for field, value in person_update.items():
                    if hasattr(client_entity.person, field):
                        setattr(client_entity.person, field, value)

            await self.db.commit()

            return await self.get_by_id(client_id)

        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Error updating client",
                client_id=client_id,
                error=str(e),
            )
            raise

    async def delete(self, client_id: int) -> bool:
        """Soft delete de cliente"""
        try:
            query = select(ClientEntity).where(
                and_(
                    ClientEntity.id == client_id,
                    ClientEntity.deleted_at.is_(None),
                )
            )

            result = await self.db.execute(query)
            client_entity = result.scalar_one_or_none()

            if not client_entity:
                return False

            # Verificar dependências (appointments, consultations, etc.)
            dependencies = await self._check_dependencies(client_id)
            if dependencies:
                raise ValueError(
                    f"Não é possível excluir. Cliente possui: {', '.join(dependencies)}"
                )

            # Soft delete
            client_entity.deleted_at = func.now()
            await self.db.commit()

            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Error deleting client",
                client_id=client_id,
                error=str(e),
            )
            raise

    async def validate_creation(
        self,
        establishment_id: int,
        client_code: Optional[str],
        tax_id: str,
        allow_existing_tax_id: bool = False,
    ) -> Dict[str, Any]:
        """Validar se é possível criar client"""
        try:
            # 1. Verificar se establishment existe
            establishment_query = select(EstablishmentEntity).where(
                and_(
                    EstablishmentEntity.id == establishment_id,
                    EstablishmentEntity.deleted_at.is_(None),
                )
            )
            establishment_result = await self.db.execute(establishment_query)
            establishment = establishment_result.scalar_one_or_none()

            if not establishment:
                return {
                    "is_valid": False,
                    "error_message": f"Estabelecimento com ID {establishment_id} não encontrado",
                }

            # 2. Determinar tipo de pessoa baseado no tax_id
            person_type = "PJ" if len(tax_id) == 14 else "PF"

            # 3. Verificar se tax_id já existe
            if tax_id:
                existing_person_query = select(People).where(
                    and_(People.tax_id == tax_id, People.deleted_at.is_(None))
                )
                existing_person_result = await self.db.execute(existing_person_query)
                existing_person = existing_person_result.scalar_one_or_none()

                if existing_person:
                    # Verificar se já é cliente neste estabelecimento
                    existing_client_query = select(ClientEntity).where(
                        and_(
                            ClientEntity.person_id == existing_person.id,
                            ClientEntity.establishment_id == establishment_id,
                            ClientEntity.deleted_at.is_(None),
                        )
                    )
                    existing_client_result = await self.db.execute(
                        existing_client_query
                    )
                    existing_client = existing_client_result.scalar_one_or_none()

                    if existing_client:
                        # Pessoa já é cliente neste estabelecimento - BLOQUEAR
                        return {
                            "is_valid": False,
                            "error_message": f"Cliente com {tax_id} já existe neste estabelecimento",
                            "existing_person": {
                                "id": existing_person.id,
                                "name": existing_person.name,
                                "person_type": existing_person.person_type,
                            },
                            "existing_client": {
                                "id": existing_client.id,
                                "client_code": existing_client.client_code,
                                "status": existing_client.status,
                            },
                        }

                    # Pessoa existe globalmente mas não neste estabelecimento
                    if allow_existing_tax_id:
                        # Permitido reutilizar pessoa existente
                        return {
                            "is_valid": True,
                            "error_message": "",
                            "existing_person": {
                                "id": existing_person.id,
                                "name": existing_person.name,
                                "person_type": existing_person.person_type,
                            },
                        }
                    else:
                        # Não permitido reutilizar - informar que pessoa existe
                        return {
                            "is_valid": False,
                            "error_message": f"Pessoa com {tax_id} já existe no sistema. Deseja reutilizar os dados existentes?",
                            "existing_person": {
                                "id": existing_person.id,
                                "name": existing_person.name,
                                "person_type": existing_person.person_type,
                            },
                            "can_reuse": True,
                        }

            # 4. Se client_code fornecido, verificar se já existe no establishment
            if client_code:
                existing_code_query = select(ClientEntity).where(
                    and_(
                        ClientEntity.establishment_id == establishment_id,
                        ClientEntity.client_code == client_code,
                        ClientEntity.deleted_at.is_(None),
                    )
                )
                existing_code_result = await self.db.execute(existing_code_query)
                existing_code = existing_code_result.scalar_one_or_none()

                if existing_code:
                    return {
                        "is_valid": False,
                        "error_message": f"Código '{client_code}' já existe neste estabelecimento",
                    }

            return {
                "is_valid": True,
                "error_message": "",
            }

        except Exception as e:
            logger.error("Error validating client creation", error=str(e))
            return {
                "is_valid": False,
                "error_message": f"Erro na validação: {str(e)}",
            }

    async def _check_dependencies(self, client_id: int) -> List[str]:
        """Verificar se client possui dependências"""
        dependencies = []

        try:
            # Verificar appointments (exemplo - ajustar conforme tabelas reais)
            # appointment_count_query = (
            #     select(func.count("*"))
            #     .select_from(text("master.appointments"))
            #     .where(
            #         and_(
            #             text("client_id = :client_id"),
            #             text("deleted_at IS NULL"),
            #         )
            #     )
            # )

            # appointment_result = await self.db.execute(
            #     appointment_count_query, {"client_id": client_id}
            # )
            # appointment_count = appointment_result.scalar() or 0

            # if appointment_count > 0:
            #     dependencies.append(f"{appointment_count} agendamentos")

            # Por enquanto, não há dependências conhecidas
            # Adicionar conforme necessário no futuro
            pass

        except Exception as e:
            logger.error(
                "Error checking dependencies",
                client_id=client_id,
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
                    and_(
                        Phone.phoneable_type == "people",
                        Phone.phoneable_id == person_id,
                        Phone.deleted_at.is_(None),
                    )
                )
                .order_by(Phone.is_principal.desc(), Phone.id)
            )
            phones_result = await self.db.execute(phones_query)
            phone_entities = phones_result.scalars().all()

            # Carregar emails
            emails_query = (
                select(Email)
                .where(
                    and_(
                        Email.emailable_type == "people",
                        Email.emailable_id == person_id,
                        Email.deleted_at.is_(None),
                    )
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
                        Address.addressable_type == "people",
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
        self, client_entity: ClientEntity
    ) -> ClientDetailed:
        """Convert ClientEntity to ClientDetailed schema"""

        # Person data
        person_data = None
        if client_entity.person:
            person_data = PersonDetailed(
                id=client_entity.person.id,
                name=client_entity.person.name,
                trade_name=client_entity.person.trade_name,
                tax_id=client_entity.person.tax_id,
                secondary_tax_id=client_entity.person.secondary_tax_id,
                person_type=client_entity.person.person_type,
                birth_date=client_entity.person.birth_date,
                gender=client_entity.person.gender,
                marital_status=client_entity.person.marital_status,
                occupation=client_entity.person.occupation,
                incorporation_date=client_entity.person.incorporation_date,
                tax_regime=client_entity.person.tax_regime,
                legal_nature=client_entity.person.legal_nature,
                municipal_registration=client_entity.person.municipal_registration,
                website=client_entity.person.website,
                status=client_entity.person.status,
                description=client_entity.person.description,
                lgpd_consent_version=client_entity.person.lgpd_consent_version,
                metadata={},  # Dicionário vazio como fallback
                created_at=self._to_naive_datetime(client_entity.person.created_at),
                updated_at=self._to_naive_datetime(client_entity.person.updated_at),
            )

        # Establishment info
        establishment_name = None
        establishment_code = None
        establishment_type = None
        company_id = None
        company_name = None

        if client_entity.establishment:
            establishment_code = client_entity.establishment.code
            establishment_type = client_entity.establishment.type
            company_id = client_entity.establishment.company_id

            if client_entity.establishment.person:
                establishment_name = client_entity.establishment.person.name

            # Company name - avoid accessing unloaded relationships
            company_name = ""  # Default empty string

        # Carregar contatos da pessoa relacionada
        contacts = await self._get_person_contacts(client_entity.person_id)

        return ClientDetailed(
            id=client_entity.id,
            person_id=client_entity.person_id,
            establishment_id=client_entity.establishment_id,
            client_code=client_entity.client_code,
            status=client_entity.status,
            created_at=self._to_naive_datetime(client_entity.created_at),
            updated_at=self._to_naive_datetime(client_entity.updated_at),
            name=client_entity.person.name if client_entity.person else f"Cliente {client_entity.id}",
            tax_id=client_entity.person.tax_id if client_entity.person else "",
            person_type=client_entity.person.person_type if client_entity.person else "PF",
            person=person_data,
            establishment_name=establishment_name or "",
            establishment_code=establishment_code or "",
            establishment_type=establishment_type or "",
            company_id=company_id or 0,
            company_name=company_name or "",
            phones=contacts["phones"],
            emails=contacts["emails"],
            addresses=contacts["addresses"],
        )
