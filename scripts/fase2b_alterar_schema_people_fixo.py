#!/usr/bin/env python3
"""
FASE 2B: ALTERAÇÃO DE SCHEMA - TABELA PEOPLE (VERSÃO CORRIGIDA)
Script para adicionar company_id na tabela people e alterar constraints
SEM TESTES PROBLEMÁTICOS QUE CAUSAM ROLLBACK
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def alter_people_schema_safe():
    """Adicionar company_id na tabela people e alterar constraints - VERSÃO SEGURA"""

    print("🔧 FASE 2B: ALTERAÇÃO DE SCHEMA - TABELA PEOPLE (VERSÃO CORRIGIDA)")
    print("=" * 70)

    async with engine.begin() as conn:

        # PASSO 1: VERIFICAÇÕES PRÉ-ALTERAÇÃO
        print("\n1️⃣ VERIFICAÇÕES PRÉ-ALTERAÇÃO:")

        # Verificar se coluna company_id já existe
        result = await conn.execute(
            text(
                """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'master'
            AND table_name = 'people'
            AND column_name = 'company_id';
        """
            )
        )
        company_id_exists = result.fetchone()

        if company_id_exists:
            print("   ⚠️  Coluna company_id já existe, script já executado!")
            print("   ✅ Pulando para validações finais...")
        else:
            print("   ✅ Coluna company_id não existe, será criada")

        # Verificar integridade dos dados antes da alteração
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.people p
            LEFT JOIN master.companies c ON c.person_id = p.id
            WHERE c.id IS NULL;
        """
            )
        )
        orphans_before = result.scalar()

        if orphans_before > 0:
            print(f"   ❌ ERRO: Ainda existem {orphans_before} pessoas órfãs!")
            print("   🛑 PARAR: Execute primeiro a migração de dados órfãos")
            return

        print(f"   ✅ Todas as pessoas têm empresa associada")

        # PASSO 2: ADICIONAR COLUNA COMPANY_ID (se não existir)
        if not company_id_exists:
            print("\n2️⃣ ADICIONANDO COLUNA COMPANY_ID:")

            print("   ⏳ Adicionando coluna company_id...")
            await conn.execute(
                text(
                    """
                ALTER TABLE master.people
                ADD COLUMN company_id INTEGER;
            """
                )
            )
            print("   ✅ Coluna company_id adicionada")

            # PASSO 3: POPULAR COLUNA COMPANY_ID
            print("\n3️⃣ POPULANDO COLUNA COMPANY_ID:")

            print("   ⏳ Atualizando company_id baseado no relacionamento person_id...")
            result = await conn.execute(
                text(
                    """
                UPDATE master.people
                SET company_id = c.id
                FROM master.companies c
                WHERE c.person_id = people.id
                AND people.company_id IS NULL;
            """
                )
            )
            updated_rows = result.rowcount
            print(f"   ✅ {updated_rows} registros atualizados")

            # PASSO 4: ADICIONAR NOT NULL CONSTRAINT
            print("\n4️⃣ ADICIONANDO NOT NULL CONSTRAINT:")

            print("   ⏳ Definindo company_id como NOT NULL...")
            await conn.execute(
                text(
                    """
                ALTER TABLE master.people
                ALTER COLUMN company_id SET NOT NULL;
            """
                )
            )
            print("   ✅ Constraint NOT NULL adicionada")

            # PASSO 5: ADICIONAR FOREIGN KEY
            print("\n5️⃣ ADICIONANDO FOREIGN KEY:")

            print("   ⏳ Adicionando referência à tabela companies...")
            await conn.execute(
                text(
                    """
                ALTER TABLE master.people
                ADD CONSTRAINT fk_people_company
                FOREIGN KEY (company_id) REFERENCES master.companies(id);
            """
                )
            )
            print("   ✅ Foreign key constraint adicionada")

            # PASSO 6: REMOVER CONSTRAINT UNIQUE PROBLEMÁTICA
            print("\n6️⃣ REMOVENDO CONSTRAINT UNIQUE PROBLEMÁTICA:")

            # Obter constraints atuais
            result = await conn.execute(
                text(
                    """
                SELECT conname, pg_get_constraintdef(c.oid) as definition
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

            current_constraints = list(result)
            for constraint in current_constraints:
                if (
                    "tax_id" in constraint.definition.lower()
                    and "company_id" not in constraint.definition.lower()
                ):
                    print(
                        f"   ⏳ Removendo constraint problemática: {constraint.conname}"
                    )
                    await conn.execute(
                        text(
                            f"""
                        ALTER TABLE master.people
                        DROP CONSTRAINT {constraint.conname};
                    """
                        )
                    )
                    print(f"   ✅ Constraint {constraint.conname} removida")

            # PASSO 7: ADICIONAR NOVA CONSTRAINT UNIQUE (company_id, tax_id)
            print("\n7️⃣ ADICIONANDO CONSTRAINT MULTI-TENANT:")

            print("   ⏳ Adicionando constraint UNIQUE (company_id, tax_id)...")
            await conn.execute(
                text(
                    """
                ALTER TABLE master.people
                ADD CONSTRAINT people_company_tax_id_unique
                UNIQUE (company_id, tax_id);
            """
                )
            )
            print("   ✅ Constraint multi-tenant adicionada")

            # PASSO 8: ADICIONAR ÍNDICES OTIMIZADOS
            print("\n8️⃣ ADICIONANDO ÍNDICES OTIMIZADOS:")

            print("   ⏳ Criando índice people_company_idx...")
            await conn.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS people_company_idx
                ON master.people(company_id);
            """
                )
            )
            print("   ✅ Índice people_company_idx criado")

            print("   ⏳ Criando índice people_company_tax_id_idx...")
            await conn.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS people_company_tax_id_idx
                ON master.people(company_id, tax_id);
            """
                )
            )
            print("   ✅ Índice people_company_tax_id_idx criado")

        else:
            print("\n2️⃣-8️⃣ COLUNA COMPANY_ID JÁ EXISTE, PULANDO ALTERAÇÕES...")

        # PASSO 9: VALIDAÇÕES FINAIS (SEM TESTES QUE CAUSAM ROLLBACK)
        print("\n9️⃣ VALIDAÇÕES FINAIS:")

        # Verificar estrutura da tabela
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
        print("   📋 Estrutura das colunas:")
        for col in columns:
            print(
                f"      - {col.column_name}: {col.data_type} | NULL: {col.is_nullable} | Default: {col.column_default}"
            )

        # Verificar constraints
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
        print("   📋 Constraints atuais:")
        for constraint in constraints:
            constraint_type = "UNIQUE" if constraint.contype == "u" else "FOREIGN KEY"
            print(
                f"      - {constraint.conname} ({constraint_type}): {constraint.definition}"
            )

        # Verificar índices
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
        print("   📋 Índices company relacionados:")
        for idx in indexes:
            print(f"      - {idx.indexname}: {idx.indexdef}")

        # PASSO 10: RESUMO FINAL
        print("\n🔟 RESUMO DA ALTERAÇÃO:")

        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.people;
        """
            )
        )
        total_people = result.scalar()

        result = await conn.execute(
            text(
                """
            SELECT COUNT(DISTINCT company_id) FROM master.people;
        """
            )
        )
        distinct_companies = result.scalar()

        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.people WHERE company_id IS NULL;
        """
            )
        )
        people_without_company = result.scalar()

        print(f"   📊 Total de pessoas: {total_people}")
        print(f"   📊 Companies distintas: {distinct_companies}")
        print(f"   📊 Pessoas sem company_id: {people_without_company}")

        # Verificar se tudo foi implementado corretamente
        company_id_exists = any(col.column_name == "company_id" for col in columns)
        multi_tenant_constraint = any(
            "company_id" in constraint.definition and "tax_id" in constraint.definition
            for constraint in constraints
        )
        old_unique_exists = any(
            constraint.definition == "UNIQUE (tax_id)" for constraint in constraints
        )

        print(
            f"\n   ✅ Coluna company_id existe: {'SIM' if company_id_exists else 'NÃO'}"
        )
        print(
            f"   ✅ Constraint multi-tenant: {'SIM' if multi_tenant_constraint else 'NÃO'}"
        )
        print(
            f"   ✅ Constraint única antiga removida: {'SIM' if not old_unique_exists else 'NÃO'}"
        )
        print(
            f"   ✅ Dados populados: {'SIM' if people_without_company == 0 else 'NÃO'}"
        )

        if (
            company_id_exists
            and multi_tenant_constraint
            and not old_unique_exists
            and people_without_company == 0
        ):
            print("\n   🎉 FASE 2B CONCLUÍDA COM SUCESSO!")
            print("   ✅ Multi-tenancy implementado na tabela people")
            print("   🚀 PRONTO PARA FASE 2C: Alteração da tabela users")
        else:
            print("\n   ⚠️  FASE 2B PARCIALMENTE CONCLUÍDA")
            print("   🔧 Algumas alterações podem precisar de ajustes")


async def main():
    """Função principal"""
    try:
        await alter_people_schema_safe()
    except Exception as e:
        print(f"❌ Erro durante alteração: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
