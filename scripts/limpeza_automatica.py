#!/usr/bin/env python3
"""
LIMPEZA AUTOMÁTICA PÓS MULTI-TENANT
Executa limpeza sem confirmação
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def cleanup_automatic():
    """Limpeza automática"""

    print("🧹 LIMPEZA AUTOMÁTICA PÓS MULTI-TENANT")
    print("=" * 50)

    async with engine.begin() as conn:

        # Reset admin context
        await conn.execute(text("SELECT master.set_current_company_id(0)"))

        print("\n1️⃣ EXECUTANDO LIMPEZA ESTRATÉGICA:")

        # Contadores para relatório
        removed_counts = {}

        # 1. Remover addresses
        result = await conn.execute(text("DELETE FROM master.addresses"))
        removed_counts["addresses"] = result.rowcount
        print(f"   🗑️ Addresses removidos: {result.rowcount}")

        # 2. Remover emails
        result = await conn.execute(text("DELETE FROM master.emails"))
        removed_counts["emails"] = result.rowcount
        print(f"   🗑️ Emails removidos: {result.rowcount}")

        # 3. Remover phones
        result = await conn.execute(text("DELETE FROM master.phones"))
        removed_counts["phones"] = result.rowcount
        print(f"   🗑️ Phones removidos: {result.rowcount}")

        # 4. Remover clients de teste
        result = await conn.execute(
            text(
                """
            DELETE FROM master.clients
            WHERE person_id IN (
                SELECT p.id FROM master.people p
                WHERE p.name LIKE '%Teste%'
                OR p.name LIKE '%Test%'
                OR p.tax_id LIKE '99%'
            )
        """
            )
        )
        removed_counts["clients"] = result.rowcount
        print(f"   🗑️ Clients de teste removidos: {result.rowcount}")

        # 5. Remover establishments de teste
        result = await conn.execute(
            text(
                """
            DELETE FROM master.establishments
            WHERE person_id IN (
                SELECT p.id FROM master.people p
                WHERE p.name LIKE '%Teste%'
                OR p.name LIKE '%Test%'
                OR p.tax_id LIKE '99%'
            )
        """
            )
        )
        removed_counts["establishments"] = result.rowcount
        print(f"   🗑️ Establishments de teste removidos: {result.rowcount}")

        # 6. Remover usuários de teste
        result = await conn.execute(
            text(
                """
            DELETE FROM master.users
            WHERE email_address LIKE '%teste%'
            OR email_address LIKE '%test%'
            OR email_address LIKE '%@multitenant.com'
            OR email_address LIKE '%@rls.com'
        """
            )
        )
        removed_counts["users"] = result.rowcount
        print(f"   🗑️ Users de teste removidos: {result.rowcount}")

        # 7. Remover people de teste e órfãs
        result = await conn.execute(
            text(
                """
            DELETE FROM master.people
            WHERE name LIKE '%Teste%'
            OR name LIKE '%Test%'
            OR name LIKE '%TESTE%'
            OR tax_id LIKE '99%'
            OR (name LIKE '%João Silva%' AND tax_id LIKE '%12345%')
        """
            )
        )
        removed_counts["people"] = result.rowcount
        print(f"   🗑️ People de teste removidos: {result.rowcount}")

        # 8. Remover companies órfãs
        result = await conn.execute(
            text(
                """
            DELETE FROM master.companies
            WHERE person_id NOT IN (SELECT id FROM master.people)
        """
            )
        )
        removed_counts["companies"] = result.rowcount
        print(f"   🗑️ Companies órfãs removidas: {result.rowcount}")

        print("\n2️⃣ VERIFICAÇÃO PÓS-LIMPEZA:")

        # Contagem final
        final_counts = {}
        tables = ["people", "users", "companies", "establishments", "clients", "menus"]

        for table in tables:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM master.{table}"))
            final_counts[table] = result.scalar()
            print(f"   📊 {table:15}: {final_counts[table]:6} registros")

        # Verificar integridade
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.people p
            LEFT JOIN master.companies c ON c.person_id = p.id
            WHERE c.id IS NULL
        """
            )
        )
        orphan_people = result.scalar()

        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.users u
            LEFT JOIN master.people p ON p.id = u.person_id
            WHERE p.id IS NULL
        """
            )
        )
        orphan_users = result.scalar()

        print(f"\n3️⃣ INTEGRIDADE:")
        print(f"   📋 Pessoas órfãs: {orphan_people}")
        print(f"   📋 Users órfãos: {orphan_users}")

        # Verificar índices multi-tenant
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM pg_indexes
            WHERE schemaname = 'master'
            AND tablename IN ('people', 'users')
            AND indexname LIKE '%company%'
        """
            )
        )
        company_indexes = result.scalar()

        print(f"   📋 Índices company: {company_indexes}")

        print(f"\n4️⃣ RESUMO DA LIMPEZA:")
        total_removed = sum(removed_counts.values())
        print(f"   📊 Total registros removidos: {total_removed}")

        for table, count in removed_counts.items():
            if count > 0:
                print(f"      - {table}: {count}")

        print(f"\n   📊 DADOS FINAIS MANTIDOS:")
        essential_data = {
            "Users": final_counts.get("users", 0),
            "Companies": final_counts.get("companies", 0),
            "Menus": final_counts.get("menus", 0),
            "People": final_counts.get("people", 0),
        }

        for name, count in essential_data.items():
            print(f"      - {name}: {count}")

        # Status final
        success = (
            orphan_people == 0
            and orphan_users == 0
            and final_counts.get("users", 0) > 0
            and final_counts.get("companies", 0) > 0
        )

        if success:
            print(f"\n   🎉 LIMPEZA CONCLUÍDA COM SUCESSO!")
            print(f"   ✅ Base de dados otimizada")
            print(f"   ✅ Integridade multi-tenant mantida")
            print(f"   ✅ Dados essenciais preservados")
            print(f"\n   🚀 SISTEMA PRONTO PARA USO!")
        else:
            print(f"\n   ⚠️  Limpeza com ressalvas")
            print(f"   🔧 Verificar dados órfãos")


async def main():
    """Função principal"""
    try:
        await cleanup_automatic()
    except Exception as e:
        print(f"❌ Erro durante limpeza: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
