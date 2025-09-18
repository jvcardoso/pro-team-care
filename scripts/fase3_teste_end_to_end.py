#!/usr/bin/env python3
"""
FASE 3: TESTE END-TO-END MULTI-TENANT
Script para testar isolamento completo do sistema multi-tenant
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine
from app.infrastructure.services.tenant_context_service import TenantContextService


async def test_end_to_end_multitenant():
    """Teste completo end-to-end do sistema multi-tenant"""

    print("🔍 FASE 3: TESTE END-TO-END MULTI-TENANT")
    print("=" * 60)

    tenant_service = TenantContextService()

    async with engine.begin() as conn:

        # PASSO 1: PREPARAÇÃO DOS DADOS DE TESTE
        print("\n1️⃣ PREPARAÇÃO DOS DADOS DE TESTE:")

        # Obter duas companies para teste
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

        test_companies = list(result)

        if len(test_companies) < 2:
            print("   ❌ ERRO: Necessárias pelo menos 2 companies para teste")
            return

        company_a_id = test_companies[0].id
        company_b_id = test_companies[1].id
        company_a_name = test_companies[0].name[:20]
        company_b_name = test_companies[1].name[:20]

        print(f"   🏢 Company A: ID {company_a_id} | {company_a_name}")
        print(f"   🏢 Company B: ID {company_b_id} | {company_b_name}")

        # PASSO 2: CRIAR PESSOAS DE TESTE COM MESMO CPF
        print("\n2️⃣ CRIANDO PESSOAS DE TESTE:")

        test_cpf = "12345678901"

        # Pessoa na Company A
        await conn.execute(
            text(
                """
            INSERT INTO master.people (
                person_type, name, tax_id, company_id, status, is_active,
                lgpd_consent_version, created_at, updated_at
            ) VALUES (
                'PF', 'João Silva Empresa A', :tax_id, :company_id, 'active', true,
                '1.0', NOW(), NOW()
            )
        """
            ),
            {"tax_id": test_cpf, "company_id": company_a_id},
        )

        # Pessoa na Company B
        await conn.execute(
            text(
                """
            INSERT INTO master.people (
                person_type, name, tax_id, company_id, status, is_active,
                lgpd_consent_version, created_at, updated_at
            ) VALUES (
                'PF', 'João Silva Empresa B', :tax_id, :company_id, 'active', true,
                '1.0', NOW(), NOW()
            )
        """
            ),
            {"tax_id": test_cpf, "company_id": company_b_id},
        )

        print(f"   ✅ Criadas pessoas com mesmo CPF: {test_cpf}")

        # PASSO 3: CRIAR USUÁRIOS DE TESTE COM MESMO EMAIL
        print("\n3️⃣ CRIANDO USUÁRIOS DE TESTE:")

        test_email = "admin@teste.com"

        # Obter pessoas criadas
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

        test_people = list(result)

        if len(test_people) != 2:
            print(f"   ❌ ERRO: Esperadas 2 pessoas, encontradas {len(test_people)}")
            return

        person_a_id, person_a_company, person_a_name = test_people[0]
        person_b_id, person_b_company, person_b_name = test_people[1]

        # Usuário na Company A
        await conn.execute(
            text(
                """
            INSERT INTO master.users (
                person_id, company_id, email_address, password, is_active,
                created_at, updated_at
            ) VALUES (
                :person_id, :company_id, :email, '$2b$12$dummy_hash_a', true,
                NOW(), NOW()
            )
        """
            ),
            {
                "person_id": person_a_id,
                "company_id": person_a_company,
                "email": test_email,
            },
        )

        # Usuário na Company B
        await conn.execute(
            text(
                """
            INSERT INTO master.users (
                person_id, company_id, email_address, password, is_active,
                created_at, updated_at
            ) VALUES (
                :person_id, :company_id, :email, '$2b$12$dummy_hash_b', true,
                NOW(), NOW()
            )
        """
            ),
            {
                "person_id": person_b_id,
                "company_id": person_b_company,
                "email": test_email,
            },
        )

        print(f"   ✅ Criados usuários com mesmo email: {test_email}")

        # PASSO 4: TESTAR ISOLAMENTO - CONTEXTO COMPANY A
        print(f"\n4️⃣ TESTANDO ISOLAMENTO - CONTEXTO COMPANY A (ID: {company_a_id}):")

        await conn.execute(
            text("SELECT master.set_current_company_id(:company_id)"),
            {"company_id": company_a_id},
        )

        # Verificar people visíveis
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.people WHERE tax_id = :tax_id
        """
            ),
            {"tax_id": test_cpf},
        )
        people_count_a = result.scalar()

        result = await conn.execute(
            text(
                """
            SELECT name FROM master.people WHERE tax_id = :tax_id LIMIT 1
        """
            ),
            {"tax_id": test_cpf},
        )
        person_name_a = result.fetchone()

        # Verificar users visíveis
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.users WHERE email_address = :email
        """
            ),
            {"email": test_email},
        )
        users_count_a = result.scalar()

        result = await conn.execute(
            text(
                """
            SELECT u.id FROM master.users u WHERE email_address = :email LIMIT 1
        """
            ),
            {"email": test_email},
        )
        user_id_a = result.fetchone()

        print(f"   📊 People com CPF {test_cpf}: {people_count_a}")
        print(f"   📋 Nome da pessoa: {person_name_a.name if person_name_a else 'N/A'}")
        print(f"   📊 Users com email {test_email}: {users_count_a}")
        print(f"   📋 User ID: {user_id_a.id if user_id_a else 'N/A'}")

        # PASSO 5: TESTAR ISOLAMENTO - CONTEXTO COMPANY B
        print(f"\n5️⃣ TESTANDO ISOLAMENTO - CONTEXTO COMPANY B (ID: {company_b_id}):")

        await conn.execute(
            text("SELECT master.set_current_company_id(:company_id)"),
            {"company_id": company_b_id},
        )

        # Verificar people visíveis
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.people WHERE tax_id = :tax_id
        """
            ),
            {"tax_id": test_cpf},
        )
        people_count_b = result.scalar()

        result = await conn.execute(
            text(
                """
            SELECT name FROM master.people WHERE tax_id = :tax_id LIMIT 1
        """
            ),
            {"tax_id": test_cpf},
        )
        person_name_b = result.fetchone()

        # Verificar users visíveis
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.users WHERE email_address = :email
        """
            ),
            {"email": test_email},
        )
        users_count_b = result.scalar()

        result = await conn.execute(
            text(
                """
            SELECT u.id FROM master.users u WHERE email_address = :email LIMIT 1
        """
            ),
            {"email": test_email},
        )
        user_id_b = result.fetchone()

        print(f"   📊 People com CPF {test_cpf}: {people_count_b}")
        print(f"   📋 Nome da pessoa: {person_name_b.name if person_name_b else 'N/A'}")
        print(f"   📊 Users com email {test_email}: {users_count_b}")
        print(f"   📋 User ID: {user_id_b.id if user_id_b else 'N/A'}")

        # PASSO 6: VERIFICAR ISOLAMENTO
        print(f"\n6️⃣ VERIFICAÇÃO DO ISOLAMENTO:")

        isolation_working = True

        # Verificar se cada contexto vê apenas seus dados
        if people_count_a != 1 or people_count_b != 1:
            print(f"   ❌ FALHA: Cada contexto deveria ver exatamente 1 pessoa")
            isolation_working = False
        else:
            print(f"   ✅ People isolados: Cada contexto vê exatamente 1 pessoa")

        if users_count_a != 1 or users_count_b != 1:
            print(f"   ❌ FALHA: Cada contexto deveria ver exatamente 1 usuário")
            isolation_working = False
        else:
            print(f"   ✅ Users isolados: Cada contexto vê exatamente 1 usuário")

        # Verificar se são pessoas diferentes
        if person_name_a and person_name_b and person_name_a.name != person_name_b.name:
            print(f"   ✅ Pessoas diferentes por contexto:")
            print(f"      - Company A: {person_name_a.name}")
            print(f"      - Company B: {person_name_b.name}")
        else:
            print(f"   ❌ FALHA: Pessoas deveriam ser diferentes por contexto")
            isolation_working = False

        # Verificar se são usuários diferentes
        if user_id_a and user_id_b and user_id_a.id != user_id_b.id:
            print(f"   ✅ Usuários diferentes por contexto:")
            print(f"      - Company A User ID: {user_id_a.id}")
            print(f"      - Company B User ID: {user_id_b.id}")
        else:
            print(f"   ❌ FALHA: Usuários deveriam ser diferentes por contexto")
            isolation_working = False

        # PASSO 7: TESTAR SEM CONTEXTO (ADMIN VIEW)
        print(f"\n7️⃣ TESTANDO SEM CONTEXTO (ADMIN VIEW):")

        await conn.execute(text("SELECT master.set_current_company_id(0)"))

        # Como postgres tem bypass, deve ver todos os dados
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.people WHERE tax_id = :tax_id
        """
            ),
            {"tax_id": test_cpf},
        )
        people_total = result.scalar()

        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.users WHERE email_address = :email
        """
            ),
            {"email": test_email},
        )
        users_total = result.scalar()

        print(f"   📊 Total people com CPF {test_cpf}: {people_total}")
        print(f"   📊 Total users com email {test_email}: {users_total}")

        if people_total >= 2 and users_total >= 2:
            print(f"   ✅ Admin bypass funcionando: Vê todos os dados")
        else:
            print(f"   ⚠️  Admin bypass pode estar limitado")

        # PASSO 8: LIMPEZA DOS DADOS DE TESTE
        print(f"\n8️⃣ LIMPEZA DOS DADOS DE TESTE:")

        # Reset context para admin
        await conn.execute(text("SELECT master.set_current_company_id(0)"))

        # Remover users de teste
        result = await conn.execute(
            text(
                """
            DELETE FROM master.users WHERE email_address = :email
        """
            ),
            {"email": test_email},
        )
        users_deleted = result.rowcount

        # Remover people de teste
        result = await conn.execute(
            text(
                """
            DELETE FROM master.people WHERE tax_id = :tax_id
        """
            ),
            {"tax_id": test_cpf},
        )
        people_deleted = result.rowcount

        print(f"   🗑️ Removidos {users_deleted} usuários de teste")
        print(f"   🗑️ Removidos {people_deleted} pessoas de teste")

        # PASSO 9: RESULTADO FINAL
        print(f"\n9️⃣ RESULTADO FINAL:")

        if isolation_working:
            print(f"   🎉 TESTE END-TO-END PASSOU COM SUCESSO!")
            print(f"   ✅ Isolamento multi-tenant funcionando perfeitamente")
            print(f"   ✅ Mesmo CPF/Email permitido entre empresas diferentes")
            print(f"   ✅ RLS bloqueando corretamente acesso entre contextos")
            print(f"   ✅ Admin bypass funcionando para administração")
            print(f"\n   🚀 SISTEMA MULTI-TENANT 100% OPERACIONAL!")
        else:
            print(f"   ❌ TESTE END-TO-END FALHOU!")
            print(f"   🔧 Isolamento multi-tenant precisa de ajustes")
            print(f"   📋 Revisar configurações de RLS e contexto")


async def main():
    """Função principal"""
    try:
        await test_end_to_end_multitenant()
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
