#!/usr/bin/env python3
"""
Verificar alterações na tabela people após FASE 2B
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def verify_people_table():
    """Verificar estrutura e constraints da tabela people"""

    print("🔍 VERIFICAÇÃO - TABELA PEOPLE")
    print("=" * 50)

    async with engine.begin() as conn:

        # 1. Verificar estrutura das colunas
        print("\n1️⃣ ESTRUTURA DAS COLUNAS:")
        result = await conn.execute(
            text(
                """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'master'
            AND table_name = 'people'
            AND column_name IN ('company_id', 'tax_id')
            ORDER BY ordinal_position;
        """
            )
        )

        columns = list(result)
        for col in columns:
            print(
                f"   - {col.column_name}: {col.data_type} | NULL: {col.is_nullable} | Default: {col.column_default}"
            )

        # 2. Verificar constraints
        print("\n2️⃣ CONSTRAINTS:")
        result = await conn.execute(
            text(
                """
            SELECT conname, contype, pg_get_constraintdef(c.oid) as definition
            FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            JOIN pg_namespace n ON t.relnamespace = n.oid
            WHERE n.nspname = 'master'
            AND t.relname = 'people'
            AND c.contype IN ('u', 'f')
            ORDER BY conname;
        """
            )
        )

        constraints = list(result)
        for constraint in constraints:
            constraint_type = "UNIQUE" if constraint.contype == "u" else "FOREIGN KEY"
            print(
                f"   - {constraint.conname} ({constraint_type}): {constraint.definition}"
            )

        # 3. Verificar índices
        print("\n3️⃣ ÍNDICES:")
        result = await conn.execute(
            text(
                """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'master'
            AND tablename = 'people'
            AND indexname LIKE '%company%'
            ORDER BY indexname;
        """
            )
        )

        indexes = list(result)
        if indexes:
            for idx in indexes:
                print(f"   - {idx.indexname}: {idx.indexdef}")
        else:
            print("   ⚠️ Nenhum índice company relacionado encontrado")

        # 4. Verificar dados
        print("\n4️⃣ DADOS:")
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) as total_people FROM master.people;
        """
            )
        )
        total_people = result.scalar()

        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) as people_with_company
            FROM master.people
            WHERE company_id IS NOT NULL;
        """
            )
        )
        people_with_company = result.scalar()

        result = await conn.execute(
            text(
                """
            SELECT COUNT(DISTINCT company_id) as distinct_companies
            FROM master.people
            WHERE company_id IS NOT NULL;
        """
            )
        )
        distinct_companies = result.scalar()

        print(f"   - Total de pessoas: {total_people}")
        print(f"   - Pessoas com company_id: {people_with_company}")
        print(f"   - Companies distintas: {distinct_companies}")

        # 5. Status geral
        print("\n5️⃣ STATUS GERAL:")

        # Verificar se coluna company_id existe
        company_id_exists = any(col.column_name == "company_id" for col in columns)

        # Verificar se constraint multi-tenant existe
        multi_tenant_constraint = any(
            "company_id" in constraint.definition and "tax_id" in constraint.definition
            for constraint in constraints
        )

        # Verificar se constraint única antiga foi removida
        old_unique_exists = any(
            constraint.definition == "UNIQUE (tax_id)" for constraint in constraints
        )

        print(
            f"   ✅ Coluna company_id existe: {'SIM' if company_id_exists else 'NÃO'}"
        )
        print(
            f"   ✅ Constraint multi-tenant: {'SIM' if multi_tenant_constraint else 'NÃO'}"
        )
        print(
            f"   ✅ Constraint única antiga removida: {'SIM' if not old_unique_exists else 'NÃO'}"
        )
        print(
            f"   ✅ Dados populados: {'SIM' if people_with_company == total_people else 'NÃO'}"
        )

        if (
            company_id_exists
            and multi_tenant_constraint
            and not old_unique_exists
            and people_with_company == total_people
        ):
            print("\n   🎉 FASE 2B CONCLUÍDA COM SUCESSO!")
            print("   ✅ Multi-tenancy implementado na tabela people")
        else:
            print("\n   ⚠️ FASE 2B PARCIALMENTE CONCLUÍDA")
            print("   🔧 Algumas alterações podem precisar de ajustes")


async def main():
    """Função principal"""
    try:
        await verify_people_table()
    except Exception as e:
        print(f"❌ Erro durante verificação: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
