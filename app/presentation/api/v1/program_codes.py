"""
Endpoints para sistema de códigos de programas
Navegação rápida estilo Datasul via Ctrl+Alt+X
"""

import re
import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db
from app.infrastructure.orm.models import User
from app.presentation.schemas.program_codes import (
    QuickSearchRequest,
    QuickSearchResponse,
    QuickSearchResult,
    ProgramCodeUsageRequest,
    ProgramCodeStatsResponse,
    ProgramCodeResponse,
)

router = APIRouter(prefix="/program-codes", tags=["Program Codes"])


# =====================================================
# BUSCA RÁPIDA (Principal)
# =====================================================


@router.post("/quick-search", response_model=QuickSearchResponse)
async def quick_search(
    request: QuickSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Busca híbrida de códigos de programas

    **Modos de busca:**
    1. Código exato (ex: "em0001") → execução direta
    2. Busca por nome/tokens (ex: "empresa") → lista de resultados

    **Validações:**
    - Filtra apenas códigos ativos
    - Verifica permissões do usuário (TODO)
    - Ordena por relevância

    **Performance:**
    - Cache Redis (TODO)
    - Índices GIN para arrays e trgm
    - Limit 20 resultados
    """
    start_time = time.time()
    query_lower = request.query.lower().strip()

    # =====================================================
    # 1. DETECTAR SE É CÓDIGO EXATO
    # =====================================================
    # Padrão: 2 letras + 4 dígitos (ex: em0001, ct0012)
    code_pattern = re.compile(r"^[a-z]{2}\d{4}$")

    if code_pattern.match(query_lower):
        # Busca exata por código
        stmt = text(
            """
            SELECT
                id,
                shortcode,
                label,
                description,
                route,
                icon,
                module_code,
                program_type,
                'exact' as match_type,
                1.0 as relevance_score
            FROM master.program_codes
            WHERE shortcode = :code
            AND is_active = TRUE
            LIMIT 1
        """
        )

        result = await db.execute(stmt, {"code": query_lower})
        row = result.fetchone()

        if row:
            search_result = QuickSearchResult(
                shortcode=row.shortcode,
                label=row.label,
                description=row.description,
                route=row.route,
                icon=row.icon,
                module_code=row.module_code,
                program_type=row.program_type,
                match_type="exact",
                relevance_score=1.0,
            )

            elapsed_ms = (time.time() - start_time) * 1000

            return QuickSearchResponse(
                query=request.query,
                execution_type="direct",  # Frontend executa direto
                results=[search_result],
                total_results=1,
                search_time_ms=round(elapsed_ms, 2),
            )

    # =====================================================
    # 2. BUSCA FUZZY POR NOME/TOKENS
    # =====================================================

    # Busca combinada:
    # a) Similaridade no label (pg_trgm)
    # b) Match em search_tokens (array contains)
    # c) Match no description

    stmt = text(
        """
        WITH search_results AS (
            SELECT
                id,
                shortcode,
                label,
                description,
                route,
                icon,
                module_code,
                program_type,
                CASE
                    -- Prioridade 1: Match exato no label (case insensitive)
                    WHEN LOWER(label) = :query THEN 1.0
                    -- Prioridade 2: Label começa com query
                    WHEN LOWER(label) LIKE :query_start THEN 0.9
                    -- Prioridade 3: Label contém query
                    WHEN LOWER(label) LIKE :query_like THEN 0.8
                    -- Prioridade 4: Match em search_tokens
                    WHEN :query = ANY(search_tokens) THEN 0.7
                    -- Prioridade 5: Similaridade pg_trgm
                    ELSE similarity(label, :query)
                END as relevance_score,
                CASE
                    WHEN LOWER(label) = :query THEN 'exact'
                    WHEN :query = ANY(search_tokens) THEN 'token'
                    ELSE 'fuzzy'
                END as match_type
            FROM master.program_codes
            WHERE is_active = TRUE
            AND (
                -- Match em label
                LOWER(label) LIKE :query_like
                -- Match em search_tokens
                OR :query = ANY(search_tokens)
                -- Match em description
                OR LOWER(description) LIKE :query_like
                -- Similaridade pg_trgm > 0.3
                OR similarity(label, :query) > 0.3
            )
        )
        SELECT *
        FROM search_results
        WHERE relevance_score > 0.3
        ORDER BY relevance_score DESC, label ASC
        LIMIT 20
    """
    )

    result = await db.execute(
        stmt,
        {
            "query": query_lower,
            "query_start": f"{query_lower}%",
            "query_like": f"%{query_lower}%",
        },
    )

    rows = result.fetchall()

    # Converter para lista de resultados
    results = [
        QuickSearchResult(
            shortcode=row.shortcode,
            label=row.label,
            description=row.description,
            route=row.route,
            icon=row.icon,
            module_code=row.module_code,
            program_type=row.program_type,
            match_type=row.match_type,
            relevance_score=round(float(row.relevance_score), 2),
        )
        for row in rows
    ]

    elapsed_ms = (time.time() - start_time) * 1000

    # Se encontrou apenas 1 resultado com score alto, pode executar direto
    execution_type = "direct" if len(results) == 1 and results[0].relevance_score >= 0.9 else "select"

    return QuickSearchResponse(
        query=request.query,
        execution_type=execution_type,
        results=results,
        total_results=len(results),
        search_time_ms=round(elapsed_ms, 2),
    )


# =====================================================
# REGISTRAR USO (Analytics)
# =====================================================


@router.post("/register-usage")
async def register_usage(
    request: ProgramCodeUsageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Registra uso de um código para analytics

    **Atualiza:**
    - usage_count (incrementa)
    - last_used_at (timestamp atual)

    **Use-case:**
    - Frontend chama após navegação bem-sucedida
    - Usado para rankings e sugestões
    """
    stmt = text(
        """
        UPDATE master.program_codes
        SET
            usage_count = usage_count + 1,
            last_used_at = CURRENT_TIMESTAMP
        WHERE shortcode = :code
        AND is_active = TRUE
        RETURNING shortcode, usage_count
    """
    )

    result = await db.execute(stmt, {"code": request.shortcode})
    await db.commit()

    row = result.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Código '{request.shortcode}' não encontrado",
        )

    return {
        "success": True,
        "shortcode": row.shortcode,
        "usage_count": row.usage_count,
        "message": "Uso registrado com sucesso",
    }


