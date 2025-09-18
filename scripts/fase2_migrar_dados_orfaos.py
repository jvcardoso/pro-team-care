#!/usr/bin/env python3
"""
FASE 2: MIGRAÇÃO DE DADOS ÓRFÃOS
Script para executar a migração dos 12 registros órfãos para empresa sistema
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def migrate_orphan_data():
    """Executar migração dos dados órfãos para empresa sistema"""

    print("🚀 FASE 2: MIGRAÇÃO DE DADOS ÓRFÃOS")
    print("=" * 60)

    async with engine.begin() as conn:

        # PASSO 1: VERIFICAÇÕES PRÉ-MIGRAÇÃO
        print("\n1️⃣ VERIFICAÇÕES PRÉ-MIGRAÇÃO:")

        # Verificar se empresa sistema já existe
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.people
            WHERE name = 'Pro Team Care - Sistema' OR tax_id = '00000000000001';
        """
            )
        )
        sistema_exists = result.scalar()

        if sistema_exists > 0:
            print("   ⚠️  Empresa sistema já existe, pulando criação...")

            # Obter ID da empresa sistema existente
            result = await conn.execute(
                text(
                    """
                SELECT c.id FROM master.companies c
                JOIN master.people p ON p.id = c.person_id
                WHERE p.name = 'Pro Team Care - Sistema' OR p.tax_id = '00000000000001';
            """
                )
            )
            sistema_company_id = result.scalar()

        else:
            print("   ✅ Empresa sistema não existe, será criada")
            sistema_company_id = None

        # Contar pessoas órfãs atuais
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.people p
            LEFT JOIN master.companies c ON c.person_id = p.id
            WHERE c.id IS NULL;
        """
            )
        )
        orphans_count = result.scalar()
        print(f"   📊 Pessoas órfãs encontradas: {orphans_count}")

        if orphans_count == 0:
            print("   ✅ Nenhuma pessoa órfã encontrada, migração desnecessária!")
            return

        # PASSO 2: CRIAR EMPRESA SISTEMA (se não existir)
        if sistema_company_id is None:
            print("\n2️⃣ CRIANDO EMPRESA SISTEMA:")

            # 2.1: Criar pessoa para empresa sistema
            result = await conn.execute(
                text(
                    """
                INSERT INTO master.people (
                    person_type, name, tax_id, status, is_active,
                    lgpd_consent_version, created_at, updated_at
                ) VALUES (
                    'PJ',
                    'Pro Team Care - Sistema',
                    '00000000000001',
                    'active',
                    true,
                    '1.0',
                    NOW(),
                    NOW()
                ) RETURNING id;
            """
                )
            )
            person_sistema_id = result.scalar()
            print(f"   ✅ Pessoa sistema criada com ID: {person_sistema_id}")

            # 2.2: Criar empresa sistema
            result = await conn.execute(
                text(
                    """
                INSERT INTO master.companies (
                    person_id,
                    settings,
                    metadata,
                    display_order,
                    created_at,
                    updated_at
                ) VALUES (
                    :person_id,
                    '{"type": "system", "description": "Empresa para dados administrativos e de sistema"}',
                    '{"created_by": "migration_script", "purpose": "system_administration", "migration_date": "2025-09-14"}',
                    0,
                    NOW(),
                    NOW()
                ) RETURNING id;
            """
                ),
                {"person_id": person_sistema_id},
            )

            sistema_company_id = result.scalar()
            print(f"   ✅ Empresa sistema criada com ID: {sistema_company_id}")

        else:
            print(f"\n2️⃣ EMPRESA SISTEMA JÁ EXISTE (ID: {sistema_company_id})")

        # PASSO 3: MIGRAR PESSOAS ÓRFÃS
        print(
            f"\n3️⃣ MIGRANDO PESSOAS ÓRFÃS PARA EMPRESA SISTEMA (ID: {sistema_company_id}):"
        )

        # 3.1: Obter lista de pessoas órfãs
        result = await conn.execute(
            text(
                """
            SELECT p.id, p.name, p.tax_id, p.person_type
            FROM master.people p
            LEFT JOIN master.companies c ON c.person_id = p.id
            WHERE c.id IS NULL
            ORDER BY p.id;
        """
            )
        )

        orphan_people = list(result)
        print(f"   📋 Encontradas {len(orphan_people)} pessoas para migrar:")

        migrated_count = 0
        for person in orphan_people:
            print(
                f"      - Migrando: ID {person.id:2} | {person.name:30} | {person.tax_id}"
            )

            try:
                # Criar nova empresa para cada pessoa órfã (relacionamento 1:1 atual)
                result = await conn.execute(
                    text(
                        """
                    INSERT INTO master.companies (
                        person_id,
                        settings,
                        metadata,
                        display_order,
                        created_at,
                        updated_at
                    ) VALUES (
                        :person_id,
                        :settings,
                        :metadata,
                        999,
                        NOW(),
                        NOW()
                    ) RETURNING id;
                """
                    ),
                    {
                        "person_id": person.id,
                        "settings": '{"type": "migrated_orphan", "original_status": "orphan"}',
                        "metadata": f'{{"migrated_from": "orphan", "migration_date": "2025-09-14", "original_person_id": {person.id}}}',
                    },
                )

                new_company_id = result.scalar()
                migrated_count += 1
                print(
                    f"        ✅ Criada empresa ID {new_company_id} para pessoa {person.id}"
                )

            except Exception as e:
                print(f"        ❌ Erro ao migrar pessoa {person.id}: {e}")

        print(f"   📊 Total migrado com sucesso: {migrated_count}/{len(orphan_people)}")

        # PASSO 4: VALIDAÇÕES PÓS-MIGRAÇÃO
        print("\n4️⃣ VALIDAÇÕES PÓS-MIGRAÇÃO:")

        # 4.1: Verificar pessoas órfãs restantes
        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.people p
            LEFT JOIN master.companies c ON c.person_id = p.id
            WHERE c.id IS NULL;
        """
            )
        )
        remaining_orphans = result.scalar()

        if remaining_orphans == 0:
            print("   ✅ Nenhuma pessoa órfã restante!")
        else:
            print(f"   ⚠️  Ainda existem {remaining_orphans} pessoas órfãs")

        # 4.2: Validar integridade do relacionamento
        result = await conn.execute(
            text(
                """
            SELECT
                COUNT(p.id) as total_pessoas,
                COUNT(c.id) as total_empresas,
                COUNT(CASE WHEN c.id IS NOT NULL THEN 1 END) as pessoas_com_empresa
            FROM master.people p
            LEFT JOIN master.companies c ON c.person_id = p.id;
        """
            )
        )

        stats = result.fetchone()
        print(f"   📊 Estatísticas finais:")
        print(f"      - Total pessoas: {stats.total_pessoas}")
        print(f"      - Total empresas: {stats.total_empresas}")
        print(f"      - Pessoas com empresa: {stats.pessoas_com_empresa}")

        if stats.total_pessoas == stats.pessoas_com_empresa:
            print("   ✅ Relacionamento 1:1 people↔companies restaurado!")
        else:
            print(
                f"   ⚠️  {stats.total_pessoas - stats.pessoas_com_empresa} pessoas ainda sem empresa"
            )

        # 4.3: Verificar constraint UNIQUE ainda funciona
        result = await conn.execute(
            text(
                """
            SELECT tax_id, COUNT(*) as count
            FROM master.people
            WHERE tax_id IS NOT NULL AND tax_id != ''
            GROUP BY tax_id
            HAVING COUNT(*) > 1;
        """
            )
        )

        duplicates = list(result)
        if duplicates:
            print(f"   ⚠️  {len(duplicates)} tax_ids duplicados encontrados:")
            for dup in duplicates[:3]:  # Mostrar apenas 3 primeiros
                print(f"      - {dup.tax_id}: {dup.count} ocorrências")
        else:
            print("   ✅ Nenhum tax_id duplicado - constraint funcionando")

        # PASSO 5: RESUMO FINAL
        print("\n5️⃣ RESUMO DA MIGRAÇÃO:")

        if remaining_orphans == 0 and migrated_count == len(orphan_people):
            print("   🎉 MIGRAÇÃO DE DADOS ÓRFÃOS CONCLUÍDA COM SUCESSO!")
            print("   ✅ Todas as pessoas órfãs foram associadas a empresas")
            print("   ✅ Relacionamento 1:1 people↔companies restaurado")
            print("   ✅ Pronto para FASE 2B: Alteração de schema")
        else:
            print("   ⚠️  MIGRAÇÃO PARCIALMENTE CONCLUÍDA:")
            print(f"      - {migrated_count} pessoas migradas com sucesso")
            print(f"      - {remaining_orphans} pessoas ainda órfãs")
            print("   🔧 AÇÃO NECESSÁRIA: Analisar pessoas não migradas")


async def main():
    """Função principal"""
    try:
        await migrate_orphan_data()
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
