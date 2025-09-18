#!/usr/bin/env python3
"""
Script para validar uso de roles/perfis no sistema
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.database import get_db


async def validate_roles_usage():
    print("=== VALIDAÇÃO DE USO DE ROLES/PERFIS ===\n")

    try:
        async for db in get_db():
            # 1. Buscar todos os roles cadastrados
            print("📋 ROLES CADASTRADOS NO SISTEMA:")
            roles_query = text(
                """
                SELECT id, name, description, is_active, created_at
                FROM master.roles
                WHERE is_active = true
                ORDER BY name
            """
            )
            roles_result = await db.execute(roles_query)
            all_roles = roles_result.fetchall()

            roles_data = []
            for role in all_roles:
                roles_data.append(
                    {
                        "id": role.id,
                        "name": role.name,
                        "description": role.description,
                        "created_at": role.created_at,
                    }
                )
                print(
                    f"   - {role.name} (ID: {role.id}) - {role.description or 'Sem descrição'}"
                )

            print(f"\n📊 Total de roles cadastrados: {len(roles_data)}\n")

            # 2. Verificar uso de cada role
            print("👥 ANÁLISE DE USO DOS ROLES:")
            roles_usage = []

            for role in roles_data:
                # Contar usuários ativos com este role
                usage_query = text(
                    """
                    SELECT COUNT(*) as user_count
                    FROM master.user_roles ur
                    WHERE ur.role_id = :role_id
                      AND ur.status = 'active'
                      AND ur.deleted_at IS NULL
                      AND EXISTS (
                          SELECT 1 FROM master.users u
                          WHERE u.id = ur.user_id
                            AND u.is_active = true
                            AND u.deleted_at IS NULL
                      )
                """
                )
                usage_result = await db.execute(usage_query, {"role_id": role["id"]})
                user_count = usage_result.scalar() or 0

                # Verificar se role tem permissões
                perms_query = text(
                    """
                    SELECT COUNT(*) as perm_count
                    FROM master.role_permissions rp
                    WHERE rp.role_id = :role_id
                """
                )
                perms_result = await db.execute(perms_query, {"role_id": role["id"]})
                perm_count = perms_result.scalar() or 0

                status = "✅ USADO" if user_count > 0 else "❌ NÃO USADO"
                perms_status = (
                    "✅ COM PERMISSÕES" if perm_count > 0 else "❌ SEM PERMISSÕES"
                )

                roles_usage.append(
                    {
                        "role": role,
                        "user_count": user_count,
                        "perm_count": perm_count,
                        "status": status,
                        "perms_status": perms_status,
                    }
                )

                print(f"   {status} - {role['name']} (ID: {role['id']})")
                print(f"      Usuários ativos: {user_count}")
                print(f"      Permissões: {perm_count} {perms_status}")
                print()

            # 3. Estatísticas gerais
            print("📈 ESTATÍSTICAS GERAIS:")
            used_roles = len([r for r in roles_usage if r["user_count"] > 0])
            unused_roles = len([r for r in roles_usage if r["user_count"] == 0])
            roles_with_perms = len([r for r in roles_usage if r["perm_count"] > 0])
            roles_without_perms = len([r for r in roles_usage if r["perm_count"] == 0])

            print(f"   ✅ Roles em uso: {used_roles}")
            print(f"   ❌ Roles não usados: {unused_roles}")
            print(f"   🔐 Roles com permissões: {roles_with_perms}")
            print(f"   🚫 Roles sem permissões: {roles_without_perms}")
            print()

            # 4. Recomendações
            print("💡 RECOMENDAÇÕES PARA ORGANIZAÇÃO:")

            # Roles não usados
            unused = [r for r in roles_usage if r["user_count"] == 0]
            if unused:
                print(f"\n🗑️ ROLES QUE PODEM SER REMOVIDOS ({len(unused)}):")
                for role in unused:
                    print(
                        f"   - {role['role']['name']} (ID: {role['role']['id']}) - {role['perms_status']}"
                    )

            # Roles sem permissões
            no_perms = [r for r in roles_usage if r["perm_count"] == 0]
            if no_perms:
                print(f"\n⚠️ ROLES SEM PERMISSÕES ({len(no_perms)}):")
                for role in no_perms:
                    usage = "USADO" if role["user_count"] > 0 else "NÃO USADO"
                    print(
                        f"   - {role['role']['name']} (ID: {role['role']['id']}) - {usage}"
                    )

            # Roles usados mas sem permissões (problema!)
            used_no_perms = [
                r for r in roles_usage if r["user_count"] > 0 and r["perm_count"] == 0
            ]
            if used_no_perms:
                print(
                    f"\n🚨 PROBLEMA CRÍTICO - ROLES USADOS SEM PERMISSÕES ({len(used_no_perms)}):"
                )
                for role in used_no_perms:
                    print(
                        f"   - {role['role']['name']} (ID: {role['role']['id']}) - {role['user_count']} usuários afetados"
                    )
                    print("     ❌ Estes usuários não têm acesso funcional ao sistema!")

            # Roles bem configurados
            well_configured = [
                r for r in roles_usage if r["user_count"] > 0 and r["perm_count"] > 0
            ]
            if well_configured:
                print(f"\n✅ ROLES BEM CONFIGURADOS ({len(well_configured)}):")
                for role in well_configured:
                    print(
                        f"   - {role['role']['name']} (ID: {role['role']['id']}) - {role['user_count']} usuários, {role['perm_count']} permissões"
                    )

            break

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(validate_roles_usage())