# =====================================================
# ESTATÍSTICAS
# =====================================================


@router.get("/stats", response_model=ProgramCodeStatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Estatísticas de uso dos códigos

    **Retorna:**
    - Total de códigos
    - Códigos ativos
    - Top 10 mais usados
    - Top 10 recentes
    """

    # Total e ativos
    stmt_counts = text(
        """
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE is_active = TRUE) as active
        FROM master.program_codes
    """
    )
    result = await db.execute(stmt_counts)
    counts = result.fetchone()

    # Top 10 mais usados
    stmt_most_used = text(
        """
        SELECT
            shortcode,
            label,
            description,
            route,
            icon,
            module_code,
            program_type,
            usage_count
        FROM master.program_codes
        WHERE is_active = TRUE
        ORDER BY usage_count DESC, last_used_at DESC NULLS LAST
        LIMIT 10
    """
    )
    result = await db.execute(stmt_most_used)
    most_used = [
        QuickSearchResult(
            shortcode=row.shortcode,
            label=row.label,
            description=row.description,
            route=row.route,
            icon=row.icon,
            module_code=row.module_code,
            program_type=row.program_type,
            match_type="stats",
            relevance_score=1.0,
        )
        for row in result.fetchall()
    ]

    # Top 10 recentes
    stmt_recent = text(
        """
        SELECT
            shortcode,
            label,
            description,
            route,
            icon,
            module_code,
            program_type,
            last_used_at
        FROM master.program_codes
        WHERE is_active = TRUE
        AND last_used_at IS NOT NULL
        ORDER BY last_used_at DESC
        LIMIT 10
    """
    )
    result = await db.execute(stmt_recent)
    recently_used = [
        QuickSearchResult(
            shortcode=row.shortcode,
            label=row.label,
            description=row.description,
            route=row.route,
            icon=row.icon,
            module_code=row.module_code,
            program_type=row.program_type,
            match_type="stats",
            relevance_score=1.0,
        )
        for row in result.fetchall()
    ]

    return ProgramCodeStatsResponse(
        total_codes=counts.total,
        active_codes=counts.active,
        most_used=most_used,
        recently_used=recently_used,
    )


# =====================================================
# LISTAR TODOS (Admin)
# =====================================================


@router.get("/", response_model=List[ProgramCodeResponse])
async def list_codes(
    skip: int = 0,
    limit: int = 100,
    module: str = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lista todos os códigos cadastrados

    **Filtros:**
    - module: filtrar por módulo (ex: EM, CT, CL)
    - active_only: apenas códigos ativos
    """
    stmt = text(
        """
        SELECT
            id,
            shortcode,
            module_code,
            program_type,
            label,
            description,
            route,
            icon,
            search_tokens,
            menu_id,
            usage_count,
            last_used_at,
            created_at,
            updated_at,
            is_active,
            required_permission
        FROM master.program_codes
        WHERE (:active_only = FALSE OR is_active = TRUE)
        AND (:module IS NULL OR module_code = :module)
        ORDER BY module_code, program_type, shortcode
        LIMIT :limit OFFSET :skip
    """
    )

    result = await db.execute(
        stmt,
        {
            "active_only": active_only,
            "module": module,
            "limit": limit,
            "skip": skip,
        },
    )

    rows = result.fetchall()

    return [
        ProgramCodeResponse(
            id=row.id,
            shortcode=row.shortcode,
            module_code=row.module_code,
            program_type=row.program_type,
            label=row.label,
            description=row.description,
            route=row.route,
            icon=row.icon,
            search_tokens=row.search_tokens or [],
            menu_id=row.menu_id,
            usage_count=row.usage_count,
            last_used_at=row.last_used_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
            is_active=row.is_active,
            required_permission=row.required_permission,
        )
        for row in rows
    ]
