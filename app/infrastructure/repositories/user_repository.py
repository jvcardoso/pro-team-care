from datetime import datetime
from typing import Dict, List, Optional, Tuple

from passlib.context import CryptContext
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import selectinload
from structlog import get_logger

# Domain
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepositoryInterface

# ORM Models
from app.infrastructure.orm.models import Address, Email, People, Phone
from app.infrastructure.orm.models import User as UserEntity

# Schemas
from app.presentation.schemas.user import UserCreate, UserDetailed, UserList, UserUpdate


class UserRepository(UserRepositoryInterface):
    """
    Repositório completo de usuários baseado no padrão CompanyRepository
    Implementa CRUD completo com relacionamentos polimórficos
    """

    def __init__(self, db):
        self.db = db
        self.logger = get_logger()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def _to_naive_datetime(self, dt):
        """Convert timezone-aware datetime to naive datetime"""
        if dt is None:
            return None
        if isinstance(dt, datetime) and dt.tzinfo is not None:
            return dt.replace(tzinfo=None)
        return dt

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def _entity_to_domain_user(self, user_entity: UserEntity) -> User:
        """Convert UserEntity to User domain entity"""
        return User(
            id=user_entity.id,
            person_id=user_entity.person_id,
            email_address=user_entity.email_address,
            password=user_entity.password,
            is_active=user_entity.is_active,
            is_system_admin=user_entity.is_system_admin,
            created_at=self._to_naive_datetime(user_entity.created_at),
            updated_at=self._to_naive_datetime(user_entity.updated_at),
            email_verified_at=self._to_naive_datetime(user_entity.email_verified_at),
            remember_token=user_entity.remember_token,
            preferences=user_entity.preferences,
            notification_settings=user_entity.notification_settings,
            two_factor_secret=user_entity.two_factor_secret,
            two_factor_recovery_codes=user_entity.two_factor_recovery_codes,
            last_login_at=self._to_naive_datetime(user_entity.last_login_at),
            password_changed_at=self._to_naive_datetime(
                user_entity.password_changed_at
            ),
            deleted_at=self._to_naive_datetime(user_entity.deleted_at),
        )

    async def create(self, user_data: UserCreate) -> UserDetailed:
        """
        Cria usuário completo com pessoa e relacionamentos
        Baseado no padrão de CompanyRepository.create
        """
        try:
            self.logger.info("Creating new user", email=user_data.email_address)

            # 1. Validar email único
            existing_user = await self.db.execute(
                select(UserEntity).where(
                    UserEntity.email_address == user_data.email_address
                )
            )
            if existing_user.scalar_one_or_none():
                raise ValueError(f"Email {user_data.email_address} já está em uso")

            # 2. Criar pessoa (PF)
            person_data = user_data.person.model_dump()
            person_data["created_at"] = datetime.utcnow()
            person_data["updated_at"] = datetime.utcnow()

            person = People(**person_data)
            self.db.add(person)
            await self.db.flush()  # Para obter o ID

            # 3. Criar usuário
            user_dict = {
                "person_id": person.id,
                "email_address": user_data.email_address,
                "password": self._hash_password(user_data.password),
                "is_active": user_data.is_active,
                "preferences": user_data.preferences or {},
                "notification_settings": user_data.notification_settings or {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            user = UserEntity(**user_dict)
            self.db.add(user)
            await self.db.flush()

            # 4. Criar relacionamentos (telefones, emails, endereços)
            await self._create_user_contacts(user.id, person.id, user_data)

            await self.db.commit()

            # 5. Buscar usuário completo criado
            created_user = await self.get_by_id(user.id)

            self.logger.info(
                "User created successfully",
                user_id=user.id,
                email=user_data.email_address,
            )
            return created_user

        except Exception as e:
            await self.db.rollback()
            self.logger.error("Error creating user", error=str(e))
            raise

    async def _create_user_contacts(
        self, user_id: int, person_id: int, user_data: UserCreate
    ):
        """Criar telefones, emails e endereços do usuário"""

        # Telefones
        for phone_data in user_data.phones or []:
            phone_dict = phone_data.model_dump()
            phone_dict.update(
                {
                    "person_id": person_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            )
            phone = Phone(**phone_dict)
            self.db.add(phone)

        # Emails adicionais
        for email_data in user_data.emails or []:
            email_dict = email_data.model_dump()
            email_dict.update(
                {
                    "person_id": person_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            )
            email = Email(**email_dict)
            self.db.add(email)

        # Endereços
        for address_data in user_data.addresses or []:
            address_dict = address_data.model_dump()
            address_dict.update(
                {
                    "person_id": person_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            )
            address = Address(**address_dict)
            self.db.add(address)

    async def get_by_id(self, user_id: int) -> Optional[UserDetailed]:
        """Buscar usuário completo por ID"""
        try:
            query = (
                select(UserEntity)
                .options(
                    selectinload(UserEntity.person),
                    selectinload(UserEntity.person).selectinload(People.phones),
                    selectinload(UserEntity.person).selectinload(People.emails),
                    selectinload(UserEntity.person).selectinload(People.addresses),
                )
                .where(and_(UserEntity.id == user_id, UserEntity.deleted_at.is_(None)))
            )

            result = await self.db.execute(query)
            user_entity = result.scalar_one_or_none()

            if not user_entity:
                return None

            return await self._entity_to_detailed_schema(user_entity)

        except Exception as e:
            self.logger.error(
                "Error fetching user by ID", user_id=user_id, error=str(e)
            )
            raise

    async def get_by_email(self, email: str) -> Optional[User]:
        """Buscar usuário por email"""
        try:
            query = (
                select(UserEntity)
                .options(selectinload(UserEntity.person))
                .where(
                    and_(
                        UserEntity.email_address == email,
                        UserEntity.deleted_at.is_(None),
                    )
                )
            )

            result = await self.db.execute(query)
            user_entity = result.scalar_one_or_none()

            if not user_entity:
                return None

            return self._entity_to_domain_user(user_entity)

        except Exception as e:
            self.logger.error("Error fetching user by email", email=email, error=str(e))
            raise

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_admin: Optional[bool] = None,
    ) -> Tuple[List[UserList], int]:
        """Listar usuários com filtros e paginação"""
        try:
            # Query base com JOINs otimizados
            base_query = (
                select(
                    UserEntity.id,
                    UserEntity.email_address,
                    UserEntity.is_active,
                    UserEntity.is_system_admin,
                    UserEntity.last_login_at,
                    UserEntity.created_at,
                    People.name.label("person_name"),
                    func.count(func.distinct(Phone.id)).label("phones_count"),
                )
                .select_from(
                    UserEntity.__table__.join(
                        People, UserEntity.person_id == People.id
                    ).outerjoin(Phone, People.id == Phone.phoneable_id)
                )
                .where(UserEntity.deleted_at.is_(None))
                .group_by(
                    UserEntity.id,
                    UserEntity.email_address,
                    UserEntity.is_active,
                    UserEntity.is_system_admin,
                    UserEntity.last_login_at,
                    UserEntity.created_at,
                    People.name,
                )
            )

            # Aplicar filtros
            filters = []

            if search:
                search_filter = or_(
                    People.name.ilike(f"%{search}%"),
                    UserEntity.email_address.ilike(f"%{search}%"),
                )
                filters.append(search_filter)

            if is_active is not None:
                filters.append(UserEntity.is_active == is_active)

            if is_admin is not None:
                filters.append(UserEntity.is_system_admin == is_admin)

            if filters:
                base_query = base_query.where(and_(*filters))

            # Query de contagem
            count_query = (
                select(func.count())
                .select_from(
                    UserEntity.__table__.join(People, UserEntity.person_id == People.id)
                )
                .where(UserEntity.deleted_at.is_(None))
            )

            if filters:
                count_query = count_query.where(and_(*filters))

            # Executar queries
            users_result = await self.db.execute(
                base_query.order_by(UserEntity.created_at.desc())
                .offset(skip)
                .limit(limit)
            )

            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            # Converter para schemas
            users = []
            for row in users_result:
                user_data = {
                    "id": row.id,
                    "person_name": row.person_name,
                    "email_address": row.email_address,
                    "is_active": row.is_active,
                    "is_system_admin": row.is_system_admin,
                    "last_login_at": self._to_naive_datetime(row.last_login_at),
                    "phones_count": row.phones_count,
                    "roles_count": 0,  # TODO: implementar quando tiver sistema de roles
                    "created_at": self._to_naive_datetime(row.created_at),
                }
                users.append(UserList(**user_data))

            return users, total

        except Exception as e:
            self.logger.error("Error listing users", error=str(e))
            raise

    async def update(
        self, user_id: int, user_data: UserUpdate
    ) -> Optional[UserDetailed]:
        """Atualizar usuário"""
        try:
            # Buscar usuário existente
            existing_user = await self.db.execute(
                select(UserEntity).where(
                    and_(UserEntity.id == user_id, UserEntity.deleted_at.is_(None))
                )
            )
            user_entity = existing_user.scalar_one_or_none()

            if not user_entity:
                return None

            # Atualizar dados do usuário
            if user_data.email_address is not None:
                # Verificar email único
                existing_email = await self.db.execute(
                    select(UserEntity).where(
                        and_(
                            UserEntity.email_address == user_data.email_address,
                            UserEntity.id != user_id,
                            UserEntity.deleted_at.is_(None),
                        )
                    )
                )
                if existing_email.scalar_one_or_none():
                    raise ValueError(f"Email {user_data.email_address} já está em uso")

                user_entity.email_address = user_data.email_address

            if user_data.is_active is not None:
                user_entity.is_active = user_data.is_active

            if user_data.preferences is not None:
                user_entity.preferences = user_data.preferences

            if user_data.notification_settings is not None:
                user_entity.notification_settings = user_data.notification_settings

            user_entity.updated_at = datetime.utcnow()

            # Atualizar dados da pessoa se fornecidos
            if user_data.person is not None:
                person = await self.db.get(People, user_entity.person_id)
                if person:
                    person_dict = user_data.person.model_dump()
                    for key, value in person_dict.items():
                        if hasattr(person, key) and value is not None:
                            setattr(person, key, value)
                    person.updated_at = datetime.utcnow()

            # TODO: Atualizar contatos se fornecidos
            # (phones, emails, addresses - implementar conforme necessidade)

            await self.db.commit()

            # Retornar usuário atualizado
            return await self.get_by_id(user_id)

        except Exception as e:
            await self.db.rollback()
            self.logger.error("Error updating user", user_id=user_id, error=str(e))
            raise

    async def delete(self, user_id: int) -> bool:
        """Soft delete do usuário"""
        try:
            user_entity = await self.db.get(UserEntity, user_id)

            if not user_entity or user_entity.deleted_at is not None:
                return False

            user_entity.deleted_at = datetime.utcnow()
            user_entity.updated_at = datetime.utcnow()

            await self.db.commit()

            self.logger.info("User soft deleted", user_id=user_id)
            return True

        except Exception as e:
            await self.db.rollback()
            self.logger.error("Error deleting user", user_id=user_id, error=str(e))
            raise

    async def count(self) -> Dict[str, int]:
        """Contar usuários por status"""
        try:
            total_query = (
                select(func.count())
                .select_from(UserEntity)
                .where(UserEntity.deleted_at.is_(None))
            )

            active_query = (
                select(func.count())
                .select_from(UserEntity)
                .where(
                    and_(UserEntity.deleted_at.is_(None), UserEntity.is_active == True)
                )
            )

            inactive_query = (
                select(func.count())
                .select_from(UserEntity)
                .where(
                    and_(UserEntity.deleted_at.is_(None), UserEntity.is_active == False)
                )
            )

            total_result = await self.db.execute(total_query)
            active_result = await self.db.execute(active_query)
            inactive_result = await self.db.execute(inactive_query)

            return {
                "total": total_result.scalar(),
                "active": active_result.scalar(),
                "inactive": inactive_result.scalar(),
            }

        except Exception as e:
            self.logger.error("Error counting users", error=str(e))
            raise

    async def change_password(self, user_id: int, new_password: str) -> bool:
        """Alterar senha do usuário"""
        try:
            user_entity = await self.db.get(UserEntity, user_id)

            if not user_entity or user_entity.deleted_at is not None:
                return False

            user_entity.password = self._hash_password(new_password)
            user_entity.password_changed_at = datetime.utcnow()
            user_entity.updated_at = datetime.utcnow()

            await self.db.commit()

            self.logger.info("User password changed", user_id=user_id)
            return True

        except Exception as e:
            await self.db.rollback()
            self.logger.error("Error changing password", user_id=user_id, error=str(e))
            raise

    async def _entity_to_detailed_schema(self, user_entity: UserEntity) -> UserDetailed:
        """Converter entidade ORM para schema detalhado"""
        try:
            # Dados básicos do usuário
            user_data = {
                "id": user_entity.id,
                "person_id": user_entity.person_id,
                "email_address": user_entity.email_address,
                "email_verified_at": self._to_naive_datetime(
                    user_entity.email_verified_at
                ),
                "is_active": user_entity.is_active,
                "is_system_admin": user_entity.is_system_admin or False,
                "last_login_at": self._to_naive_datetime(user_entity.last_login_at),
                "preferences": user_entity.preferences or {},
                "notification_settings": user_entity.notification_settings or {},
                "created_at": self._to_naive_datetime(user_entity.created_at),
                "updated_at": self._to_naive_datetime(user_entity.updated_at),
            }

            # Dados da pessoa
            person_data = {
                "id": user_entity.person.id,
                "name": user_entity.person.name,
                "tax_id": user_entity.person.tax_id,
                "birth_date": user_entity.person.birth_date,
                "gender": user_entity.person.gender,
                "person_type": user_entity.person.person_type,
                "status": user_entity.person.status,
                "created_at": self._to_naive_datetime(user_entity.person.created_at),
                "updated_at": self._to_naive_datetime(user_entity.person.updated_at),
            }

            user_data["person"] = person_data

            # Contatos (se carregados)
            user_data["phones"] = []
            user_data["emails"] = []
            user_data["addresses"] = []
            user_data["roles"] = []  # TODO: implementar roles

            if hasattr(user_entity.person, "phones") and user_entity.person.phones:
                for phone in user_entity.person.phones:
                    user_data["phones"].append(
                        {
                            "id": phone.id,
                            "number": phone.number,
                            "phone_type": phone.type,
                            "line_type": phone.line_type,
                            "is_whatsapp": phone.is_whatsapp or False,
                            "is_primary": phone.is_principal or False,
                        }
                    )

            if hasattr(user_entity.person, "emails") and user_entity.person.emails:
                for email in user_entity.person.emails:
                    user_data["emails"].append(
                        {
                            "id": email.id,
                            "email_address": email.email_address,
                            "email_type": email.type,
                            "is_primary": email.is_principal or False,
                            "is_verified": email.verified_at is not None,
                        }
                    )

            if (
                hasattr(user_entity.person, "addresses")
                and user_entity.person.addresses
            ):
                for address in user_entity.person.addresses:
                    user_data["addresses"].append(
                        {
                            "id": address.id,
                            "street": address.street,
                            "number": address.number,
                            "complement": address.details,
                            "neighborhood": address.neighborhood,
                            "city": address.city,
                            "state": address.state,
                            "country": address.country,
                            "postal_code": address.zip_code,
                            "address_type": address.type,
                            "is_primary": address.is_principal or False,
                        }
                    )

            return UserDetailed(**user_data)

        except Exception as e:
            self.logger.error("Error converting entity to schema", error=str(e))
            raise

    # ===== MÉTODOS LEGACY PARA COMPATIBILIDADE =====

    def _orm_to_domain(self, user_orm: UserEntity) -> User:
        """Converter ORM model para domain entity (compatibilidade)"""
        return User(
            id=user_orm.id,
            person_id=user_orm.person_id,
            email_address=user_orm.email_address,
            password=user_orm.password,
            is_active=user_orm.is_active,
            is_system_admin=user_orm.is_system_admin,
            created_at=user_orm.created_at,
            updated_at=user_orm.updated_at,
            email_verified_at=user_orm.email_verified_at,
            remember_token=user_orm.remember_token,
        )

    async def find_by_email(self, email: str) -> Optional[User]:
        """Buscar por email (compatibilidade com auth)"""
        result = await self.get_by_email(email)
        if not result:
            return None

        # Converter para domain entity para compatibilidade
        user_entity = await self.db.execute(
            select(UserEntity).where(UserEntity.email_address == email)
        )
        entity = user_entity.scalar_one_or_none()

        return self._orm_to_domain(entity) if entity else None
