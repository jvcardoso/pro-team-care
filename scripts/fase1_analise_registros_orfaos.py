#!/usr/bin/env python3
"""
FASE 1: ANÁLISE DE REGISTROS ÓRFÃOS
Script para identificar dados problemáticos antes da migração multi-tenant
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def analyze_orphan_records():
    """Analisar registros órfãos que podem causar problemas na migração"""

    # Usar engine global

    print("🔍 FASE 1: ANÁLISE DE REGISTROS ÓRFÃOS")
    print("=" * 60)

    async with engine.begin() as conn:

        # 1. PESSOAS SEM EMPRESA (problema crítico)
        print("\n1️⃣ PESSOAS SEM EMPRESA:")
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) as pessoas_sem_empresa
            FROM master.people p
            LEFT JOIN master.companies c ON c.person_id = p.id
            WHERE c.id IS NULL;
        """
            )
        )
        pessoas_sem_empresa = result.scalar()

        if pessoas_sem_empresa > 0:
            print(f"   ⚠️  {pessoas_sem_empresa} pessoas sem empresa (CRÍTICO)")

            # Listar algumas para análise
            result = await conn.execute(
                text(
                    """
                SELECT p.id, p.name, p.tax_id, p.person_type
                FROM master.people p
                LEFT JOIN master.companies c ON c.person_id = p.id
                WHERE c.id IS NULL
                LIMIT 5;
            """
                )
            )

            print("   📋 Exemplos:")
            for row in result:
                print(
                    f"      - ID: {row.id}, Nome: {row.name}, CPF/CNPJ: {row.tax_id}, Tipo: {row.person_type}"
                )
        else:
            print("   ✅ Nenhuma pessoa sem empresa")

        # 2. USUÁRIOS SEM PESSOA (problema crítico)
        print("\n2️⃣ USUÁRIOS SEM PESSOA:")
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) as usuarios_sem_pessoa
            FROM master.users u
            LEFT JOIN master.people p ON p.id = u.person_id
            WHERE p.id IS NULL;
        """
            )
        )
        usuarios_sem_pessoa = result.scalar()

        if usuarios_sem_pessoa > 0:
            print(f"   ⚠️  {usuarios_sem_pessoa} usuários sem pessoa (CRÍTICO)")
        else:
            print("   ✅ Todos os usuários têm pessoa associada")

        # 3. ESTABELECIMENTOS ÓRFÃOS
        print("\n3️⃣ ESTABELECIMENTOS ÓRFÃOS:")
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) as estabelecimentos_orfaos
            FROM master.establishments e
            LEFT JOIN master.companies c ON c.id = e.company_id
            WHERE c.id IS NULL;
        """
            )
        )
        estabelecimentos_orfaos = result.scalar()

        if estabelecimentos_orfaos > 0:
            print(f"   ⚠️  {estabelecimentos_orfaos} estabelecimentos órfãos")
        else:
            print("   ✅ Todos os estabelecimentos têm empresa")

        # 4. CLIENTES ÓRFÃOS
        print("\n4️⃣ CLIENTES ÓRFÃOS:")
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) as clientes_orfaos
            FROM master.clients cl
            LEFT JOIN master.establishments e ON e.id = cl.establishment_id
            WHERE e.id IS NULL;
        """
            )
        )
        clientes_orfaos = result.scalar()

        if clientes_orfaos > 0:
            print(f"   ⚠️  {clientes_orfaos} clientes órfãos")
        else:
            print("   ✅ Todos os clientes têm estabelecimento")

        # 5. ANÁLISE DE DUPLICAÇÃO TAX_ID
        print("\n5️⃣ ANÁLISE DE DUPLICAÇÃO TAX_ID:")
        result = await conn.execute(
            text(
                """
            SELECT tax_id, COUNT(*) as quantidade
            FROM master.people
            WHERE tax_id IS NOT NULL AND tax_id != ''
            GROUP BY tax_id
            HAVING COUNT(*) > 1
            ORDER BY quantidade DESC
            LIMIT 10;
        """
            )
        )

        duplicados = list(result)
        if duplicados:
            print("   ⚠️  TAX_IDs duplicados encontrados:")
            for row in duplicados:
                print(f"      - {row.tax_id}: {row.quantidade} registros")
        else:
            print("   ✅ Nenhum TAX_ID duplicado (constraint funcionando)")

        # 6. ESTATÍSTICAS GERAIS
        print("\n6️⃣ ESTATÍSTICAS GERAIS:")

        # Total de registros por tabela crítica
        tabelas = ["people", "companies", "establishments", "clients", "users"]
        for tabela in tabelas:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM master.{tabela};"))
            count = result.scalar()
            print(f"   📊 {tabela:15}: {count:6} registros")

        # 7. RELACIONAMENTO PEOPLE ↔ COMPANIES
        print("\n7️⃣ RELACIONAMENTO PEOPLE ↔ COMPANIES:")
        result = await conn.execute(
            text(
                """
            SELECT
                COUNT(DISTINCT p.id) as total_pessoas,
                COUNT(DISTINCT c.id) as total_empresas,
                COUNT(DISTINCT c.person_id) as pessoas_com_empresa
            FROM master.people p
            LEFT JOIN master.companies c ON c.person_id = p.id;
        """
            )
        )

        row = result.fetchone()
        print(f"   📊 Total pessoas: {row.total_pessoas}")
        print(f"   📊 Total empresas: {row.total_empresas}")
        print(f"   📊 Pessoas com empresa: {row.pessoas_com_empresa}")

        if row.total_pessoas != row.pessoas_com_empresa:
            print(
                f"   ⚠️  {row.total_pessoas - row.pessoas_com_empresa} pessoas SEM empresa"
            )

        # 8. VERIFICAR CONSTRAINT UNIQUE PROBLEMÁTICA
        print("\n8️⃣ CONSTRAINTS PROBLEMÁTICAS:")
        result = await conn.execute(
            text(
                """
            SELECT conname, contype, pg_get_constraintdef(c.oid) as definition
            FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            JOIN pg_namespace n ON t.relnamespace = n.oid
            WHERE n.nspname = 'master'
            AND t.relname = 'people'
            AND c.contype = 'u'
            AND pg_get_constraintdef(c.oid) LIKE '%tax_id%';
        """
            )
        )

        constraints = list(result)
        for constraint in constraints:
            print(f"   ⚠️  {constraint.conname}: {constraint.definition}")

        print("\n" + "=" * 60)
        print("🎯 RESUMO DA ANÁLISE:")

        # Calcular nível de risco
        total_problemas = (
            pessoas_sem_empresa
            + usuarios_sem_pessoa
            + estabelecimentos_orfaos
            + clientes_orfaos
            + len(duplicados)
        )

        if total_problemas == 0:
            print("✅ RISCO BAIXO: Nenhum registro órfão encontrado")
            print("✅ MIGRAÇÃO PODE PROSSEGUIR SEM PROBLEMAS")
        elif total_problemas <= 10:
            print("⚠️  RISCO MÉDIO: Poucos registros problemáticos")
            print("⚠️  CORREÇÃO NECESSÁRIA ANTES DA MIGRAÇÃO")
        else:
            print("🚨 RISCO ALTO: Muitos registros problemáticos")
            print("🚨 LIMPEZA DE DADOS OBRIGATÓRIA ANTES DA MIGRAÇÃO")

        print(f"\n📊 Total de problemas encontrados: {total_problemas}")


async def main():
    """Função principal"""
    try:
        await analyze_orphan_records()
    except Exception as e:
        print(f"❌ Erro durante análise: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
