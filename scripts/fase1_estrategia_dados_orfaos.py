#!/usr/bin/env python3
"""
FASE 1: ESTRATÉGIA PARA DADOS ÓRFÃOS
Script para preparar migração dos 12 registros órfãos identificados
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def strategy_for_orphan_data():
    """Definir estratégia para migração dos dados órfãos"""

    print("🔧 FASE 1: ESTRATÉGIA PARA DADOS ÓRFÃOS")
    print("=" * 60)

    async with engine.begin() as conn:

        # 1. ANALISAR PESSOAS ÓRFÃS EM DETALHES
        print("\n1️⃣ ANÁLISE DETALHADA DAS PESSOAS ÓRFÃS:")
        result = await conn.execute(
            text(
                """
            SELECT
                p.id,
                p.name,
                p.tax_id,
                p.person_type,
                p.created_at,
                CASE
                    WHEN u.id IS NOT NULL THEN 'Tem usuário'
                    ELSE 'Sem usuário'
                END as tem_usuario,
                u.email_address
            FROM master.people p
            LEFT JOIN master.companies c ON c.person_id = p.id
            LEFT JOIN master.users u ON u.person_id = p.id
            WHERE c.id IS NULL
            ORDER BY p.created_at;
        """
            )
        )

        orphans = list(result)
        print(f"   📊 Total de pessoas órfãs: {len(orphans)}")
        print("   📋 Detalhes:")

        system_admins = []
        test_users = []
        real_people = []

        for person in orphans:
            print(
                f"      - ID: {person.id:2} | {person.name:30} | {person.tax_id:15} | {person.tem_usuario:12} | {person.email_address or 'Sem email'}"
            )

            # Classificar o tipo de pessoa órfã
            name_lower = person.name.lower()
            if "admin" in name_lower or "sistema" in name_lower:
                system_admins.append(person)
            elif "teste" in name_lower:
                test_users.append(person)
            else:
                real_people.append(person)

        print(f"\n   🔍 CLASSIFICAÇÃO:")
        print(f"      - Admins de sistema: {len(system_admins)}")
        print(f"      - Usuários de teste: {len(test_users)}")
        print(f"      - Pessoas reais: {len(real_people)}")

        # 2. VERIFICAR SE EXISTE EMPRESA "SISTEMA" OU "DEFAULT"
        print("\n2️⃣ VERIFICAR EMPRESA PADRÃO PARA ÓRFÃOS:")
        result = await conn.execute(
            text(
                """
            SELECT c.id, p.name as company_name
            FROM master.companies c
            JOIN master.people p ON p.id = c.person_id
            WHERE LOWER(p.name) LIKE '%sistema%'
               OR LOWER(p.name) LIKE '%admin%'
               OR LOWER(p.name) LIKE '%default%'
            ORDER BY c.id;
        """
            )
        )

        system_companies = list(result)
        if system_companies:
            print("   ✅ Empresas do sistema encontradas:")
            for company in system_companies:
                print(f"      - ID: {company.id} | Nome: {company.company_name}")
        else:
            print("   ⚠️  Nenhuma empresa do sistema encontrada")

        # 3. PROPOR ESTRATÉGIAS
        print("\n3️⃣ ESTRATÉGIAS PROPOSTAS:")

        print("\n   📋 ESTRATÉGIA A: CRIAR EMPRESA 'SISTEMA'")
        print("      1. Criar empresa 'Pro Team Care - Sistema'")
        print("      2. Associar todos os admins de sistema a esta empresa")
        print("      3. Manter isolation para dados administrativos")

        print("\n   📋 ESTRATÉGIA B: EMPRESA POR TIPO DE USUÁRIO")
        print("      1. 'Pro Team Care - Administração' para admins")
        print("      2. 'Pro Team Care - Testes' para dados de teste")
        print("      3. Analisar pessoas reais caso a caso")

        print("\n   📋 ESTRATÉGIA C: MIGRAÇÃO PARA PRIMEIRA EMPRESA")
        result = await conn.execute(
            text("SELECT MIN(id) as first_company FROM master.companies;")
        )
        first_company = result.scalar()
        print(f"      1. Migrar todos para empresa ID {first_company}")
        print("      2. Mais simples mas mistura dados administrativos")

        # 4. RECOMENDAR ESTRATÉGIA
        print("\n4️⃣ RECOMENDAÇÃO:")
        print("   🎯 ESTRATÉGIA A (Empresa Sistema) é a MELHOR opção:")
        print("      ✅ Mantém isolamento adequado")
        print("      ✅ Facilita administração futura")
        print("      ✅ Permite backup/restore independente")
        print("      ✅ Compliance com multi-tenancy")

        # 5. SCRIPT SQL PARA ESTRATÉGIA A
        print("\n5️⃣ SCRIPT SQL PARA IMPLEMENTAÇÃO:")
        print(
            """
   -- PASSO 1: Criar pessoa para empresa sistema
   INSERT INTO master.people (
       person_type, name, tax_id, status, is_active,
       lgpd_consent_version, created_at, updated_at
   ) VALUES (
       'PJ',
       'Pro Team Care - Sistema',
       '00000000000001',  -- CNPJ fictício para sistema
       'active',
       true,
       '1.0',
       NOW(),
       NOW()
   );

   -- PASSO 2: Criar empresa sistema
   INSERT INTO master.companies (
       person_id,
       settings,
       metadata,
       display_order,
       created_at,
       updated_at
   ) VALUES (
       (SELECT id FROM master.people WHERE name = 'Pro Team Care - Sistema'),
       '{"type": "system", "description": "Empresa para dados administrativos e de sistema"}',
       '{"created_by": "migration_script", "purpose": "system_administration"}',
       0,
       NOW(),
       NOW()
   );

   -- PASSO 3: Obter ID da empresa sistema
   -- SET @sistema_company_id = (SELECT id FROM master.companies c JOIN master.people p ON p.id = c.person_id WHERE p.name = 'Pro Team Care - Sistema');
        """
        )

        # 6. VALIDAÇÃO ANTES DA MIGRAÇÃO
        print("\n6️⃣ VALIDAÇÕES NECESSÁRIAS:")
        print("   ✅ Verificar se CNPJ '00000000000001' não existe")
        print("   ✅ Confirmar que pessoas órfãs não têm clientes")
        print("   ✅ Validar que não há estabelecimentos órfãos")

        # Executar validações
        result = await conn.execute(
            text("SELECT COUNT(*) FROM master.people WHERE tax_id = '00000000000001';")
        )
        cnpj_exists = result.scalar()

        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.clients c
            JOIN master.people p ON p.id = c.person_id
            LEFT JOIN master.companies co ON co.person_id = p.id
            WHERE co.id IS NULL;
        """
            )
        )
        orphan_clients = result.scalar()

        print(f"\n   📊 RESULTADOS DAS VALIDAÇÕES:")
        print(
            f"      - CNPJ '00000000000001' existe: {'❌ SIM' if cnpj_exists > 0 else '✅ NÃO'}"
        )
        print(
            f"      - Clientes órfãos: {orphan_clients} {'⚠️' if orphan_clients > 0 else '✅'}"
        )

        if cnpj_exists > 0:
            print("   ⚠️  ATENÇÃO: Precisa escolher outro CNPJ para empresa sistema")

        # 7. PRÓXIMOS PASSOS
        print("\n7️⃣ PRÓXIMOS PASSOS:")
        print("   1. ✅ Executar script de criação da empresa sistema")
        print("   2. ✅ Migrar pessoas órfãs para empresa sistema")
        print("   3. ✅ Validar integridade dos dados")
        print("   4. ✅ Prosseguir para FASE 2 (alteração de schema)")


async def main():
    """Função principal"""
    try:
        await strategy_for_orphan_data()
    except Exception as e:
        print(f"❌ Erro durante análise: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
