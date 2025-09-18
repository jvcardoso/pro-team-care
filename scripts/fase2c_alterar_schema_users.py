#!/usr/bin/env python3
"""
FASE 2C: ALTERAÇÃO DE SCHEMA - TABELA USERS
Script para adicionar company_id na tabela users e alterar constraints
"""

import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.database import engine


async def alter_users_schema():
    """Adicionar company_id na tabela users e alterar constraints"""

    print("🔧 FASE 2C: ALTERAÇÃO DE SCHEMA - TABELA USERS")
    print("=" * 60)

    async with engine.begin() as conn:

        # PASSO 1: VERIFICAÇÕES PRÉ-ALTERAÇÃO
        print("\n1️⃣ VERIFICAÇÕES PRÉ-ALTERAÇÃO:")

        # Verificar se coluna company_id já existe
        result = await conn.execute(
            text(
                """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'master'
            AND table_name = 'users'
            AND column_name = 'company_id';
        """
            )
        )
        company_id_exists = result.fetchone()

        if company_id_exists:
            print("   ⚠️  Coluna company_id já existe, script já executado!")
            print("   ✅ Pulando para validações finais...")
        else:
            print("   ✅ Coluna company_id não existe, será criada")

        # Verificar estrutura atual da tabela users
        result = await conn.execute(
            text(
                """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'master'
            AND table_name = 'users'
            AND column_name IN ('person_id', 'email_address')
            ORDER BY ordinal_position;
        """
            )
        )

        current_columns = list(result)
        print("   📋 Colunas atuais relevantes:")
        for col in current_columns:
            print(
                f"      - {col.column_name}: {col.data_type} | NULL: {col.is_nullable}"
            )

        # Verificar constraints atuais na tabela users
        result = await conn.execute(
            text(
                """
            SELECT conname, contype, pg_get_constraintdef(c.oid) as definition
            FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            JOIN pg_namespace n ON t.relnamespace = n.oid
            WHERE n.nspname = 'master'
            AND t.relname = 'users'
            AND c.contype = 'u'
            AND pg_get_constraintdef(c.oid) LIKE '%email_address%';
        """
            )
        )

        current_constraints = list(result)
        print("   📋 Constraints atuais:")
        for constraint in current_constraints:
            print(f"      - {constraint.conname}: {constraint.definition}")

        # Verificar relacionamento users → people → companies
        result = await conn.execute(
            text(
                """
            SELECT
                COUNT(u.id) as total_users,
                COUNT(p.id) as users_with_person,
                COUNT(p.company_id) as users_with_company
            FROM master.users u
            LEFT JOIN master.people p ON p.id = u.person_id;
        """
            )
        )

        relationships = result.fetchone()
        print(f"   📊 Relacionamentos:")
        print(f"      - Total usuários: {relationships.total_users}")
        print(f"      - Usuários com pessoa: {relationships.users_with_person}")
        print(
            f"      - Usuários com empresa (via pessoa): {relationships.users_with_company}"
        )

        if relationships.total_users != relationships.users_with_company:
            missing = relationships.total_users - relationships.users_with_company
            print(f"   ⚠️  {missing} usuários não têm empresa via pessoa")

        # PASSO 2: ADICIONAR COLUNA COMPANY_ID (se não existir)
        if not company_id_exists:
            print("\n2️⃣ ADICIONANDO COLUNA COMPANY_ID:")

            print("   ⏳ Adicionando coluna company_id...")
            await conn.execute(
                text(
                    """
                ALTER TABLE master.users
                ADD COLUMN company_id INTEGER;
            """
                )
            )
            print("   ✅ Coluna company_id adicionada")

            # PASSO 3: POPULAR COLUNA COMPANY_ID
            print("\n3️⃣ POPULANDO COLUNA COMPANY_ID:")

            print(
                "   ⏳ Atualizando company_id baseado no relacionamento person → company..."
            )
            result = await conn.execute(
                text(
                    """
                UPDATE master.users
                SET company_id = p.company_id
                FROM master.people p
                WHERE p.id = users.person_id
                AND users.company_id IS NULL;
            """
                )
            )
            updated_rows = result.rowcount
            print(f"   ✅ {updated_rows} registros atualizados")

            # Verificar se todos foram atualizados
            result = await conn.execute(
                text(
                    """
                SELECT COUNT(*) FROM master.users WHERE company_id IS NULL;
            """
                )
            )
            null_company_ids = result.scalar()

            if null_company_ids > 0:
                print(f"   ❌ ERRO: {null_company_ids} usuários ainda sem company_id!")

                # Listar usuários problemáticos
                result = await conn.execute(
                    text(
                        """
                    SELECT u.id, u.email_address, u.person_id
                    FROM master.users u
                    LEFT JOIN master.people p ON p.id = u.person_id
                    WHERE u.company_id IS NULL
                    LIMIT 5;
                """
                    )
                )

                problem_users = list(result)
                print("   📋 Usuários problemáticos:")
                for user in problem_users:
                    print(
                        f"      - User ID {user.id}: {user.email_address} | Person ID: {user.person_id}"
                    )

                print("   🛑 PARAR: Resolver usuários sem pessoa ou empresa primeiro")
                return
            else:
                print("   ✅ Todos os usuários têm company_id preenchido")

            # PASSO 4: ADICIONAR NOT NULL CONSTRAINT
            print("\n4️⃣ ADICIONANDO NOT NULL CONSTRAINT:")

            print("   ⏳ Definindo company_id como NOT NULL...")
            await conn.execute(
                text(
                    """
                ALTER TABLE master.users
                ALTER COLUMN company_id SET NOT NULL;
            """
                )
            )
            print("   ✅ Constraint NOT NULL adicionada")

            # PASSO 5: ADICIONAR FOREIGN KEY
            print("\n5️⃣ ADICIONANDO FOREIGN KEY:")

            print("   ⏳ Adicionando referência à tabela companies...")
            await conn.execute(
                text(
                    """
                ALTER TABLE master.users
                ADD CONSTRAINT fk_users_company
                FOREIGN KEY (company_id) REFERENCES master.companies(id);
            """
                )
            )
            print("   ✅ Foreign key constraint adicionada")

            # PASSO 6: REMOVER CONSTRAINT UNIQUE PROBLEMÁTICA
            print("\n6️⃣ REMOVENDO CONSTRAINT UNIQUE PROBLEMÁTICA:")

            for constraint in current_constraints:
                if (
                    "email_address" in constraint.definition.lower()
                    and "company_id" not in constraint.definition.lower()
                ):
                    print(
                        f"   ⏳ Removendo constraint problemática: {constraint.conname}"
                    )
                    await conn.execute(
                        text(
                            f"""
                        ALTER TABLE master.users
                        DROP CONSTRAINT {constraint.conname};
                    """
                        )
                    )
                    print(f"   ✅ Constraint {constraint.conname} removida")

            # PASSO 7: ADICIONAR NOVA CONSTRAINT UNIQUE (company_id, email_address)
            print("\n7️⃣ ADICIONANDO CONSTRAINT MULTI-TENANT:")

            print("   ⏳ Adicionando constraint UNIQUE (company_id, email_address)...")
            await conn.execute(
                text(
                    """
                ALTER TABLE master.users
                ADD CONSTRAINT users_company_email_unique
                UNIQUE (company_id, email_address);
            """
                )
            )
            print("   ✅ Constraint multi-tenant adicionada")

            # PASSO 8: ADICIONAR ÍNDICES OTIMIZADOS
            print("\n8️⃣ ADICIONANDO ÍNDICES OTIMIZADOS:")

            print("   ⏳ Criando índice users_company_idx...")
            await conn.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS users_company_idx
                ON master.users(company_id);
            """
                )
            )
            print("   ✅ Índice users_company_idx criado")

            print("   ⏳ Criando índice users_company_email_idx...")
            await conn.execute(
                text(
                    """
                CREATE INDEX IF NOT EXISTS users_company_email_idx
                ON master.users(company_id, email_address);
            """
                )
            )
            print("   ✅ Índice users_company_email_idx criado")

        else:
            print("\n2️⃣-8️⃣ COLUNA COMPANY_ID JÁ EXISTE, PULANDO ALTERAÇÕES...")

        # PASSO 9: VALIDAÇÕES FINAIS
        print("\n9️⃣ VALIDAÇÕES FINAIS:")

        # Verificar estrutura da tabela
        result = await conn.execute(
            text(
                """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'master'
            AND table_name = 'users'
            AND column_name IN ('company_id', 'email_address', 'person_id')
            ORDER BY ordinal_position;
        """
            )
        )

        columns = list(result)
        print("   📋 Estrutura das colunas:")
        for col in columns:
            print(
                f"      - {col.column_name}: {col.data_type} | NULL: {col.is_nullable} | Default: {col.column_default}"
            )

        # Verificar constraints
        result = await conn.execute(
            text(
                """
            SELECT conname, contype, pg_get_constraintdef(c.oid) as definition
            FROM pg_constraint c
            JOIN pg_class t ON c.conrelid = t.oid
            JOIN pg_namespace n ON t.relnamespace = n.oid
            WHERE n.nspname = 'master'
            AND t.relname = 'users'
            AND c.contype IN ('u', 'f')
            ORDER BY conname;
        """
            )
        )

        constraints = list(result)
        print("   📋 Constraints atuais:")
        for constraint in constraints:
            constraint_type = "UNIQUE" if constraint.contype == "u" else "FOREIGN KEY"
            print(
                f"      - {constraint.conname} ({constraint_type}): {constraint.definition}"
            )

        # Verificar índices
        result = await conn.execute(
            text(
                """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'master'
            AND tablename = 'users'
            AND indexname LIKE '%company%'
            ORDER BY indexname;
        """
            )
        )

        indexes = list(result)
        print("   📋 Índices company relacionados:")
        for idx in indexes:
            print(f"      - {idx.indexname}: {idx.indexdef}")

        # PASSO 10: RESUMO FINAL
        print("\n🔟 RESUMO DA ALTERAÇÃO:")

        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.users;
        """
            )
        )
        total_users = result.scalar()

        result = await conn.execute(
            text(
                """
            SELECT COUNT(DISTINCT company_id) FROM master.users;
        """
            )
        )
        distinct_companies = result.scalar()

        result = await conn.execute(
            text(
                """
            SELECT COUNT(*) FROM master.users WHERE company_id IS NULL;
        """
            )
        )
        users_without_company = result.scalar()

        print(f"   📊 Total de usuários: {total_users}")
        print(f"   📊 Companies distintas: {distinct_companies}")
        print(f"   📊 Usuários sem company_id: {users_without_company}")

        # Verificar se tudo foi implementado corretamente
        company_id_exists = any(col.column_name == "company_id" for col in columns)
        multi_tenant_constraint = any(
            "company_id" in constraint.definition
            and "email_address" in constraint.definition
            for constraint in constraints
        )
        old_unique_exists = any(
            constraint.definition == "UNIQUE (email_address)"
            for constraint in constraints
        )

        print(
            f"\n   ✅ Coluna company_id existe: {'SIM' if company_id_exists else 'NÃO'}"
        )
        print(
            f"   ✅ Constraint multi-tenant: {'SIM' if multi_tenant_constraint else 'NÃO'}"
        )
        print(
            f"   ✅ Constraint única antiga removida: {'SIM' if not old_unique_exists else 'NÃO'}"
        )
        print(
            f"   ✅ Dados populados: {'SIM' if users_without_company == 0 else 'NÃO'}"
        )

        if (
            company_id_exists
            and multi_tenant_constraint
            and not old_unique_exists
            and users_without_company == 0
        ):
            print("\n   🎉 FASE 2C CONCLUÍDA COM SUCESSO!")
            print("   ✅ Multi-tenancy implementado na tabela users")
            print("   🚀 PRONTO PARA VALIDAÇÃO FINAL DA FASE 2")
        else:
            print("\n   ⚠️  FASE 2C PARCIALMENTE CONCLUÍDA")
            print("   🔧 Algumas alterações podem precisar de ajustes")


async def main():
    """Função principal"""
    try:
        await alter_users_schema()
    except Exception as e:
        print(f"❌ Erro durante alteração: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
