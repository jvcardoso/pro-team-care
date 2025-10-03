"""
Endpoints para ativação de empresas

Este módulo implementa todos os endpoints relacionados ao processo de ativação:
1. POST /send-contract-email - Envia email de aceite de contrato
2. POST /accept-contract - Registra aceite de contrato
3. POST /validate-user-token - Valida token de criação de usuário
4. POST /create-manager-user - Cria usuário gestor
5. GET /status/{company_id} - Consulta status de ativação
6. POST /resend-contract-email - Reenvia email de contrato
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.company_activation_use_case import (
    CompanyActivationUseCase,
)
from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.orm.models import User
from app.presentation.schemas.company_activation import (
    AcceptContractRequest,
    AcceptContractResponse,
    CompanyActivationStatus,
    ResendActivationEmailRequest,
    SendContractEmailRequest,
    SendEmailResponse,
    ValidateActivationTokenRequest,
    ValidateTokenResponse,
)

router = APIRouter(prefix="/company-activation", tags=["company-activation"])


@router.post("/send-contract-email", response_model=SendEmailResponse)
async def send_contract_email(
    request: SendContractEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Envia email de aceite de contrato para empresa

    **Requer autenticação**: Admin do sistema

    **Fluxo**:
    1. Admin cadastra empresa no sistema
    2. Admin clica em "Enviar Email de Ativação"
    3. Sistema gera token único (válido por 7 dias)
    4. Email enviado para o responsável da empresa
    5. Responsável recebe link para aceitar termos

    **Observações**:
    - Empresa deve estar com status 'pending_contract'
    - Se contrato já foi aceito, retorna erro
    - Token expira em 7 dias
    """
    try:
        use_case = CompanyActivationUseCase(db)
        result = await use_case.send_contract_email(
            company_id=request.company_id,
            recipient_email=request.recipient_email,
            recipient_name=request.recipient_name,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}",
        )


@router.post("/accept-contract", response_model=AcceptContractResponse)
async def accept_contract(
    request: AcceptContractRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra aceite de contrato e envia email de criação de usuário

    **Endpoint público** (não requer autenticação)

    **Fluxo**:
    1. Responsável acessa link do email
    2. Lê e aceita os termos de uso
    3. Sistema registra aceite com IP e timestamp (compliance)
    4. Status da empresa: 'pending_contract' → 'pending_user'
    5. Sistema AUTOMATICAMENTE envia email de criação de usuário

    **Próximo passo**:
    - Responsável recebe email para criar conta de gestor
    - Link válido por 24 horas

    **Segurança**:
    - Registra IP de origem (auditoria/compliance)
    - Registra timestamp do aceite
    - Registra nome e email de quem aceitou
    """
    try:
        use_case = CompanyActivationUseCase(db)
        result = await use_case.accept_contract(
            contract_token=request.contract_token,
            accepted_by_name=request.accepted_by_name,
            accepted_by_email=request.accepted_by_email,
            ip_address=request.ip_address,
            terms_version=request.terms_version,
            accepted_by_cpf=request.accepted_by_cpf,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}",
        )


@router.post("/validate-user-token", response_model=ValidateTokenResponse)
async def validate_user_creation_token(
    request: ValidateActivationTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Valida token de criação de usuário gestor

    **Endpoint público** (não requer autenticação)

    **Uso**:
    - Frontend chama este endpoint ao carregar a página de criação
    - Valida se token é válido e não expirou
    - Retorna dados da empresa para exibir no formulário

    **Validações**:
    - Token existe?
    - Token não expirou? (24h)
    - Empresa não foi ativada ainda?
    """
    try:
        use_case = CompanyActivationUseCase(db)
        result = await use_case.validate_user_creation_token(
            user_creation_token=request.token
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}",
        )


