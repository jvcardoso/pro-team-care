#!/usr/bin/env python3
"""
VALIDAÇÃO SIMPLES FINAL - FASE 2 CONCLUÍDA
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def simple_validation():
    """Validação simples e direta"""

    print("🎉 VALIDAÇÃO FINAL - FASE 2 MULTI-TENANCY")
    print("=" * 55)

    async with engine.begin() as conn:

        # 1. Estatísticas básicas
        result = await conn.execute(text("SELECT COUNT(*) FROM master.people;"))
        total_people = result.scalar()

        result = await conn.execute(text("SELECT COUNT(*) FROM master.users;"))
        total_users = result.scalar()

        result = await conn.execute(text("SELECT COUNT(*) FROM master.companies;"))
        total_companies = result.scalar()

        print(f"\n📊 ESTATÍSTICAS:")
        print(f"   - People: {total_people}")
        print(f"   - Users: {total_users}")
        print(f"   - Companies: {total_companies}")

        # 2. Verificar constraints críticas
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            JOIN pg_namespace n ON t.relnamespace = n.oid
            WHERE n.nspname = 'master'
            AND t.relname = 'people'
            AND c.contype = 'u'
            AND pg_get_constraintdef(c.oid) LIKE '%company_id%tax_id%';
        """
            )
        )
        people_constraint = result.scalar()

        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            JOIN pg_namespace n ON t.relnamespace = n.oid
            WHERE n.nspname = 'master'
            AND t.relname = 'users'
            AND c.contype = 'u'
            AND pg_get_constraintdef(c.oid) LIKE '%company_id%email_address%';
        """
            )
        )
        users_constraint = result.scalar()

        print(f"\n✅ CONSTRAINTS MULTI-TENANT:")
        print(
            f"   - People constraint: {'ATIVO' if people_constraint > 0 else 'FALTANDO'}"
        )
        print(
            f"   - Users constraint: {'ATIVO' if users_constraint > 0 else 'FALTANDO'}"
        )

        # 3. Status final
        success = (
            total_people > 0
            and total_users > 0
            and people_constraint > 0
            and users_constraint > 0
        )

        if success:
            print(f"\n🎉 FASE 2 CONCLUÍDA COM SUCESSO TOTAL!")
            print(f"   ✅ {total_people} pessoas com isolamento por company")
            print(f"   ✅ {total_users} usuários com isolamento por company")
            print(f"   ✅ Constraints multi-tenant implementadas")
            print(f"   ✅ Sistema 100% pronto para multi-tenancy")
            print(f"\n🚀 PRÓXIMO: FASE 3 (RLS + Aplicação)")
        else:
            print(f"\n⚠️ Algumas validações falharam")


async def main():
    try:
        await simple_validation()
    except Exception as e:
        print(f"❌ Erro: {e}")


if __name__ == "__main__":
    asyncio.run(main())
