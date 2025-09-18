from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text

from app.infrastructure.auth import get_current_user
from app.infrastructure.database import get_db

router = APIRouter(
    prefix="/simple-db-admin",
    tags=["Simple Database Administration"],
    dependencies=[Depends(get_current_user)],  # Requer autenticação
)


@router.get("/tables", summary="Listar todas as tabelas do banco")
async def list_tables(
    schema: str = Query(default="master", description="Schema do banco"),
    db=Depends(get_db),
):
    """Lista todas as tabelas do schema especificado"""
    try:
        query = text(
            """
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = :schema
            ORDER BY table_name
        """
        )
        result = await db.execute(query, {"schema": schema})
        tables = [{"name": row[0], "type": row[1]} for row in result.fetchall()]

        return {"schema": schema, "tables_count": len(tables), "tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar tabelas: {str(e)}")


@router.get("/table/{table_name}/structure", summary="Estrutura da tabela")
async def get_table_structure(
    table_name: str,
    schema: str = Query(default="master", description="Schema do banco"),
    db=Depends(get_db),
):
    """Obtém a estrutura completa de uma tabela"""
    try:
        # Informações das colunas
        columns_query = text(
            """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE table_schema = :schema AND table_name = :table_name
            ORDER BY ordinal_position
        """
        )

        columns_result = await db.execute(
            columns_query, {"schema": schema, "table_name": table_name}
        )
        columns = []
        for row in columns_result.fetchall():
            columns.append(
                {
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2] == "YES",
                    "default": row[3],
                    "max_length": row[4],
                    "precision": row[5],
                    "scale": row[6],
                }
            )

        return {"table_name": table_name, "schema": schema, "columns": columns}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao obter estrutura da tabela: {str(e)}"
        )


@router.get("/table/{table_name}/data", summary="Dados da tabela")
async def get_table_data(
    table_name: str,
    schema: str = Query(default="master", description="Schema do banco"),
    limit: int = Query(default=50, description="Limite de registros"),
    offset: int = Query(default=0, description="Offset para paginação"),
    order_by: Optional[str] = Query(default=None, description="Coluna para ordenação"),
    order_desc: bool = Query(default=False, description="Ordenação decrescente"),
    db=Depends(get_db),
):
    """Obtém dados de uma tabela com paginação"""
    try:
        # Construir query base
        base_query = f"SELECT * FROM {schema}.{table_name}"
        count_query = f"SELECT COUNT(*) FROM {schema}.{table_name}"

        # Adicionar ordenação se especificada
        if order_by:
            direction = "DESC" if order_desc else "ASC"
            base_query += f" ORDER BY {order_by} {direction}"

        # Adicionar limit e offset
        base_query += f" LIMIT {limit} OFFSET {offset}"

        # Executar queries
        data_result = await db.execute(text(base_query))
        count_result = await db.execute(text(count_query))

        # Processar dados
        rows = data_result.fetchall()
        columns = list(data_result.keys()) if rows else []
        total = count_result.scalar()

        # Converter dados para formato JSON serializable
        data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value = row[i]
                if isinstance(value, datetime):
                    value = value.isoformat()
                row_dict[col] = value
            data.append(row_dict)

        return {
            "table_name": table_name,
            "schema": schema,
            "total_records": total,
            "showing_records": len(data),
            "offset": offset,
            "limit": limit,
            "columns": columns,
            "data": data,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao obter dados da tabela: {str(e)}"
        )


@router.post("/query", summary="Executar query customizada")
async def execute_custom_query(query_data: Dict[str, Any], db=Depends(get_db)):
    """Executa uma query SQL customizada (somente SELECT)"""
    try:
        query_sql = query_data.get("query", "").strip()

        if not query_sql:
            raise HTTPException(status_code=400, detail="Query não pode estar vazia")

        # Verificar se é apenas SELECT (segurança básica)
        if not query_sql.upper().startswith("SELECT"):
            raise HTTPException(
                status_code=400, detail="Apenas queries SELECT são permitidas"
            )

        # Executar query
        result = await db.execute(text(query_sql))

        if result.returns_rows:
            rows = result.fetchall()
            columns = list(result.keys()) if rows else []

            # Converter dados para formato JSON
            data = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    row_dict[col] = value
                data.append(row_dict)

            return {
                "success": True,
                "query": query_sql,
                "columns": columns,
                "rows_returned": len(data),
                "data": data,
            }
        else:
            return {
                "success": True,
                "query": query_sql,
                "message": "Query executada com sucesso (sem retorno de dados)",
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao executar query: {str(e)}")


@router.get("/table/{table_name}/search", summary="Buscar na tabela")
async def search_table(
    table_name: str,
    schema: str = Query(default="master", description="Schema do banco"),
    column: str = Query(..., description="Coluna para busca"),
    value: str = Query(..., description="Valor para buscar"),
    limit: int = Query(default=20, description="Limite de registros"),
    db=Depends(get_db),
):
    """Busca registros em uma tabela por coluna e valor"""
    try:
        # Query de busca com ILIKE para busca case-insensitive
        search_query = text(
            f"""
            SELECT * FROM {schema}.{table_name}
            WHERE CAST({column} AS TEXT) ILIKE :value
            LIMIT :limit
        """
        )

        result = await db.execute(search_query, {"value": f"%{value}%", "limit": limit})

        rows = result.fetchall()
        columns = list(result.keys()) if rows else []

        # Converter dados
        data = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                value_data = row[i]
                if isinstance(value_data, datetime):
                    value_data = value_data.isoformat()
                row_dict[col] = value_data
            data.append(row_dict)

        return {
            "table_name": table_name,
            "search_column": column,
            "search_value": value,
            "results_count": len(data),
            "data": data,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")