@router.post("/create-manager-user")
async def create_manager_user(
    token: str,
    user_name: str,
    user_email: str,
    password: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Cria usuário gestor usando token de criação

    **Endpoint público** (não requer autenticação)

    **Fluxo final**:
    1. Responsável preenche formulário de criação
    2. Sistema cria usuário com context_type='company'
    3. Status da empresa: 'pending_user' → 'active'
    4. Empresa totalmente ativada ✅

    **Dados criados**:
    - Usuário ativo com acesso total à empresa
    - Permissões de gestor da empresa
    - Registro de quem ativou a empresa

    **Pós-ativação**:
    - Usuário pode fazer login
    - Empresa pode criar assinatura
    - Empresa pode criar estabelecimentos
    - Empresa pode criar clientes
    """
    try:
        use_case = CompanyActivationUseCase(db)
        result = await use_case.create_manager_user_from_token(
            user_creation_token=token,
            user_name=user_name,
            user_email=user_email,
            password=password,
        )
        return {
            "success": True,
            "message": "Usuário gestor criado com sucesso! Empresa ativada.",
            "user_id": result["user_id"],
            "email": result["email"],
            "company_id": result["company_id"],
            "access_status": result["access_status"],
            "next_step": "Você já pode fazer login no sistema!",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}",
        )


@router.get("/status/{company_id}", response_model=CompanyActivationStatus)
async def get_company_activation_status(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Consulta status detalhado de ativação da empresa

    **Requer autenticação**: Usuário do sistema

    **Retorna**:
    - Status atual (pending_contract, contract_signed, pending_user, active)
    - Se contrato foi enviado e quando
    - Se contrato foi aceito e por quem
    - Se tem usuário ativo
    - Métricas (dias desde criação, dias sem resposta)
    - Flag de atraso (mais de 7 dias sem ativação)

    **Uso**:
    - Admin visualizar status na lista de empresas
    - Dashboard de empresas pendentes
    - Detalhes da empresa (aba Ativação)
    """
    try:
        use_case = CompanyActivationUseCase(db)
        result = await use_case.get_company_activation_status(company_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}",
        )


@router.post("/resend-contract-email", response_model=SendEmailResponse)
async def resend_contract_email(
    request: ResendActivationEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Reenvia email de aceite de contrato

    **Requer autenticação**: Admin do sistema

    **Quando usar**:
    - Cliente não recebeu o email
    - Email foi para spam
    - Token expirou (7 dias)

    **Observações**:
    - Gera novo token válido por 7 dias
    - Envia para o mesmo email anterior
    - Apenas para empresas com status 'pending_contract'
    """
    try:
        use_case = CompanyActivationUseCase(db)
        result = await use_case.resend_contract_email(request.company_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}",
        )


@router.get("/pending-companies")
async def get_pending_companies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista empresas pendentes de ativação

    **Requer autenticação**: Admin do sistema

    **Retorna**:
    - Empresas com status != 'active'
    - Ordenadas por data de criação (mais recentes primeiro)
    - Inclui métricas de cada empresa

    **Uso**:
    - Dashboard de empresas pendentes
    - Filtro na lista de empresas
    - Relatórios gerenciais
    """
    try:
        from sqlalchemy import select

        from app.infrastructure.orm.models import Company, People

        # Buscar empresas pendentes
        query = (
            select(Company)
            .options(selectinload(Company.people))
            .where(Company.access_status != "active")
            .order_by(Company.created_at.desc())
        )

        result = await db.execute(query)
        companies = result.scalars().all()

        # Criar lista de status
        use_case = CompanyActivationUseCase(db)
        companies_status = []

        for company in companies:
            try:
                company_status = await use_case.get_company_activation_status(
                    company.id
                )
                companies_status.append(company_status)
            except Exception as e:
                print(f"Erro ao processar empresa {company.id}: {e}")
                continue

        # Estatísticas
        stats = {
            "total": len(companies_status),
            "pending_contract": sum(
                1 for c in companies_status if c.access_status == "pending_contract"
            ),
            "contract_signed": sum(
                1 for c in companies_status if c.access_status == "contract_signed"
            ),
            "pending_user": sum(
                1 for c in companies_status if c.access_status == "pending_user"
            ),
            "overdue": sum(1 for c in companies_status if c.is_overdue),
        }

        return {"stats": stats, "companies": companies_status}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}",
        )
