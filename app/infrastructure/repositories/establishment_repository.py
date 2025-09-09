from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select, func, and_, or_, text, case
from sqlalchemy.exc import SQLAlchemyError
import structlog

from app.infrastructure.orm.models import Establishments as EstablishmentEntity, People, Company
from app.presentation.schemas.establishment import (
    EstablishmentCreate, 
    EstablishmentUpdate,
    EstablishmentUpdateComplete,
    EstablishmentDetailed, 
    EstablishmentSimple,
    EstablishmentListParams,
    EstablishmentReorderRequest,
    PersonDetailed
)

logger = structlog.get_logger()

class EstablishmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_naive_datetime(self, dt):
        """Convert timezone-aware datetime to naive datetime"""
        if dt is None:
            return None
        if hasattr(dt, 'replace'):
            return dt.replace(tzinfo=None)
        return dt

    async def create(self, establishment_data: EstablishmentCreate) -> EstablishmentDetailed:
        """Criar estabelecimento completo com pessoa e relacionamentos"""
        try:
            # 1. Validar se pode criar establishment
            validation = await self.validate_creation(
                establishment_data.company_id,
                establishment_data.code,
                establishment_data.is_principal
            )
            
            if not validation["is_valid"]:
                raise ValueError(validation["error_message"])

            # 2. Criar pessoa para o establishment
            person_entity = People(
                name=establishment_data.person.name,
                tax_id=establishment_data.person.tax_id,
                person_type=establishment_data.person.person_type,
                status=establishment_data.person.status,
                description=establishment_data.person.description,
            )
            self.db.add(person_entity)
            await self.db.flush()

            # 3. Criar establishment
            establishment_entity = EstablishmentEntity(
                person_id=person_entity.id,
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
                    joinedload(EstablishmentEntity.company).joinedload(Company.people)
                )
                .where(
                    and_(
                        EstablishmentEntity.id == establishment_id,
                        EstablishmentEntity.deleted_at.is_(None)
                    )
                )
            )

            result = await self.db.execute(query)
            establishment_entity = result.scalar_one_or_none()

            if not establishment_entity:
                return None

            return await self._entity_to_detailed_schema(establishment_entity)

        except Exception as e:
            logger.error("Error fetching establishment by ID", establishment_id=establishment_id, error=str(e))
            raise

    async def get_by_company_and_code(self, company_id: int, code: str) -> Optional[EstablishmentSimple]:
        """Buscar estabelecimento por company_id e code"""
        try:
            query = (
                select(EstablishmentEntity)
                .where(
                    and_(
                        EstablishmentEntity.company_id == company_id,
                        EstablishmentEntity.code == code,
                        EstablishmentEntity.deleted_at.is_(None)
                    )
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
                created_at=self._to_naive_datetime(establishment_entity.created_at)
            )

        except Exception as e:
            logger.error("Error fetching establishment by company and code", 
                        company_id=company_id, code=code, error=str(e))
            raise

    async def list_establishments(self, params: EstablishmentListParams) -> List[EstablishmentDetailed]:
        """Listar estabelecimentos com filtros e paginação"""
        try:
            query = (
                select(EstablishmentEntity)
                .options(
                    joinedload(EstablishmentEntity.person),
                    joinedload(EstablishmentEntity.company).joinedload(Company.people)
                )
                .where(EstablishmentEntity.deleted_at.is_(None))
            )

            # Aplicar filtros
            if params.company_id:
                query = query.where(EstablishmentEntity.company_id == params.company_id)
            
            if params.is_active is not None:
                query = query.where(EstablishmentEntity.is_active == params.is_active)
                
            if params.is_principal is not None:
                query = query.where(EstablishmentEntity.is_principal == params.is_principal)
                
            if params.type:
                query = query.where(EstablishmentEntity.type == params.type)
                
            if params.category:
                query = query.where(EstablishmentEntity.category == params.category)

            if params.search:
                search_term = f"%{params.search.lower()}%"
                query = query.join(People, EstablishmentEntity.person_id == People.id).where(
                    or_(
                        func.lower(People.name).like(search_term),
                        func.lower(EstablishmentEntity.code).like(search_term)
                    )
                )

            # Ordenação
            query = query.order_by(
                EstablishmentEntity.company_id,
                EstablishmentEntity.display_order,
                EstablishmentEntity.code
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
                query = query.where(EstablishmentEntity.is_principal == params.is_principal)
                
            if params.type:
                query = query.where(EstablishmentEntity.type == params.type)
                
            if params.category:
                query = query.where(EstablishmentEntity.category == params.category)

            if params.search:
                search_term = f"%{params.search.lower()}%"
                query = query.join(People, EstablishmentEntity.person_id == People.id).where(
                    or_(
                        func.lower(People.name).like(search_term),
                        func.lower(EstablishmentEntity.code).like(search_term)
                    )
                )

            result = await self.db.execute(query)
            return result.scalar() or 0

        except Exception as e:
            logger.error("Error counting establishments", error=str(e))
            raise

    async def update(self, establishment_id: int, establishment_data: EstablishmentUpdateComplete) -> EstablishmentDetailed:
        """Atualizar estabelecimento e pessoa relacionada"""
        try:
            # Buscar establishment existente
            query = (
                select(EstablishmentEntity)
                .options(joinedload(EstablishmentEntity.person))
                .where(
                    and_(
                        EstablishmentEntity.id == establishment_id,
                        EstablishmentEntity.deleted_at.is_(None)
                    )
                )
            )

            result = await self.db.execute(query)
            establishment_entity = result.scalar_one_or_none()

            if not establishment_entity:
                raise ValueError(f"Establishment com ID {establishment_id} não encontrado")

            # Validações específicas
            if establishment_data.code and establishment_data.code != establishment_entity.code:
                existing = await self.get_by_company_and_code(establishment_entity.company_id, establishment_data.code)
                if existing and existing.id != establishment_id:
                    raise ValueError(f"Code '{establishment_data.code}' já existe nesta empresa")

            if establishment_data.is_principal and not establishment_entity.is_principal:
                # Verificar se já existe principal na empresa
                principal_query = select(EstablishmentEntity).where(
                    and_(
                        EstablishmentEntity.company_id == establishment_entity.company_id,
                        EstablishmentEntity.is_principal == True,
                        EstablishmentEntity.deleted_at.is_(None),
                        EstablishmentEntity.id != establishment_id
                    )
                )
                existing_principal = await self.db.execute(principal_query)
                if existing_principal.scalar_one_or_none():
                    raise ValueError("Já existe um establishment principal nesta empresa")

            # Atualizar campos do establishment
            update_fields = establishment_data.dict(exclude={'person'}, exclude_none=True)
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
            logger.error("Error updating establishment", establishment_id=establishment_id, error=str(e))
            raise

    async def delete(self, establishment_id: int) -> bool:
        """Soft delete de estabelecimento"""
        try:
            query = select(EstablishmentEntity).where(
                and_(
                    EstablishmentEntity.id == establishment_id,
                    EstablishmentEntity.deleted_at.is_(None)
                )
            )

            result = await self.db.execute(query)
            establishment_entity = result.scalar_one_or_none()

            if not establishment_entity:
                return False

            # Verificar dependências (users, professionals, clients)
            dependencies = await self._check_dependencies(establishment_id)
            if dependencies:
                raise ValueError(f"Não é possível excluir. Establishment possui: {', '.join(dependencies)}")

            # Soft delete
            establishment_entity.deleted_at = func.now()
            await self.db.commit()

            return True

        except Exception as e:
            await self.db.rollback()
            logger.error("Error deleting establishment", establishment_id=establishment_id, error=str(e))
            raise

    async def reorder(self, reorder_data: EstablishmentReorderRequest) -> bool:
        """Reordenar establishments dentro da empresa"""
        try:
            # Usar função do banco para reordenação
            query = select(
                func.master.reorder_establishments(
                    reorder_data.company_id,
                    text("'" + str(reorder_data.establishment_orders).replace("'", '"') + "'::jsonb")
                )
            )

            result = await self.db.execute(query)
            success = result.scalar()

            if success:
                await self.db.commit()
                return True
            else:
                await self.db.rollback()
                return False

        except Exception as e:
            await self.db.rollback()
            logger.error("Error reordering establishments", error=str(e))
            raise

    async def validate_creation(self, company_id: int, code: str, is_principal: bool = False) -> Dict[str, Any]:
        """Validar se é possível criar establishment"""
        try:
            query = select(
                func.master.validate_establishment_creation(company_id, code, is_principal)
            )

            result = await self.db.execute(query)
            row = result.fetchone()

            if row:
                return {
                    "is_valid": row[0],
                    "error_message": row[1],
                    "suggested_display_order": row[2]
                }
            else:
                return {
                    "is_valid": False,
                    "error_message": "Erro na validação",
                    "suggested_display_order": 1
                }

        except Exception as e:
            logger.error("Error validating establishment creation", error=str(e))
            return {
                "is_valid": False,
                "error_message": f"Erro na validação: {str(e)}",
                "suggested_display_order": 1
            }

    async def _check_dependencies(self, establishment_id: int) -> List[str]:
        """Verificar se establishment possui dependências"""
        dependencies = []
        
        try:
            # Verificar users
            user_count_query = select(func.count("*")).select_from(
                text("master.user_establishments")
            ).where(
                and_(
                    text("establishment_id = :establishment_id"),
                    text("deleted_at IS NULL")
                )
            )
            
            user_result = await self.db.execute(user_count_query, {"establishment_id": establishment_id})
            user_count = user_result.scalar() or 0
            
            if user_count > 0:
                dependencies.append(f"{user_count} usuários")

            # Verificar professionals
            prof_count_query = select(func.count("*")).select_from(
                text("master.professionals")
            ).where(
                and_(
                    text("establishment_id = :establishment_id"),
                    text("deleted_at IS NULL")
                )
            )
            
            prof_result = await self.db.execute(prof_count_query, {"establishment_id": establishment_id})
            prof_count = prof_result.scalar() or 0
            
            if prof_count > 0:
                dependencies.append(f"{prof_count} profissionais")

            # Verificar clients
            client_count_query = select(func.count("*")).select_from(
                text("master.clients")
            ).where(
                and_(
                    text("establishment_id = :establishment_id"),
                    text("deleted_at IS NULL")
                )
            )
            
            client_result = await self.db.execute(client_count_query, {"establishment_id": establishment_id})
            client_count = client_result.scalar() or 0
            
            if client_count > 0:
                dependencies.append(f"{client_count} clientes")

        except Exception as e:
            logger.error("Error checking dependencies", establishment_id=establishment_id, error=str(e))

        return dependencies

    async def _entity_to_detailed_schema(self, establishment_entity: EstablishmentEntity) -> EstablishmentDetailed:
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
                created_at=self._to_naive_datetime(establishment_entity.person.created_at),
                updated_at=self._to_naive_datetime(establishment_entity.person.updated_at)
            )

        # Company info
        company_name = None
        company_tax_id = None
        if establishment_entity.company and establishment_entity.company.people:
            company_name = establishment_entity.company.people.name
            company_tax_id = establishment_entity.company.people.tax_id

        # Get counters (simplified for now)
        user_count = 0
        professional_count = 0
        client_count = 0

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
            client_count=client_count
        )