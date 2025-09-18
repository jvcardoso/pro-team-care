#!/usr/bin/env python3
"""
REORGANIZAR MENUS HIERÁRQUICOS USANDO ORM
Administração > Negócio (Empresas, Estabelecimentos, Clientes)
Administração > Segurança (Usuários, Perfis, Auditoria, Menus)
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import async_session
from app.infrastructure.orm.models import Menu


async def reorganize_menus():
    """Reorganizar menus usando ORM"""

    print("🔧 REORGANIZANDO MENUS HIERÁRQUICOS USANDO ORM")
    print("=" * 50)

    async with async_session() as session:

        # PASSO 1: Verificar se já existem os submenus
        print("\n1️⃣ Verificando menus existentes...")

        existing_query = select(Menu).where(
            Menu.parent_id == 20, Menu.name.in_(["Negócio", "Segurança"])
        )
        existing_result = await session.execute(existing_query)
        existing_menus = existing_result.scalars().all()

        if existing_menus:
            print(f"   ⚠️ Encontrados {len(existing_menus)} menus já existentes:")
            for menu in existing_menus:
                print(f"      - {menu.name} (ID: {menu.id})")

            # Remove os existentes para recriar
            for menu in existing_menus:
                await session.delete(menu)
            await session.commit()
            print("   🗑️ Menus existentes removidos")

        # PASSO 2: Criar submenu 'Negócio'
        print("\n2️⃣ Criando submenu Negócio...")

        negocio_menu = Menu(
            parent_id=20,
            level=2,
            sort_order=10,
            name="Negócio",
            slug="negocio",
            icon="Briefcase",
            description="Gestão de empresas, estabelecimentos e clientes",
            type="category",
            accepts_children=True,
            visible_in_menu=True,
            is_active=True,
            is_visible=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        session.add(negocio_menu)
        await session.flush()  # Para obter o ID
        negocio_id = negocio_menu.id
        print(f"   ✅ Negócio criado (ID: {negocio_id})")

        # PASSO 3: Criar submenu 'Segurança'
        print("\n3️⃣ Criando submenu Segurança...")

        seguranca_menu = Menu(
            parent_id=20,
            level=2,
            sort_order=20,
            name="Segurança",
            slug="seguranca",
            icon="Shield",
            description="Usuários, perfis, auditoria e menus",
            type="category",
            accepts_children=True,
            visible_in_menu=True,
            is_active=True,
            is_visible=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        session.add(seguranca_menu)
        await session.flush()  # Para obter o ID
        seguranca_id = seguranca_menu.id
        print(f"   ✅ Segurança criado (ID: {seguranca_id})")

        # PASSO 4: Mover menus para 'Negócio'
        print(f"\n4️⃣ Movendo menus para Negócio (ID: {negocio_id})...")

        menus_negocio = [(14, "Empresas"), (136, "Estabelecimentos"), (138, "Clientes")]

        for menu_id, nome in menus_negocio:
            await session.execute(
                update(Menu)
                .where(Menu.id == menu_id)
                .values(
                    parent_id=negocio_id,
                    level=3,
                    sort_order=menu_id % 100,  # Usar parte final do ID como ordem
                )
            )
            print(f"   📋 {nome} (ID: {menu_id}) movido para Negócio")

        # PASSO 5: Mover menus para 'Segurança'
        print(f"\n5️⃣ Movendo menus para Segurança (ID: {seguranca_id})...")

        menus_seguranca = [
            (21, "Usuários"),
            (22, "Perfis e Permissões"),
            (23, "Auditoria"),
        ]

        for menu_id, nome in menus_seguranca:
            await session.execute(
                update(Menu)
                .where(Menu.id == menu_id)
                .values(
                    parent_id=seguranca_id,
                    level=3,
                    sort_order=menu_id % 100,  # Usar parte final do ID como ordem
                )
            )
            print(f"   🔒 {nome} (ID: {menu_id}) movido para Segurança")

        # PASSO 6: Criar menu 'Menus' em Segurança
        print(f"\n6️⃣ Criando menu 'Menus' em Segurança...")

        menus_menu = Menu(
            parent_id=seguranca_id,
            level=3,
            sort_order=24,
            name="Menus",
            slug="menus",
            url="/admin/menus",
            icon="Menu",
            description="Gestão de menus do sistema",
            type="page",
            accepts_children=False,
            visible_in_menu=True,
            is_active=True,
            is_visible=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        session.add(menus_menu)
        await session.flush()
        print(f"   📋 Menu 'Menus' criado (ID: {menus_menu.id})")

        # PASSO 7: Commit de todas as mudanças
        await session.commit()
        print("\n💾 Todas as mudanças confirmadas no banco de dados")

        # PASSO 8: Verificar estrutura final
        print("\n7️⃣ VERIFICAÇÃO DA ESTRUTURA FINAL:")
        print("=" * 40)

        # Consultar estrutura final
        final_query = (
            select(Menu)
            .where(Menu.parent_id.in_([20, negocio_id, seguranca_id]))
            .order_by(Menu.parent_id, Menu.sort_order, Menu.name)
        )

        final_result = await session.execute(final_query)
        final_menus = final_result.scalars().all()

        print("\n📋 Administração (20)")

        # Organizar por parent_id
        by_parent = {}
        for menu in final_menus:
            if menu.parent_id not in by_parent:
                by_parent[menu.parent_id] = []
            by_parent[menu.parent_id].append(menu)

        # Mostrar submenus de Administração
        admin_submenus = by_parent.get(20, [])
        for submenu in admin_submenus:
            print(f"├── {submenu.name} ({submenu.id}) - {submenu.icon}")

            # Mostrar itens do submenu
            submenu_items = by_parent.get(submenu.id, [])
            for item in submenu_items:
                url_info = f" → {item.url}" if item.url else ""
                print(f"│   ├── {item.name} ({item.id}) - {item.icon}{url_info}")

        print(f"\n✅ REORGANIZAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"   📁 Negócio (ID: {negocio_id}): Empresas, Estabelecimentos, Clientes")
        print(
            f"   🔒 Segurança (ID: {seguranca_id}): Usuários, Perfis, Auditoria, Menus"
        )


async def main():
    """Função principal"""
    try:
        await reorganize_menus()
    except Exception as e:
        print(f"❌ Erro durante reorganização: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
