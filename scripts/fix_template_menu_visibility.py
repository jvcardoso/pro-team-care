#!/usr/bin/env python3
"""
Script para tornar o menu 'Templates & Exemplos' visível no banco de dados
"""

import asyncio
import os
import sys

# Adicionar o diretório raiz do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

from config.settings import get_settings


async def fix_template_menu_visibility():
    """Torna o menu Templates & Exemplos visível"""
    settings = get_settings()

    # Criar engine síncrono para este script simples
    DATABASE_URL = f"postgresql://{settings.db_username}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_database}"

    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            # Verificar se o menu existe
            result = conn.execute(
                text(
                    """
                SELECT id, name, is_visible
                FROM master.menus
                WHERE name LIKE '%Template%' OR name LIKE '%Exemplo%'
                ORDER BY id
            """
                )
            )

            menus = result.fetchall()
            print(f"📋 Menus encontrados com 'Template' ou 'Exemplo': {len(menus)}")

            for menu in menus:
                print(f"  - ID: {menu[0]}, Nome: {menu[1]}, Visível: {menu[2]}")

            if menus:
                # Atualizar todos para visível
                for menu in menus:
                    if not menu[2]:  # Se não está visível
                        conn.execute(
                            text(
                                """
                            UPDATE master.menus
                            SET is_visible = true,
                                visible_in_menu = true,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = :menu_id
                        """
                            ),
                            {"menu_id": menu[0]},
                        )

                        print(
                            f"✅ Menu '{menu[1]}' (ID: {menu[0]}) foi tornado visível"
                        )
                    else:
                        print(f"ℹ️ Menu '{menu[1]}' (ID: {menu[0]}) já está visível")

                conn.commit()
                print("\n🎉 Alterações salvas com sucesso!")

                # Verificar resultado final
                result = conn.execute(
                    text(
                        """
                    SELECT id, name, is_visible, visible_in_menu
                    FROM master.menus
                    WHERE name LIKE '%Template%' OR name LIKE '%Exemplo%'
                    ORDER BY id
                """
                    )
                )

                updated_menus = result.fetchall()
                print("\n📋 Estado final dos menus:")
                for menu in updated_menus:
                    print(
                        f"  - ID: {menu[0]}, Nome: {menu[1]}, Visível: {menu[2]}, Visível no Menu: {menu[3]}"
                    )

            else:
                print("⚠️ Nenhum menu encontrado com 'Template' ou 'Exemplo' no nome")

                # Listar todos os menus para debug
                result = conn.execute(
                    text(
                        """
                    SELECT id, name, is_visible
                    FROM master.menus
                    ORDER BY sort_order, id
                    LIMIT 20
                """
                    )
                )

                all_menus = result.fetchall()
                print("\n📋 Primeiros 20 menus no sistema:")
                for menu in all_menus:
                    print(f"  - ID: {menu[0]}, Nome: {menu[1]}, Visível: {menu[2]}")

    except Exception as e:
        print(f"❌ Erro ao alterar visibilidade do menu: {e}")
        return False

    return True


if __name__ == "__main__":
    print("🔧 Corrigindo visibilidade do menu Templates & Exemplos...")

    result = asyncio.run(fix_template_menu_visibility())

    if result:
        print("\n✅ Script executado com sucesso!")
        print("💡 Agora atualize a página no navegador para ver o menu aparecer")
    else:
        print("\n❌ Script falhou. Verifique os logs acima.")
