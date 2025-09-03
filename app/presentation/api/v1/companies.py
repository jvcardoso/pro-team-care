from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.infrastructure.database import get_db
from app.infrastructure.repositories.company_repository import CompanyRepository
from app.presentation.schemas.company import (
    CompanyCreate, CompanyUpdate, CompanyDetailed, CompanyList
)

router = APIRouter()

logger = get_logger()


async def get_company_repository(db: AsyncSession = Depends(get_db)) -> CompanyRepository:
    """Dependency to get company repository"""
    return CompanyRepository(db)


@router.post(
    "/", 
    response_model=CompanyDetailed, 
    status_code=status.HTTP_201_CREATED,
    summary="Criar Empresa",
    description="""
    Cria uma nova empresa com todos os dados relacionados (contatos, endereços, etc.).
    
    **Validações automáticas:**
    - CNPJ deve ser válido e único no sistema
    - Email deve ter formato válido
    - Telefone deve seguir padrão brasileiro (DDD + número)
    - CEP será enriquecido automaticamente com dados da ViaCEP
    
    **Campos obrigatórios:**
    - people.name: Nome da empresa
    - people.tax_id: CNPJ da empresa
    - people.person_type: Deve ser "PJ"
    - people.status: Status da empresa (active, inactive, suspended)
    """,
    tags=["Companies"],
    responses={
        201: {
            "description": "Empresa criada com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "person_id": 1,
                        "people": {
                            "name": "Empresa Exemplo LTDA",
                            "trade_name": "Exemplo Corp",
                            "tax_id": "11222333000144",
                            "status": "active"
                        },
                        "phones": [{"number": "11987654321", "type": "commercial"}],
                        "emails": [{"email_address": "contato@exemplo.com", "type": "work"}],
                        "addresses": [{"street": "Avenida Paulista", "city": "São Paulo"}]
                    }
                }
            }
        },
        400: {"description": "Dados inválidos ou CNPJ já existe"},
        401: {"description": "Não autorizado - token JWT inválido"},
        422: {"description": "Erro de validação dos dados enviados"}
    }
)
async def create_company(
    company_data: CompanyCreate,
    repository: CompanyRepository = Depends(get_company_repository)
):
    try:
        logger.info("=== INÍCIO CRIAÇÃO EMPRESA ===")
        logger.info("Dados recebidos", company_data=company_data.model_dump())
        logger.info("Repository obtido", repository_type=type(repository).__name__)

        # Log específico dos endereços
        addresses_data = company_data.addresses or []
        for i, addr in enumerate(addresses_data):
            logger.info(f"Endereço {i+1} recebido", address_data={
                'street': addr.street,
                'number': addr.number,
                'latitude': addr.latitude,
                'longitude': addr.longitude,
                'geocoding_accuracy': getattr(addr, 'geocoding_accuracy', None),
                'geocoding_source': getattr(addr, 'geocoding_source', None),
                'ibge_city_code': getattr(addr, 'ibge_city_code', None),
                'gia_code': getattr(addr, 'gia_code', None),
                'siafi_code': getattr(addr, 'siafi_code', None),
                'area_code': getattr(addr, 'area_code', None)
            })

        logger.info("Chamando repository.create_company...")
        result = await repository.create_company(company_data)
        logger.info("Empresa criada com sucesso", company_id=result.id)
        logger.info("=== FIM CRIAÇÃO EMPRESA ===")

        # Verificar se os dados foram salvos corretamente
        if result.addresses:
            for i, addr in enumerate(result.addresses):
                logger.info(f"Endereço {i+1} salvo", saved_address={
                    'id': addr.id,
                    'latitude': addr.latitude,
                    'longitude': addr.longitude,
                    'geocoding_accuracy': addr.geocoding_accuracy,
                    'geocoding_source': addr.geocoding_source,
                    'ibge_city_code': addr.ibge_city_code,
                    'gia_code': addr.gia_code,
                    'siafi_code': addr.siafi_code,
                    'area_code': addr.area_code
                })

        return result
    except Exception as e:
        logger.error("Erro ao criar empresa", error=str(e), error_type=type(e).__name__)
        logger.error("Detalhes do erro", exc_info=True)

        if "tax_id" in str(e).lower() and "unique" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company with this CNPJ already exists"
            )

        # ✅ Log seguro sem exposição de detalhes internos
        logger.error(
            "Erro interno ao criar empresa", 
            error=str(e), 
            exc_info=True
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor. Contate o suporte."
        )


