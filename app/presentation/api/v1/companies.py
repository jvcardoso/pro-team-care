from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import get_logger

from app.infrastructure.database import get_db
from app.infrastructure.repositories.company_repository import CompanyRepository
from app.domain.models.company import (
    CompanyCreate, CompanyUpdate, CompanyDetailed, CompanyList
)

router = APIRouter()

logger = get_logger()


async def get_company_repository(db: AsyncSession = Depends(get_db)) -> CompanyRepository:
    """Dependency to get company repository"""
    return CompanyRepository(db)


@router.post("/", response_model=CompanyDetailed, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    repository: CompanyRepository = Depends(get_company_repository)
):
    """
    Create a new company with all related data
    
    - **people**: Company personal data (name, tax_id, etc.)
    - **company**: Company specific settings and metadata
    - **phones**: List of phone numbers (optional)
    - **emails**: List of email addresses (optional)
    - **addresses**: List of addresses (optional)
    """
    try:
        logger.info("Criando empresa", company_data=company_data.model_dump())

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

        result = await repository.create_company(company_data)
        logger.info("Empresa criada com sucesso", company_id=result.id)

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

        # Log detalhado para debug
        error_detail = f"Error creating company: {str(e)}"
        logger.error("Erro interno detalhado", error_detail=error_detail)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.get("/", response_model=List[CompanyList])
async def get_companies(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search in name, trade_name or tax_id"),
    status: Optional[str] = Query(None, description="Filter by status"),
    repository: CompanyRepository = Depends(get_company_repository)
):
    """
    Get list of companies with filtering and pagination
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    - **search**: Search term for name, trade_name or tax_id
    - **status**: Filter by company status (active, inactive, etc.)
    """
    return await repository.get_companies(skip=skip, limit=limit, search=search, status=status)


@router.get("/count")
async def count_companies(
    search: Optional[str] = Query(None, description="Search in name, trade_name or tax_id"),
    status: Optional[str] = Query(None, description="Filter by status"),
    repository: CompanyRepository = Depends(get_company_repository)
):
    """
    Get total count of companies with optional filters
    
    - **search**: Search term for name, trade_name or tax_id
    - **status**: Filter by company status
    """
    total = await repository.count_companies(search=search, status=status)
    return {"total": total}


@router.get("/{company_id}", response_model=CompanyDetailed)
async def get_company(
    company_id: int,
    repository: CompanyRepository = Depends(get_company_repository)
):
    """
    Get a specific company with all related data
    
    - **company_id**: Company ID to retrieve
    """
    company = await repository.get_company(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return company


@router.put("/{company_id}", response_model=CompanyDetailed)
async def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    repository: CompanyRepository = Depends(get_company_repository)
):
    """
    Update a company's information
    
    - **company_id**: Company ID to update
    - **company_data**: Updated company information
    """
    try:
        company = await repository.update_company(company_id, company_data)
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empresa não encontrada"
            )
        return company
    except ValueError as e:
        # Erros de validação de regras de negócio
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Erro ao atualizar empresa {company_id}: {str(e)}")  # Log para debug
        
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
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao atualizar empresa: {str(e)}"
        )


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: int,
    repository: CompanyRepository = Depends(get_company_repository)
):
    """
    Delete a company (soft delete)
    
    - **company_id**: Company ID to delete
    """
    success = await repository.delete_company(company_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )


@router.get("/{company_id}/contacts")
async def get_company_contacts(
    company_id: int,
    repository: CompanyRepository = Depends(get_company_repository)
):
    """
    Get company contact information (phones and emails only)
    
    - **company_id**: Company ID
    """
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