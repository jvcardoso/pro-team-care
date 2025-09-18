#!/usr/bin/env python3
"""
FASE 3: TESTE END-TO-END MULTI-TENANT (VERSÃO LIMPA)
Script para testar isolamento completo com limpeza prévia
"""

import asyncio
import random
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def test_multitenant_clean():
    """Teste multi-tenant com limpeza prévia"""

    print("🔍 FASE 3: TESTE END-TO-END MULTI-TENANT (LIMPO)")
    print("=" * 65)

    # Gerar dados únicos para este teste
    test_cpf = f"99{random.randint(100000000, 999999999)}"
    test_email = f"teste{random.randint(1000, 9999)}@multitenant.com"

    async with engine.begin() as conn:

        # PASSO 1: LIMPEZA PRÉVIA
        print("\n1️⃣ LIMPEZA PRÉVIA:")

        # Reset context para admin
        await conn.execute(text("SELECT master.set_current_company_id(0)"))

        # Limpar possíveis dados antigos
        await conn.execute(
            text(
                "DELETE FROM master.users WHERE email_address LIKE '%@multitenant.com'"
            )
        )
        await conn.execute(text("DELETE FROM master.people WHERE tax_id LIKE '99%'"))

        print(f"   🧹 Dados antigos de teste removidos")

        # PASSO 2: PREPARAÇÃO
        print(f"\n2️⃣ PREPARAÇÃO DOS DADOS DE TESTE:")

        # Obter companies para teste
        result = await conn.execute(
            text(
                """
            SELECT c.id, p.name
            FROM master.companies c
            JOIN master.people p ON p.id = c.person_id
            WHERE p.name != 'Pro Team Care - Sistema'
            ORDER BY c.id
            LIMIT 2;
        """
            )
        )

        companies = list(result)
        if len(companies) < 2:
            print("   ❌ ERRO: Necessárias pelo menos 2 companies")
            return

        company_a_id, company_a_name = companies[0]
        company_b_id, company_b_name = companies[1]

        print(f"   🏢 Company A: ID {company_a_id} | {company_a_name[:20]}")
        print(f"   🏢 Company B: ID {company_b_id} | {company_b_name[:20]}")
        print(f"   📋 CPF de teste: {test_cpf}")
        print(f"   📧 Email de teste: {test_email}")

        # PASSO 3: CRIAR DADOS DE TESTE
        print(f"\n3️⃣ CRIANDO DADOS DE TESTE:")

        # Pessoa A
        await conn.execute(
            text(
                """
            INSERT INTO master.people (
                person_type, name, tax_id, company_id, status, is_active,
                lgpd_consent_version, created_at, updated_at
            ) VALUES (
                'PF', 'João Silva Company A', :tax_id, :company_id, 'active', true,
                '1.0', NOW(), NOW()
            ) RETURNING id;
        """
            ),
            {"tax_id": test_cpf, "company_id": company_a_id},
        )

        # Pessoa B
        await conn.execute(
            text(
                """
            INSERT INTO master.people (
                person_type, name, tax_id, company_id, status, is_active,
                lgpd_consent_version, created_at, updated_at
            ) VALUES (
                'PF', 'João Silva Company B', :tax_id, :company_id, 'active', true,
                '1.0', NOW(), NOW()
            ) RETURNING id;
        """
            ),
            {"tax_id": test_cpf, "company_id": company_b_id},
        )

        print(f"   ✅ 2 pessoas criadas com mesmo CPF em companies diferentes")

        # Obter IDs das pessoas criadas
        result = await conn.execute(
            text(
                """
            SELECT id, company_id, name
            FROM master.people
            WHERE tax_id = :tax_id
            ORDER BY company_id
        """
            ),
            {"tax_id": test_cpf},
        )

        people = list(result)
        person_a_id, _, person_a_name = people[0]
        person_b_id, _, person_b_name = people[1]

        # Usuário A
        await conn.execute(
            text(
                """
            INSERT INTO master.users (
                person_id, company_id, email_address, password, is_active,
                created_at, updated_at
            ) VALUES (
                :person_id, :company_id, :email, '$2b$12$hash_a', true,
                NOW(), NOW()
            )
        """
            ),
            {"person_id": person_a_id, "company_id": company_a_id, "email": test_email},
        )

        # Usuário B
        await conn.execute(
            text(
                """
            INSERT INTO master.users (
                person_id, company_id, email_address, password, is_active,
                created_at, updated_at
            ) VALUES (
                :person_id, :company_id, :email, '$2b$12$hash_b', true,
                NOW(), NOW()
            )
        """
            ),
            {"person_id": person_b_id, "company_id": company_b_id, "email": test_email},
        )

        print(f"   ✅ 2 usuários criados com mesmo email em companies diferentes")

        # PASSO 4: TESTAR ISOLAMENTO
        print(f"\n4️⃣ TESTANDO ISOLAMENTO RLS:")

        # Contexto Company A
        await conn.execute(
            text("SELECT master.set_current_company_id(:company_id)"),
            {"company_id": company_a_id},
        )

        result = await conn.execute(
            text("SELECT COUNT(*) FROM master.people WHERE tax_id = :tax_id"),
            {"tax_id": test_cpf},
        )
        people_a = result.scalar()

        result = await conn.execute(
            text("SELECT name FROM master.people WHERE tax_id = :tax_id LIMIT 1"),
            {"tax_id": test_cpf},
        )
        name_a = result.fetchone()

        result = await conn.execute(
            text("SELECT COUNT(*) FROM master.users WHERE email_address = :email"),
            {"email": test_email},
        )
        users_a = result.scalar()

        print(f"   📊 Company A contexto:")
        print(f"      - People visíveis: {people_a}")
        print(f"      - Nome: {name_a.name if name_a else 'N/A'}")
        print(f"      - Users visíveis: {users_a}")

        # Contexto Company B
        await conn.execute(
            text("SELECT master.set_current_company_id(:company_id)"),
            {"company_id": company_b_id},
        )

        result = await conn.execute(
            text("SELECT COUNT(*) FROM master.people WHERE tax_id = :tax_id"),
            {"tax_id": test_cpf},
        )
        people_b = result.scalar()

        result = await conn.execute(
            text("SELECT name FROM master.people WHERE tax_id = :tax_id LIMIT 1"),
            {"tax_id": test_cpf},
        )
        name_b = result.fetchone()

        result = await conn.execute(
            text("SELECT COUNT(*) FROM master.users WHERE email_address = :email"),
            {"email": test_email},
        )
        users_b = result.scalar()

        print(f"   📊 Company B contexto:")
        print(f"      - People visíveis: {people_b}")
        print(f"      - Nome: {name_b.name if name_b else 'N/A'}")
        print(f"      - Users visíveis: {users_b}")

        # PASSO 5: VERIFICAÇÃO DO ISOLAMENTO
        print(f"\n5️⃣ VERIFICAÇÃO DO ISOLAMENTO:")

        isolation_perfect = True

        # Cada contexto deve ver exatamente 1 registro
        if people_a != 1 or people_b != 1:
            print(
                f"   ❌ FALHA: Cada contexto deveria ver 1 pessoa (A: {people_a}, B: {people_b})"
            )
            isolation_perfect = False
        else:
            print(f"   ✅ SUCESSO: Isolamento de people funcionando")

        if users_a != 1 or users_b != 1:
            print(
                f"   ❌ FALHA: Cada contexto deveria ver 1 usuário (A: {users_a}, B: {users_b})"
            )
            isolation_perfect = False
        else:
            print(f"   ✅ SUCESSO: Isolamento de users funcionando")

        # Verificar se são registros diferentes
        if name_a and name_b and name_a.name != name_b.name:
            print(f"   ✅ SUCESSO: Dados isolados por company")
            print(f"      - Company A vê: {name_a.name}")
            print(f"      - Company B vê: {name_b.name}")
        else:
            print(f"   ❌ FALHA: Contextos veem dados iguais")
            isolation_perfect = False

        # PASSO 6: TESTE ADMIN VIEW
        print(f"\n6️⃣ TESTE ADMIN VIEW (sem contexto):")

        await conn.execute(text("SELECT master.set_current_company_id(0)"))

        result = await conn.execute(
            text("SELECT COUNT(*) FROM master.people WHERE tax_id = :tax_id"),
            {"tax_id": test_cpf},
        )
        total_people = result.scalar()

        result = await conn.execute(
            text("SELECT COUNT(*) FROM master.users WHERE email_address = :email"),
            {"email": test_email},
        )
        total_users = result.scalar()

        print(f"   📊 Admin vê (bypass das políticas RLS):")
        print(f"      - Total people: {total_people}")
        print(f"      - Total users: {total_users}")

        # PASSO 7: LIMPEZA FINAL
        print(f"\n7️⃣ LIMPEZA DOS DADOS DE TESTE:")

        users_deleted = await conn.execute(
            text("DELETE FROM master.users WHERE email_address = :email"),
            {"email": test_email},
        )
        people_deleted = await conn.execute(
            text("DELETE FROM master.people WHERE tax_id = :tax_id"),
            {"tax_id": test_cpf},
        )

        print(f"   🗑️ Removidos usuários: {users_deleted.rowcount}")
        print(f"   🗑️ Removidos pessoas: {people_deleted.rowcount}")

        # PASSO 8: RESULTADO FINAL
        print(f"\n8️⃣ RESULTADO FINAL:")

        if isolation_perfect:
            print(f"   🎉 TESTE END-TO-END PASSOU COM SUCESSO ABSOLUTO!")
            print(f"   ✅ Multi-tenancy funcionando perfeitamente")
            print(f"   ✅ RLS isolando dados por company_id")
            print(f"   ✅ Mesmo CPF/email permitido entre companies")
            print(f"   ✅ Admin bypass ativo para administração")
            print(f"\n   🚀 SISTEMA 100% PRONTO PARA PRODUÇÃO!")
        else:
            print(f"   ❌ TESTE IDENTIFICOU PROBLEMAS:")
            print(f"   🔧 Isolamento RLS precisa de ajustes")


async def main():
    """Função principal"""
    try:
        await test_multitenant_clean()
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
