#!/usr/bin/env python3
"""
Script para debug da estrutura do banco de dados
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_DATABASE')}"

async def main():
    engine = create_async_engine(DATABASE_URL)

    async with engine.begin() as conn:
        # 1. Testar conexão básica
        print("=== TESTE DE CONEXÃO ===")
        try:
            result = await conn.execute(text("SELECT version();"))
            version = result.fetchone()
            print(f"✅ Conexão OK - PostgreSQL: {version[0]}")
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            return

        # 2. Verificar tabelas relacionadas a establishments
        print("\n=== TABELAS RELACIONADAS A ESTABLISHMENTS ===")
        result = await conn.execute(text("""
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = 'master'
            AND (table_name LIKE '%establishment%' OR table_name = 'people' OR table_name = 'companies')
            ORDER BY table_name;
        """))

        tables = result.fetchall()
        for row in tables:
            print(f"- {row[0]} ({row[1]})")

        # 3. Verificar estrutura da tabela establishments
        print("\n=== ESTRUTURA DA TABELA ESTABLISHMENTS ===")
        try:
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'master'
                AND table_name = 'establishments'
                ORDER BY ordinal_position;
            """))

            for row in result.fetchall():
                print(f"- {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")

        except Exception as e:
            print(f"❌ Erro ao verificar estrutura: {e}")

        # 4. Verificar funções PostgreSQL customizadas
        print("\n=== FUNÇÕES POSTGRESQL CUSTOMIZADAS ===")
        try:
            result = await conn.execute(text("""
                SELECT routine_name, routine_type
                FROM information_schema.routines
                WHERE routine_schema = 'master'
                AND routine_name LIKE '%establishment%'
                ORDER BY routine_name;
            """))

            functions = result.fetchall()
            if functions:
                for row in functions:
                    print(f"- {row[0]} ({row[1]})")
            else:
                print("Nenhuma função encontrada")

        except Exception as e:
            print(f"❌ Erro ao verificar funções: {e}")

        # 5. Testar query básica de establishments
        print("\n=== TESTE DA QUERY DE ESTABLISHMENTS ===")
        try:
            result = await conn.execute(text("""
                SELECT COUNT(*) as total
                FROM master.establishments e
                WHERE e.deleted_at IS NULL;
            """))

            row = result.fetchone()
            print(f"✅ Query básica OK - Total de establishments: {row[0]}")

        except Exception as e:
            print(f"❌ Erro na query básica: {e}")

        # 6. Testar query com JOIN (similar ao código)
        print("\n=== TESTE DA QUERY COM JOIN ===")
        try:
            result = await conn.execute(text("""
                SELECT e.id, e.code, p.name as establishment_name, c.id as company_id
                FROM master.establishments e
                LEFT JOIN master.people p ON e.person_id = p.id
                LEFT JOIN master.companies c ON e.company_id = c.id
                WHERE e.deleted_at IS NULL
                LIMIT 5;
            """))

            rows = result.fetchall()
            print(f"✅ Query com JOIN OK - {len(rows)} registros retornados")
            for row in rows:
                print(f"  ID: {row[0]}, Code: {row[1]}, Name: {row[2]}, Company: {row[3]}")

        except Exception as e:
            print(f"❌ Erro na query com JOIN: {e}")

        # 7. Verificar se há dados nas tabelas relacionadas
        print("\n=== VERIFICAÇÃO DE DADOS ===")
        try:
            # People
            result = await conn.execute(text("SELECT COUNT(*) FROM master.people;"))
            people_count = result.fetchone()[0]
            print(f"People: {people_count} registros")

            # Companies
            result = await conn.execute(text("SELECT COUNT(*) FROM master.companies;"))
            companies_count = result.fetchone()[0]
            print(f"Companies: {companies_count} registros")

            # Establishments
            result = await conn.execute(text("SELECT COUNT(*) FROM master.establishments WHERE deleted_at IS NULL;"))
            establishments_count = result.fetchone()[0]
            print(f"Establishments ativos: {establishments_count} registros")

        except Exception as e:
            print(f"❌ Erro ao verificar dados: {e}")

if __name__ == "__main__":
    asyncio.run(main())