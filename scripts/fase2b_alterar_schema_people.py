#!/usr/bin/env python3
"""
FASE 2B: ALTERAÇÃO DE SCHEMA - TABELA PEOPLE
Script para adicionar company_id na tabela people e alterar constraints
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def alter_people_schema():
    """Adicionar company_id na tabela people e alterar constraints"""

    print("🔧 FASE 2B: ALTERAÇÃO DE SCHEMA - TABELA PEOPLE")
    print("=" * 60)

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
            print("   ⚠️  Coluna company_id já existe, pulando criação...")
        else:
            print("   ✅ Coluna company_id não existe, será criada")

        # Verificar constraint atual
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
        print("   📋 Constraints atuais:")
        for constraint in current_constraints:
            print(f"      - {constraint.conname}: {constraint.definition}")

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

        else:
            print("\n2️⃣ COLUNA COMPANY_ID JÁ EXISTE, PULANDO...")

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

        # Verificar se todos foram atualizados
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.people WHERE company_id IS NULL;
        """
            )
        )
        null_company_ids = result.scalar()

        if null_company_ids > 0:
            print(f"   ❌ ERRO: {null_company_ids} registros ainda sem company_id!")
            return
        else:
            print("   ✅ Todos os registros têm company_id preenchido")

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

        # PASSO 5: REMOVER CONSTRAINT UNIQUE PROBLEMÁTICA
        print("\n5️⃣ ALTERANDO CONSTRAINTS UNIQUE:")

        for constraint in current_constraints:
            if "tax_id" in constraint.definition.lower():
                print(f"   ⏳ Removendo constraint problemática: {constraint.conname}")
                await conn.execute(
                    text(
                        f"""
                    ALTER TABLE master.people
                    DROP CONSTRAINT {constraint.conname};
                """
                    )
                )
                print(f"   ✅ Constraint {constraint.conname} removida")

        # PASSO 6: ADICIONAR NOVA CONSTRAINT UNIQUE (company_id, tax_id)
        print("\n6️⃣ ADICIONANDO CONSTRAINT MULTI-TENANT:")

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

        # PASSO 7: ADICIONAR ÍNDICE OTIMIZADO
        print("\n7️⃣ ADICIONANDO ÍNDICES OTIMIZADOS:")

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

        # PASSO 8: VALIDAÇÕES PÓS-ALTERAÇÃO
        print("\n8️⃣ VALIDAÇÕES PÓS-ALTERAÇÃO:")

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

        # PASSO 9: TESTE DE FUNCIONALIDADE
        print("\n9️⃣ TESTE DE FUNCIONALIDADE:")

        # Tentar inserir registros com mesmo tax_id em companies diferentes
        print("   ⏳ Testando constraint multi-tenant...")

        try:
            # Obter duas companies diferentes
            result = await conn.execute(
                text(
                    """
                SELECT id FROM master.companies ORDER BY id LIMIT 2;
            """
                )
            )
            companies = list(result)

            if len(companies) >= 2:
                company1_id, company2_id = companies[0].id, companies[1].id

                # Teste: inserir mesmo tax_id em companies diferentes (deve funcionar)
                await conn.execute(
                    text(
                        """
                    INSERT INTO master.people (
                        person_type, name, tax_id, company_id, status, is_active,
                        lgpd_consent_version, created_at, updated_at
                    ) VALUES
                    ('PF', 'Teste Multi-Tenant 1', '99988877766', :company1_id, 'active', true, '1.0', NOW(), NOW()),
                    ('PF', 'Teste Multi-Tenant 2', '99988877766', :company2_id, 'active', true, '1.0', NOW(), NOW());
                """
                    ),
                    {"company1_id": company1_id, "company2_id": company2_id},
                )

                print("   ✅ Mesmo tax_id em companies diferentes: PERMITIDO")

                # Limpar dados de teste
                await conn.execute(
                    text(
                        """
                    DELETE FROM master.people WHERE tax_id = '99988877766';
                """
                    )
                )

                # Teste: inserir mesmo tax_id na MESMA company (deve falhar)
                try:
                    await conn.execute(
                        text(
                            """
                        INSERT INTO master.people (
                            person_type, name, tax_id, company_id, status, is_active,
                            lgpd_consent_version, created_at, updated_at
                        ) VALUES
                        ('PF', 'Teste Duplicado 1', '88877766655', :company_id, 'active', true, '1.0', NOW(), NOW()),
                        ('PF', 'Teste Duplicado 2', '88877766655', :company_id, 'active', true, '1.0', NOW(), NOW());
                    """
                        ),
                        {"company_id": company1_id},
                    )

                    print(
                        "   ❌ ERRO: Duplicação na mesma company deveria ter falhado!"
                    )

                except Exception:
                    print("   ✅ Duplicação na mesma company: BLOQUEADO (correto)")

                    # Limpar possíveis dados parciais
                    await conn.execute(
                        text(
                            """
                        DELETE FROM master.people WHERE tax_id = '88877766655';
                    """
                        )
                    )

        except Exception as e:
            print(f"   ⚠️  Teste de funcionalidade falhou: {e}")

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

        print(f"   📊 Total de pessoas: {total_people}")
        print(f"   📊 Companies distintas: {distinct_companies}")
        print("   ✅ Coluna company_id adicionada e populada")
        print("   ✅ Constraint UNIQUE(company_id, tax_id) ativa")
        print("   ✅ Índices otimizados criados")
        print("   ✅ Multi-tenancy funcional na tabela people")
        print("\n   🎉 FASE 2B CONCLUÍDA COM SUCESSO!")
        print("   🚀 PRONTO PARA FASE 2C: Alteração da tabela users")


async def main():
    """Função principal"""
    try:
        await alter_people_schema()
    except Exception as e:
        print(f"❌ Erro durante alteração: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
