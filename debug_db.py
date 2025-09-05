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

DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

async def main():
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        # 1. Encontrar tabelas relacionadas a menu
        print("=== TABELAS RELACIONADAS A MENU ===")
        result = await conn.execute(text("""
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'master' 
            AND (table_name LIKE '%menu%' OR table_name LIKE '%permission%')
            ORDER BY table_name;
        """))
        
        for row in result.fetchall():
            print(f"- {row[0]} ({row[1]})")
        
        # 2. Verificar estrutura da tabela menu (se existir)
        print("\n=== ESTRUTURA DA TABELA MENU ===")
        try:
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = 'master' 
                AND table_name = 'menu'
                ORDER BY ordinal_position;
            """))
            
            for row in result.fetchall():
                print(f"- {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")
                
        except Exception as e:
            print(f"Erro: {e}")
            
        # 3. Verificar dados básicos do usuário ID 1
        print("\n=== USUÁRIO ID 1 ===")
        try:
            result = await conn.execute(text("""
                SELECT id, email, name, person_type, is_system_admin
                FROM master.users 
                WHERE id = 1;
            """))
            
            row = result.fetchone()
            if row:
                print(f"ID: {row[0]}, Email: {row[1]}, Nome: {row[2]}, Tipo: {row[3]}, Admin: {row[4]}")
            else:
                print("Usuário ID 1 não encontrado")
                
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    asyncio.run(main())