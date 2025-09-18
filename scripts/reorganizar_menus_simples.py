#!/usr/bin/env python3
"""
REORGANIZAR MENUS HIERÁRQUICOS - VERSÃO SIMPLES
Administração > Negócio (Empresas, Estabelecimentos, Clientes)
Administração > Segurança (Usuários, Perfis, Auditoria, Menus)
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def reorganize_menus_simple():
    """Reorganizar menus usando SQL direto"""

    print("🔧 REORGANIZANDO MENUS HIERÁRQUICOS")
    print("=" * 40)

    async with engine.begin() as conn:
        await conn.execute(text("SELECT master.set_current_company_id(0)"))

        # PASSO 1: Verificar menus existentes
        print("\n1️⃣ Verificando menus existentes...")

        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.menus
            WHERE parent_id = 20 AND name IN ('Negócio', 'Segurança')
        """
            )
        )
        existing_count = result.scalar()

        if existing_count > 0:
            print(
                f"   ⚠️ Encontrados {existing_count} menus já existentes - removendo..."
            )
            await conn.execute(
                text(
                    """
                DELETE FROM master.menus
                WHERE parent_id = 20 AND name IN ('Negócio', 'Segurança')
            """
                )
            )
            print("   🗑️ Menus existentes removidos")

        # PASSO 2: Obter próximo ID disponível
        result = await conn.execute(
            text(
                """
            SELECT COALESCE(MAX(id), 0) + 1 FROM master.menus
        """
            )
        )
        next_id = result.scalar()
        print(f"   📋 Próximo ID disponível: {next_id}")

        # PASSO 3: Inserir submenu Negócio
        print(f"\n2️⃣ Criando submenu Negócio (ID: {next_id})...")

        await conn.execute(
            text(
                f"""
            INSERT INTO master.menus (
                id, parent_id, level, sort_order, name, slug, icon, description,
                type, accepts_children, visible_in_menu, is_active, is_visible,
                created_at, updated_at
            ) VALUES (
                {next_id}, 20, 2, 10, 'Negócio', 'negocio', 'Briefcase', 'Gestão de empresas, estabelecimentos e clientes',
                'menu', true, true, true, true,
                NOW(), NOW()
            )
        """
            )
        )

        negocio_id = next_id
        next_id += 1
        print(f"   ✅ Negócio criado (ID: {negocio_id})")

        # PASSO 4: Inserir submenu Segurança
        print(f"\n3️⃣ Criando submenu Segurança (ID: {next_id})...")

        await conn.execute(
            text(
                f"""
            INSERT INTO master.menus (
                id, parent_id, level, sort_order, name, slug, icon, description,
                type, accepts_children, visible_in_menu, is_active, is_visible,
                created_at, updated_at
            ) VALUES (
                {next_id}, 20, 2, 20, 'Segurança', 'seguranca', 'Shield', 'Usuários, perfis, auditoria e menus',
                'menu', true, true, true, true,
                NOW(), NOW()
            )
        """
            )
        )

        seguranca_id = next_id
        next_id += 1
        print(f"   ✅ Segurança criado (ID: {seguranca_id})")

        # PASSO 5: Mover menus para Negócio
        print(f"\n4️⃣ Movendo menus para Negócio...")

        menus_negocio = [(14, "Empresas"), (136, "Estabelecimentos"), (138, "Clientes")]

        for menu_id, nome in menus_negocio:
            await conn.execute(
                text(
                    f"""
                UPDATE master.menus
                SET parent_id = {negocio_id}, level = 3, sort_order = {menu_id}
                WHERE id = {menu_id}
            """
                )
            )
            print(f"   📋 {nome} (ID: {menu_id}) movido para Negócio")

        # PASSO 6: Mover menus para Segurança
        print(f"\n5️⃣ Movendo menus para Segurança...")

        menus_seguranca = [
            (21, "Usuários"),
            (22, "Perfis e Permissões"),
            (23, "Auditoria"),
        ]

        for menu_id, nome in menus_seguranca:
            await conn.execute(
                text(
                    f"""
                UPDATE master.menus
                SET parent_id = {seguranca_id}, level = 3, sort_order = {menu_id}
                WHERE id = {menu_id}
            """
                )
            )
            print(f"   🔒 {nome} (ID: {menu_id}) movido para Segurança")

        # PASSO 7: Criar menu Menus
        print(f"\n6️⃣ Criando menu 'Menus' em Segurança...")

        await conn.execute(
            text(
                f"""
            INSERT INTO master.menus (
                id, parent_id, level, sort_order, name, slug, url, icon, description,
                type, accepts_children, visible_in_menu, is_active, is_visible,
                created_at, updated_at
            ) VALUES (
                {next_id}, {seguranca_id}, 3, 24, 'Menus', 'menus', '/admin/menus', 'Menu', 'Gestão de menus do sistema',
                'menu', false, true, true, true,
                NOW(), NOW()
            )
        """
            )
        )

        menus_menu_id = next_id
        print(f"   📋 Menu 'Menus' criado (ID: {menus_menu_id})")

        # PASSO 8: Verificar estrutura final
        print(f"\n7️⃣ VERIFICAÇÃO DA ESTRUTURA FINAL:")
        print("=" * 40)

        result = await conn.execute(
            text(
                f"""
            SELECT
                m.id, m.name, m.icon, m.url,
                CASE
                    WHEN m.id = 20 THEN 'ROOT'
                    WHEN m.parent_id = 20 THEN 'ADMIN_SUBMENU'
                    WHEN m.parent_id = {negocio_id} THEN 'NEGOCIO'
                    WHEN m.parent_id = {seguranca_id} THEN 'SEGURANCA'
                    ELSE 'OTHER'
                END as category
            FROM master.menus m
            WHERE m.id = 20 OR m.parent_id IN (20, {negocio_id}, {seguranca_id})
            ORDER BY
                CASE WHEN m.id = 20 THEN 0
                     WHEN m.parent_id = 20 THEN 1
                     ELSE 2 END,
                m.sort_order, m.name
        """
            )
        )

        menus = result.fetchall()
        current_category = None

        for menu in menus:
            if menu.category != current_category:
                current_category = menu.category

                if menu.category == "ROOT":
                    print(f"\n📋 {menu.name} ({menu.id})")
                elif menu.category == "ADMIN_SUBMENU":
                    print(f"\n  📁 SUBMENUS:")
                elif menu.category in ["NEGOCIO", "SEGURANCA"]:
                    section_name = (
                        "Negócio" if menu.category == "NEGOCIO" else "Segurança"
                    )
                    print(f"\n    {section_name}:")

            if menu.category == "ADMIN_SUBMENU":
                print(f"    ├── {menu.name} ({menu.id}) - {menu.icon}")
            elif menu.category in ["NEGOCIO", "SEGURANCA"]:
                url_info = f" → {menu.url}" if menu.url else ""
                print(f"      ├── {menu.name} ({menu.id}) - {menu.icon}{url_info}")

        print(f"\n✅ REORGANIZAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"   📁 Negócio (ID: {negocio_id}): Empresas, Estabelecimentos, Clientes")
        print(
            f"   🔒 Segurança (ID: {seguranca_id}): Usuários, Perfis, Auditoria, Menus"
        )

        print(f"\n🎯 ESTRUTURA FINAL:")
        print(f"   Administração")
        print(f"   ├── Negócio")
        print(f"   │   ├── Empresas")
        print(f"   │   ├── Estabelecimentos")
        print(f"   │   └── Clientes")
        print(f"   └── Segurança")
        print(f"       ├── Usuários")
        print(f"       ├── Perfis e Permissões")
        print(f"       ├── Auditoria")
        print(f"       └── Menus")


async def main():
    """Função principal"""
    try:
        await reorganize_menus_simple()
    except Exception as e:
        print(f"❌ Erro durante reorganização: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
