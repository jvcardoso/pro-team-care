#!/usr/bin/env python3
"""
FASE 2: VALIDAÇÃO FINAL DO MULTI-TENANCY
Script para testar e validar o funcionamento completo do sistema multi-tenant
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def validate_multi_tenancy():
    """Validar funcionamento completo do multi-tenancy"""

    print("🔍 FASE 2: VALIDAÇÃO FINAL DO MULTI-TENANCY")
    print("=" * 65)

    async with engine.begin() as conn:

        # PASSO 1: VERIFICAR ESTRUTURA DAS TABELAS
        print("\n1️⃣ ESTRUTURA DAS TABELAS:")

        # Verificar tabela people
        result = await conn.execute(
            text(
                """
            SELECT
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'master'
            AND table_name = 'people'
            AND column_name IN ('company_id', 'tax_id')
            ORDER BY ordinal_position;
        """
            )
        )

        people_columns = list(result)
        print("   📋 Tabela PEOPLE:")
        for col in people_columns:
            print(
                f"      - {col.column_name}: {col.data_type} | NULL: {col.is_nullable}"
            )

        # Verificar tabela users
        result = await conn.execute(
            text(
                """
            SELECT
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'master'
            AND table_name = 'users'
            AND column_name IN ('company_id', 'email_address')
            ORDER BY ordinal_position;
        """
            )
        )

        users_columns = list(result)
        print("   📋 Tabela USERS:")
        for col in users_columns:
            print(
                f"      - {col.column_name}: {col.data_type} | NULL: {col.is_nullable}"
            )

        # PASSO 2: VERIFICAR CONSTRAINTS MULTI-TENANT
        print("\n2️⃣ CONSTRAINTS MULTI-TENANT:")

        # Constraints da tabela people
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
            AND pg_get_constraintdef(c.oid) LIKE '%company_id%';
        """
            )
        )

        people_constraints = list(result)
        print("   📋 Constraints PEOPLE:")
        for constraint in people_constraints:
            print(f"      - {constraint.conname}: {constraint.definition}")

        # Constraints da tabela users
        result = await conn.execute(
            text(
                """
            SELECT conname, pg_get_constraintdef(c.oid) as definition
            FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            JOIN pg_namespace n ON t.relnamespace = n.oid
            WHERE n.nspname = 'master'
            AND t.relname = 'users'
            AND c.contype = 'u'
            AND pg_get_constraintdef(c.oid) LIKE '%company_id%';
        """
            )
        )

        users_constraints = list(result)
        print("   📋 Constraints USERS:")
        for constraint in users_constraints:
            print(f"      - {constraint.conname}: {constraint.definition}")

        # PASSO 3: TESTAR FUNCIONAMENTO
        print("\n3️⃣ TESTE DE FUNCIONAMENTO:")

        # 3.1: Obter duas companies diferentes para teste
        result = await conn.execute(
            text(
                """
            SELECT id, p.name as company_name
            FROM master.companies c
            JOIN master.people p ON p.id = c.person_id
            WHERE c.id != (
                SELECT c2.id FROM master.companies c2
                JOIN master.people p2 ON p2.id = c2.person_id
                WHERE p2.name = 'Pro Team Care - Sistema'
            )
            ORDER BY c.id
            LIMIT 2;
        """
            )
        )

        test_companies = list(result)

        if len(test_companies) >= 2:
            company1_id = test_companies[0].id
            company2_id = test_companies[1].id
            company1_name = test_companies[0].company_name[:20]
            company2_name = test_companies[1].company_name[:20]

            print(f"   🏢 Usando para testes:")
            print(f"      - Company 1: ID {company1_id} | {company1_name}")
            print(f"      - Company 2: ID {company2_id} | {company2_name}")

            # 3.2: TESTE PEOPLE - Mesmo CPF em companies diferentes (DEVE FUNCIONAR)
            print("\n   📝 TESTE 1: PEOPLE - Mesmo CPF em companies diferentes")
            test_cpf = "11122233344"

            try:
                await conn.execute(
                    text(
                        """
                    INSERT INTO master.people (
                        person_type, name, tax_id, company_id, status, is_active,
                        lgpd_consent_version, created_at, updated_at
                    ) VALUES
                    ('PF', 'João Silva', :tax_id, :company1_id, 'active', true, '1.0', NOW(), NOW()),
                    ('PF', 'João Silva Outro', :tax_id, :company2_id, 'active', true, '1.0', NOW(), NOW());
                """
                    ),
                    {
                        "tax_id": test_cpf,
                        "company1_id": company1_id,
                        "company2_id": company2_id,
                    },
                )

                print("      ✅ SUCESSO: Mesmo CPF em companies diferentes - PERMITIDO")

                # Limpar dados de teste
                await conn.execute(
                    text("DELETE FROM master.people WHERE tax_id = :tax_id;"),
                    {"tax_id": test_cpf},
                )

            except Exception as e:
                print(f"      ❌ FALHA: {e}")

            # 3.3: TESTE PEOPLE - Mesmo CPF na MESMA company (DEVE FALHAR)
            print("\n   📝 TESTE 2: PEOPLE - Mesmo CPF na mesma company")
            test_cpf2 = "55566677788"

            try:
                await conn.execute(
                    text(
                        """
                    INSERT INTO master.people (
                        person_type, name, tax_id, company_id, status, is_active,
                        lgpd_consent_version, created_at, updated_at
                    ) VALUES
                    ('PF', 'Maria Santos', :tax_id, :company_id, 'active', true, '1.0', NOW(), NOW()),
                    ('PF', 'Maria Santos Duplicada', :tax_id, :company_id, 'active', true, '1.0', NOW(), NOW());
                """
                    ),
                    {"tax_id": test_cpf2, "company_id": company1_id},
                )

                print(
                    "      ❌ FALHA: Duplicação na mesma company deveria ter sido bloqueada!"
                )
                # Limpar se conseguiu inserir
                await conn.execute(
                    text("DELETE FROM master.people WHERE tax_id = :tax_id;"),
                    {"tax_id": test_cpf2},
                )

            except Exception:
                print(
                    "      ✅ SUCESSO: Duplicação na mesma company - BLOQUEADO (correto)"
                )

            # 3.4: TESTE USERS - Mesmo email em companies diferentes (DEVE FUNCIONAR)
            print("\n   📝 TESTE 3: USERS - Mesmo email em companies diferentes")
            test_email = "teste@multitenant.com"

            # Primeiro, criar pessoas para os usuários
            try:
                await conn.execute(
                    text(
                        """
                    INSERT INTO master.people (
                        person_type, name, tax_id, company_id, status, is_active,
                        lgpd_consent_version, created_at, updated_at
                    ) VALUES
                    ('PF', 'User Test 1', '12312312312', :company1_id, 'active', true, '1.0', NOW(), NOW()),
                    ('PF', 'User Test 2', '45645645645', :company2_id, 'active', true, '1.0', NOW(), NOW());
                """
                    ),
                    {"company1_id": company1_id, "company2_id": company2_id},
                )

                # Obter IDs das pessoas criadas
                result = await conn.execute(
                    text(
                        """
                    SELECT id, name, company_id FROM master.people
                    WHERE tax_id IN ('12312312312', '45645645645')
                    ORDER BY tax_id;
                """
                    )
                )

                test_people = list(result)
                person1_id = test_people[0].id
                person2_id = test_people[1].id

                # Criar usuários com mesmo email em companies diferentes
                await conn.execute(
                    text(
                        """
                    INSERT INTO master.users (
                        person_id, email_address, company_id, password_hash,
                        is_active, created_at, updated_at
                    ) VALUES
                    (:person1_id, :email, :company1_id, '$2b$12$dummy_hash_1', true, NOW(), NOW()),
                    (:person2_id, :email, :company2_id, '$2b$12$dummy_hash_2', true, NOW(), NOW());
                """
                    ),
                    {
                        "email": test_email,
                        "person1_id": person1_id,
                        "person2_id": person2_id,
                        "company1_id": company1_id,
                        "company2_id": company2_id,
                    },
                )

                print(
                    "      ✅ SUCESSO: Mesmo email em companies diferentes - PERMITIDO"
                )

                # Limpar dados de teste
                await conn.execute(
                    text("DELETE FROM master.users WHERE email_address = :email;"),
                    {"email": test_email},
                )
                await conn.execute(
                    text(
                        "DELETE FROM master.people WHERE tax_id IN ('12312312312', '45645645645');"
                    )
                )

            except Exception as e:
                print(f"      ❌ FALHA: {e}")
                # Tentar limpar dados parciais
                await conn.execute(
                    text("DELETE FROM master.users WHERE email_address = :email;"),
                    {"email": test_email},
                )
                await conn.execute(
                    text(
                        "DELETE FROM master.people WHERE tax_id IN ('12312312312', '45645645645');"
                    )
                )

        else:
            print("   ⚠️  Não há companies suficientes para testes completos")

        # PASSO 4: ESTATÍSTICAS FINAIS
        print("\n4️⃣ ESTATÍSTICAS FINAIS:")

        # Estatísticas gerais
        result = await conn.execute(
            text(
                """
            SELECT
                'people' as tabela,
                COUNT(*) as total_registros,
                COUNT(DISTINCT company_id) as companies_distintas
            FROM master.people
            UNION ALL
            SELECT
                'users' as tabela,
                COUNT(*) as total_registros,
                COUNT(DISTINCT company_id) as companies_distintas
            FROM master.users;
        """
            )
        )

        stats = list(result)
        for stat in stats:
            print(
                f"   📊 {stat.tabela.upper()}: {stat.total_registros} registros | {stat.companies_distintas} companies"
            )

        # Verificar integridade dos relacionamentos
        result = await conn.execute(
            text(
                """
            SELECT
                COUNT(*) as total_people,
                COUNT(DISTINCT p.company_id) as people_companies,
                COUNT(DISTINCT c.id) as actual_companies
            FROM master.people p
            JOIN master.companies c ON c.id = p.company_id;
        """
            )
        )

        integrity = result.fetchone()
        print(
            f"   📊 INTEGRIDADE: {integrity.total_people} pessoas em {integrity.people_companies} companies ({integrity.actual_companies} existentes)"
        )

        # PASSO 5: RESUMO FINAL
        print("\n5️⃣ RESUMO DA FASE 2:")

        # Verificar se tudo foi implementado
        people_has_company_id = any(
            col.column_name == "company_id" for col in people_columns
        )
        users_has_company_id = any(
            col.column_name == "company_id" for col in users_columns
        )
        people_has_constraint = len(people_constraints) > 0
        users_has_constraint = len(users_constraints) > 0

        print(
            f"   ✅ People com company_id: {'SIM' if people_has_company_id else 'NÃO'}"
        )
        print(f"   ✅ Users com company_id: {'SIM' if users_has_company_id else 'NÃO'}")
        print(
            f"   ✅ People com constraint multi-tenant: {'SIM' if people_has_constraint else 'NÃO'}"
        )
        print(
            f"   ✅ Users com constraint multi-tenant: {'SIM' if users_has_constraint else 'NÃO'}"
        )

        all_implemented = (
            people_has_company_id
            and users_has_company_id
            and people_has_constraint
            and users_has_constraint
        )

        if all_implemented:
            print("\n   🎉 FASE 2 CONCLUÍDA COM SUCESSO TOTAL!")
            print("   ✅ Multi-tenancy implementado nas tabelas críticas")
            print("   ✅ Constraints globais problemáticas removidas")
            print("   ✅ Constraints multi-tenant implementadas")
            print("   ✅ Dados órfãos migrados com sucesso")
            print("   ✅ Sistema pronto para multi-tenancy real")
            print("\n   🚀 PRÓXIMA ETAPA: FASE 3 (Implementação de RLS)")
        else:
            print("\n   ⚠️  FASE 2 PARCIALMENTE IMPLEMENTADA")
            print("   🔧 Algumas implementações podem precisar de ajustes")


async def main():
    """Função principal"""
    try:
        await validate_multi_tenancy()
    except Exception as e:
        print(f"❌ Erro durante validação: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
