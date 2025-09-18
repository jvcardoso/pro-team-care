#!/usr/bin/env python3
"""
Script para analisar permissões detalhadas de cada role
"""

import asyncio
import sys

sys.path.append(".")

from sqlalchemy import text

from app.infrastructure.database import get_db


async def analyze_role_permissions():
    print("=== ANÁLISE DETALHADA DE PERMISSÕES POR ROLE ===\n")

    try:
        async for db in get_db():
            # Buscar roles com permissões
            roles_with_perms_query = text(
                """
                SELECT DISTINCT r.id, r.name, r.description, COUNT(rp.permission_id) as perm_count
                FROM master.roles r
                JOIN master.role_permissions rp ON r.id = rp.role_id
                WHERE r.is_active = true
                GROUP BY r.id, r.name, r.description
                ORDER BY r.name
            """
            )
            roles_result = await db.execute(roles_with_perms_query)
            roles = roles_result.fetchall()

            print("🔍 ANÁLISE DETALHADA DOS ROLES COM PERMISSÕES:\n")

            for role in roles:
                print(f"🎭 ROLE: {role.name} (ID: {role.id})")
                print(f"   📝 Descrição: {role.description or 'Sem descrição'}")
                print(f"   🔢 Total de permissões: {role.perm_count}")

                # Buscar permissões específicas do role
                perms_query = text(
                    """
                    SELECT p.name, p.context_level, p.module, p.action, p.resource
                    FROM master.permissions p
                    JOIN master.role_permissions rp ON p.id = rp.permission_id
                    WHERE rp.role_id = :role_id
                      AND p.is_active = true
                    ORDER BY p.context_level, p.module, p.name
                """
                )
                perms_result = await db.execute(perms_query, {"role_id": role.id})
                permissions = perms_result.fetchall()

                # Agrupar por contexto
                contexts = {}
                for perm in permissions:
                    ctx = perm.context_level
                    if ctx not in contexts:
                        contexts[ctx] = []
                    contexts[ctx].append(perm)

                print("   📋 Permissões por contexto:")
                for ctx, perms_list in contexts.items():
                    print(f"      🔸 {ctx.upper()}:")
                    for perm in perms_list:
                        print(f"         - {perm.name} ({perm.module}.{perm.action})")
                print()

            # Análise comparativa
            print("📊 ANÁLISE COMPARATIVA DOS ROLES ATIVOS:\n")

            # Roles ativos (com usuários)
            active_roles_query = text(
                """
                SELECT DISTINCT r.name, r.id, COUNT(DISTINCT ur.user_id) as user_count, COUNT(rp.permission_id) as perm_count
                FROM master.roles r
                LEFT JOIN master.user_roles ur ON r.id = ur.role_id AND ur.status = 'active' AND ur.deleted_at IS NULL
                LEFT JOIN master.role_permissions rp ON r.id = rp.role_id
                WHERE r.is_active = true
                  AND EXISTS (
                      SELECT 1 FROM master.user_roles ur2
                      JOIN master.users u ON ur2.user_id = u.id
                      WHERE ur2.role_id = r.id AND ur2.status = 'active' AND ur2.deleted_at IS NULL
                        AND u.is_active = true AND u.deleted_at IS NULL
                  )
                GROUP BY r.id, r.name
                ORDER BY user_count DESC, perm_count DESC
            """
            )
            active_result = await db.execute(active_roles_query)
            active_roles = active_result.fetchall()

            print("✅ ROLES ATIVOS (com usuários):")
            for role in active_roles:
                print(f"   - {role.name} (ID: {role.id})")
                print(f"     👥 Usuários: {role.user_count}")
                print(f"     🔐 Permissões: {role.perm_count}")
                print()

            # Roles inativos mas com permissões (podem ser reutilizados)
            inactive_with_perms_query = text(
                """
                SELECT r.name, r.id, COUNT(rp.permission_id) as perm_count
                FROM master.roles r
                LEFT JOIN master.role_permissions rp ON r.id = rp.role_id
                WHERE r.is_active = true
                  AND NOT EXISTS (
                      SELECT 1 FROM master.user_roles ur
                      JOIN master.users u ON ur.user_id = u.id
                      WHERE ur.role_id = r.id AND ur.status = 'active' AND ur.deleted_at IS NULL
                        AND u.is_active = true AND u.deleted_at IS NULL
                  )
                GROUP BY r.id, r.name
                HAVING COUNT(rp.permission_id) > 0
                ORDER BY perm_count DESC
            """
            )
            inactive_result = await db.execute(inactive_with_perms_query)
            inactive_roles = inactive_result.fetchall()

            print("⚠️ ROLES INATIVOS MAS COM PERMISSÕES (podem ser reutilizados):")
            for role in inactive_roles:
                print(
                    f"   - {role.name} (ID: {role.id}) - {role.perm_count} permissões"
                )
            print()

            # Sugestões de consolidação
            print("💡 SUGESTÕES PARA ORGANIZAÇÃO:\n")

            # Identificar roles similares
            similar_roles = [
                (
                    "admin_empresa",
                    "admin_empresa_customizado",
                    "granular_admin_empresa",
                ),
                ("super_admin", "granular_super_admin", "System Administrator"),
                ("admin_estabelecimento", "granular_admin_estabelecimento"),
                ("operador", "granular_operador", "granular_gerente_operacional"),
            ]

            print("🔄 ROLES SIMILARES QUE PODEM SER CONSOLIDADOS:")
            for similar_group in similar_roles:
                active_in_group = []
                inactive_in_group = []

                for role_name in similar_group:
                    # Verificar se está ativo
                    check_role_query = text(
                        """
                        SELECT r.id,
                               CASE WHEN EXISTS (
                                   SELECT 1 FROM master.user_roles ur
                                   JOIN master.users u ON ur.user_id = u.id
                                   WHERE ur.role_id = r.id AND ur.status = 'active' AND ur.deleted_at IS NULL
                                     AND u.is_active = true AND u.deleted_at IS NULL
                               ) THEN 'ACTIVE' ELSE 'INACTIVE' END as status
                        FROM master.roles r
                        WHERE r.name = :role_name AND r.is_active = true
                    """
                    )
                    check_result = await db.execute(
                        check_role_query, {"role_name": role_name}
                    )
                    check_data = check_result.fetchone()

                    if check_data:
                        if check_data.status == "ACTIVE":
                            active_in_group.append(role_name)
                        else:
                            inactive_in_group.append(role_name)

                if len(active_in_group) > 1:
                    print(f"   ⚠️ GRUPO SIMILAR COM MÚLTIPLOS ATIVOS:")
                    for role in active_in_group:
                        print(f"      - {role}")
                    print("      💡 Recomendação: Consolidar em um único role")
                elif active_in_group and inactive_in_group:
                    print(f"   ✅ GRUPO BEM ORGANIZADO:")
                    print(f"      ✅ Ativo: {active_in_group[0]}")
                    print(f"      🗑️ Inativos: {', '.join(inactive_in_group)}")
                    print("      💡 Pode remover os inativos se não forem necessários")
            print()

            print("🎯 PLANO DE AÇÃO RECOMENDADO:")
            print("   1. ✅ Manter apenas os 3 roles ativos atualmente")
            print("   2. 🗑️ Remover os 5 roles sem permissões")
            print(
                "   3. 🔄 Avaliar consolidação dos 11 roles não usados mas com permissões"
            )
            print(
                "   4. 📋 Documentar claramente as responsabilidades de cada role restante"
            )
            print("   5. 🧪 Testar thoroughly após qualquer remoção")

            break

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(analyze_role_permissions())