@router.get(
    "/", 
    response_model=List[CompanyList],
    summary="Listar Empresas",
    description="""
    Retorna lista paginada de empresas com filtros opcionais.
    
    **Funcionalidades:**
    - Paginação com skip/limit
    - Busca por nome, nome fantasia ou CNPJ
    - Filtro por status
    - Contadores de contatos (telefones, emails, endereços)
    
    **Performance:**
    - Máximo 1000 registros por requisição
    - Otimizado para listagens grandes com índices de banco
    """,
    tags=["Companies"],
    responses={
        200: {
            "description": "Lista de empresas retornada com sucesso",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "name": "Empresa Exemplo LTDA",
                            "trade_name": "Exemplo Corp",
                            "tax_id": "11.222.333/0001-44",
                            "status": "active",
                            "phones_count": 2,
                            "emails_count": 1,
                            "addresses_count": 1,
                            "created_at": "2024-01-15T10:30:00Z"
                        }
                    ]
                }
            }
        },
        401: {"description": "Não autorizado - token JWT inválido"},
        422: {"description": "Parâmetros de query inválidos"}
    }
)
async def get_companies(
    skip: int = Query(0, ge=0, description="Número de registros para pular (paginação)"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros para retornar (1-1000)"),
    search: Optional[str] = Query(None, description="Buscar por nome, nome fantasia ou CNPJ"),
    status: Optional[str] = Query(None, description="Filtrar por status (active, inactive, suspended)"),
    repository: CompanyRepository = Depends(get_company_repository)
):
    return await repository.get_companies(skip=skip, limit=limit, search=search, status=status)


@router.get(
    "/count",
    summary="Contar Empresas",
    description="""
    Retorna o total de empresas que atendem aos critérios de filtro.
    
    **Útil para:**
    - Implementar paginação no frontend
    - Estatísticas e relatórios
    - Validar filtros antes de fazer listagem completa
    """,
    tags=["Companies"],
    responses={
        200: {
            "description": "Contagem retornada com sucesso",
            "content": {
                "application/json": {
                    "example": {"total": 150}
                }
            }
        },
        401: {"description": "Não autorizado"}
    }
)
async def count_companies(
    search: Optional[str] = Query(None, description="Buscar por nome, nome fantasia ou CNPJ"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    repository: CompanyRepository = Depends(get_company_repository)
):
    """
    Get total count of companies with optional filters
    
    - **search**: Search term for name, trade_name or tax_id
    - **status**: Filter by company status
    """
    total = await repository.count_companies(search=search, status=status)
    return {"total": total}


@router.get(
    "/{company_id}", 
    response_model=CompanyDetailed,
    summary="Obter Empresa por ID",
    description="""
    Retorna todos os dados de uma empresa específica incluindo contatos completos.
    
    **Dados retornados:**
    - Informações da empresa (nome, CNPJ, status)
    - Todos os telefones cadastrados
    - Todos os emails cadastrados  
    - Todos os endereços com dados de geolocalização
    - Metadados e configurações da empresa
    """,
    tags=["Companies"],
    responses={
        200: {
            "description": "Empresa encontrada com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "people": {
                            "name": "Empresa Exemplo LTDA",
                            "tax_id": "11.222.333/0001-44",
                            "status": "active"
                        },
                        "phones": [{"number": "11987654321", "is_whatsapp": True}],
                        "emails": [{"email_address": "contato@exemplo.com"}],
                        "addresses": [{
                            "street": "Avenida Paulista, 1000",
                            "city": "São Paulo",
                            "latitude": -23.5505,
                            "longitude": -46.6333
                        }]
                    }
                }
            }
        },
        404: {"description": "Empresa não encontrada"},
        401: {"description": "Não autorizado"}
    }
)
async def get_company(
    company_id: int,
    repository: CompanyRepository = Depends(get_company_repository)
):
    company = await repository.get_company(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return company


@router.put(
    "/{company_id}", 
    response_model=CompanyDetailed,
    summary="Atualizar Empresa",
    description="""
    Atualiza os dados de uma empresa existente.
    
    **Funcionalidades:**
    - Atualização parcial ou completa dos dados
    - Validação automática de CNPJ se alterado
    - Atualização de contatos (adicionar/remover/modificar)
    - Enriquecimento automático de novos endereços
    
    **Restrições:**
    - CNPJ não pode ser duplicado no sistema
    - Empresa deve existir e não estar excluída
    """,
    tags=["Companies"],
    responses={
        200: {
            "description": "Empresa atualizada com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "people": {
                            "name": "Empresa Atualizada LTDA",
                            "tax_id": "11.222.333/0001-44",
                            "status": "active"
                        },
                        "updated_at": "2024-01-15T15:30:00Z"
                    }
                }
            }
        },
        400: {"description": "Dados inválidos ou CNPJ duplicado"},
        404: {"description": "Empresa não encontrada"},
        401: {"description": "Não autorizado"}
    }
)
async def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    repository: CompanyRepository = Depends(get_company_repository)
):
    try:
        company = await repository.update_company(company_id, company_data)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa não encontrada"
            )
        return company
    except ValueError as e:
        # ✅ Log estruturado sem exposição de detalhes
        logger.warning(
            "Erro de validação na atualização de empresa",
            company_id=company_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dados inválidos. Verifique as informações fornecidas."
        )
    except Exception as e:
        logger.error(
            "Erro ao atualizar empresa",
            company_id=company_id,
            error=str(e),
            exc_info=True
        )
        
        if "tax_id" in str(e).lower() and "unique" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empresa com este CNPJ já existe"
            )
        if "foreign key constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro de relacionamento de dados. Verifique os campos obrigatórios."
            )
        if "not null constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campo obrigatório não preenchido"
            )
        
        # ✅ Resposta segura sem exposição de detalhes internos
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor. Contate o suporte."
        )


