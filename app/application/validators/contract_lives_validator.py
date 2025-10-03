"""
Validadores de regras de negócio para Contract Lives
Centraliza lógica de validação complexa para reutilização
"""

from datetime import date
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.orm.models import Contract, ContractLive


class ContractLivesValidator:
    """Validador de regras de negócio para vidas de contratos"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_contract_exists(self, contract_id: int) -> Contract:
        """
        Valida se contrato existe e está ativo

        Args:
            contract_id: ID do contrato

        Returns:
            Contract: Objeto do contrato

        Raises:
            HTTPException 404: Se contrato não existir
            HTTPException 400: Se contrato estiver inativo
        """
        query = select(Contract).where(Contract.id == contract_id)
        result = await self.db.execute(query)
        contract = result.scalar_one_or_none()

        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contrato {contract_id} não encontrado",
            )

        if contract.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contrato {contract_id} está inativo (status: {contract.status})",
            )

        return contract

    async def validate_no_period_overlap(
        self,
        contract_id: int,
        person_id: int,
        start_date: date,
        end_date: Optional[date] = None,
        exclude_life_id: Optional[int] = None,
    ) -> None:
        """
        Valida que não há sobreposição de períodos para a mesma pessoa no contrato

        REGRA DE NEGÓCIO: Uma pessoa não pode ter 2 vínculos ativos simultâneos
        no mesmo contrato.

        Cenários cobertos:
        1. Novo período INICIA antes de período existente TERMINAR
        2. Novo período TERMINA depois de período existente INICIAR
        3. Novo período ENGLOBA completamente período existente
        4. Novo período está CONTIDO em período existente

        Args:
            contract_id: ID do contrato
            person_id: ID da pessoa
            start_date: Data de início do novo período
            end_date: Data de fim do novo período (None = sem fim)
            exclude_life_id: ID da vida a excluir da validação (para updates)

        Raises:
            HTTPException 400: Se houver sobreposição de período
        """

        # Construir query para buscar períodos existentes
        base_query = select(ContractLive).where(
            ContractLive.contract_id == contract_id,
            ContractLive.person_id == person_id,
        )

        # Excluir a própria vida (caso seja update)
        if exclude_life_id:
            base_query = base_query.where(ContractLive.id != exclude_life_id)

        # Lógica de sobreposição de períodos:
        # Dois períodos [A_start, A_end] e [B_start, B_end] SE SOBREPÕEM se:
        # A_start <= B_end AND A_end >= B_start

        if end_date is None:
            # Novo período sem fim (end_date = NULL)
            # Sobrepõe se período existente:
            # 1. Não tem fim (ambos infinitos)
            # 2. Termina após o novo período iniciar
            overlap_condition = or_(
                ContractLive.end_date.is_(None),  # Período existente também sem fim
                ContractLive.end_date >= start_date,  # Período existente termina após novo iniciar
            )
        else:
            # Novo período com fim definido
            # Sobrepõe se:
            # 1. Período existente sem fim E inicia antes do novo terminar
            # 2. Período existente com fim E há interseção de datas
            overlap_condition = or_(
                and_(
                    ContractLive.end_date.is_(None),
                    ContractLive.start_date <= end_date,
                ),
                and_(
                    ContractLive.end_date.isnot(None),
                    ContractLive.start_date <= end_date,
                    ContractLive.end_date >= start_date,
                ),
            )

        query = base_query.where(overlap_condition)

        result = await self.db.execute(query)
        overlapping_life = result.scalar_one_or_none()

        if overlapping_life:
            # Montar mensagem de erro detalhada
            existing_period = (
                f"{overlapping_life.start_date} até "
                f"{overlapping_life.end_date or 'presente'}"
            )
            new_period = f"{start_date} até {end_date or 'presente'}"

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Período sobrepõe vida existente desta pessoa no contrato. "
                    f"Período existente: {existing_period}. "
                    f"Novo período: {new_period}. "
                    f"Uma pessoa não pode ter 2 vínculos ativos simultâneos."
                ),
            )

    async def validate_lives_limits(
        self,
        contract_id: int,
        action: str = "add",
        current_active_count: Optional[int] = None,
    ) -> None:
        """
        Valida limites de vidas do contrato (mínimo, máximo, contratado)

        Args:
            contract_id: ID do contrato
            action: Ação sendo realizada ('add' ou 'remove')
            current_active_count: Contador atual de vidas ativas (opcional, será calculado se None)

        Raises:
            HTTPException 400: Se ação violar limites do contrato
        """
        # Buscar informações do contrato
        contract = await self.validate_contract_exists(contract_id)

        # Contar vidas ativas se não foi fornecido
        if current_active_count is None:
            query = select(ContractLive).where(
                ContractLive.contract_id == contract_id,
                ContractLive.status == "active",
            )
            result = await self.db.execute(query)
            active_lives = result.scalars().all()
            current_active_count = len(active_lives)

        if action == "add":
            # Validar LIMITE MÁXIMO
            if contract.lives_maximum:
                if current_active_count >= contract.lives_maximum:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Limite máximo de vidas atingido. "
                            f"Máximo: {contract.lives_maximum}, "
                            f"Ativas: {current_active_count}"
                        ),
                    )

            # Validar VIDAS CONTRATADAS
            if current_active_count >= contract.lives_contracted:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Todas as vidas contratadas já estão em uso. "
                        f"Contratadas: {contract.lives_contracted}, "
                        f"Ativas: {current_active_count}"
                    ),
                )

        elif action == "remove":
            # Validar LIMITE MÍNIMO
            if contract.lives_minimum:
                if current_active_count <= contract.lives_minimum:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            f"Não é possível remover: mínimo de vidas deve ser mantido. "
                            f"Mínimo: {contract.lives_minimum}, "
                            f"Ativas: {current_active_count}"
                        ),
                    )

    async def validate_date_within_contract_period(
        self, contract_id: int, start_date: date, end_date: Optional[date] = None
    ) -> None:
        """
        Valida que período da vida está dentro do período do contrato

        Args:
            contract_id: ID do contrato
            start_date: Data de início da vida
            end_date: Data de fim da vida (opcional)

        Raises:
            HTTPException 400: Se período estiver fora do contrato
        """
        contract = await self.validate_contract_exists(contract_id)

        # Validar start_date dentro do período do contrato
        if start_date < contract.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Data de início da vida ({start_date}) é anterior ao "
                    f"início do contrato ({contract.start_date})"
                ),
            )

        if contract.end_date and start_date > contract.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Data de início da vida ({start_date}) é posterior ao "
                    f"fim do contrato ({contract.end_date})"
                ),
            )

        # Validar end_date dentro do período do contrato (se fornecido)
        if end_date:
            if contract.end_date and end_date > contract.end_date:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Data de fim da vida ({end_date}) é posterior ao "
                        f"fim do contrato ({contract.end_date})"
                    ),
                )

    async def validate_substitution_allowed(self, life_id: int) -> ContractLive:
        """
        Valida se uma vida pode ser substituída

        Args:
            life_id: ID da vida

        Returns:
            ContractLive: Objeto da vida validado

        Raises:
            HTTPException 404: Se vida não existir
            HTTPException 400: Se substituição não for permitida
        """
        query = select(ContractLive).where(ContractLive.id == life_id)
        result = await self.db.execute(query)
        life = result.scalar_one_or_none()

        if not life:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vida {life_id} não encontrada",
            )

        # Verificar se substituição é permitida
        # Nota: Campo allows_substitution não existe na tabela atual
        # Essa validação pode ser baseada em relationship_type ou outras regras

        # Validar status - apenas vidas ativas podem ser substituídas
        if life.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Apenas vidas ativas podem ser substituídas. Status atual: {life.status}",
            )

        return life