@router.delete(
    "/{company_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir Empresa",
    description="""
    Exclui uma empresa do sistema (exclusão lógica).
    
    **Comportamento:**
    - Exclusão lógica (soft delete) - dados preservados
    - Empresa não aparecerá mais nas listagens
    - Relacionamentos mantidos para auditoria
    - Ação irreversível via API (requer intervenção no banco)
    
    **Segurança:**
    - Requer autenticação válida
    - Operação auditada nos logs
    """,
    tags=["Companies"],
    responses={
        204: {"description": "Empresa excluída com sucesso (sem conteúdo na resposta)"},
        404: {"description": "Empresa não encontrada"},
        401: {"description": "Não autorizado"}
    }
)
async def delete_company(
    company_id: int,
    repository: CompanyRepository = Depends(get_company_repository)
):
    success = await repository.delete_company(company_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )


@router.get("/cnpj/{cnpj}")
async def get_company_by_cnpj(
    cnpj: str,
    repository: CompanyRepository = Depends(get_company_repository)
):
    """
    Get a company by CNPJ with all related data

    - **cnpj**: CNPJ to search for (with or without formatting)
    """
    # Validação básica do CNPJ
    clean_cnpj = cnpj.replace(".", "").replace("/", "").replace("-", "")
    if not clean_cnpj.isdigit() or len(clean_cnpj) != 14:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CNPJ format. Must be 14 digits."
        )

    company = await repository.get_company_by_cnpj(clean_cnpj)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    return company


@router.get(
    "/{company_id}/contacts",
    summary="Obter Contatos da Empresa",
    description="""
    Retorna apenas os contatos (telefones e emails) de uma empresa.
    
    **Otimização:**
    - Endpoint leve para casos que não precisam de todos os dados
    - Útil para componentes de contato rápido
    - Não inclui endereços (use GET /{id} para dados completos)
    
    **Casos de uso:**
    - Listas de contato
    - Integrações de telefonia
    - Envio de emails em massa
    """,
    tags=["Companies"],
    responses={
        200: {
            "description": "Contatos retornados com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "phones": [
                            {
                                "number": "11987654321",
                                "type": "commercial",
                                "is_whatsapp": True,
                                "is_principal": True
                            }
                        ],
                        "emails": [
                            {
                                "email_address": "contato@empresa.com",
                                "type": "work",
                                "is_principal": True
                            }
                        ]
                    }
                }
            }
        },
        404: {"description": "Empresa não encontrada"},
        401: {"description": "Não autorizado"}
    }
)
async def get_company_contacts(
    company_id: int,
    repository: CompanyRepository = Depends(get_company_repository)
):
    company = await repository.get_company(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    return {
        "company_id": company_id,
        "name": company.people.name,
        "trade_name": company.people.trade_name,
        "phones": company.phones,
        "emails": company.emails
    }