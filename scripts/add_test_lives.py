#!/usr/bin/env python3
"""
Script to add test contract lives for debugging purposes.
"""

import asyncio
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime

from sqlalchemy import select

from app.infrastructure.orm.database import get_db
from app.infrastructure.orm.models import Contract, ContractLive, People


async def add_test_lives():
    """Add test lives to contracts for debugging."""
    async for db in get_db():
        try:
            # Get first contract
            contract_query = select(Contract).limit(1)
            contract_result = await db.execute(contract_query)
            contract = contract_result.scalar_one_or_none()

            if not contract:
                print("❌ No contracts found. Create a contract first.")
                return

            print(f"📄 Using contract: {contract.contract_number} (ID: {contract.id})")

            # Get or create a test person
            person_query = select(People).where(People.name == "Pessoa Teste").limit(1)
            person_result = await db.execute(person_query)
            person = person_result.scalar_one_or_none()

            if not person:
                # Create test person
                person = People(
                    name="Pessoa Teste",
                    tax_id="12345678901",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.add(person)
                await db.commit()
                await db.refresh(person)
                print(f"👤 Created test person: {person.name} (ID: {person.id})")

            # Check if life already exists
            life_query = (
                select(ContractLive)
                .where(
                    ContractLive.contract_id == contract.id,
                    ContractLive.person_id == person.id,
                )
                .limit(1)
            )
            life_result = await db.execute(life_query)
            existing_life = life_result.scalar_one_or_none()

            if existing_life:
                print(f"✅ Test life already exists for contract {contract.id}")
                return

            # Create test life
            test_life = ContractLive(
                contract_id=contract.id,
                person_id=person.id,
                relationship_type="FUNCIONARIO",
                start_date=datetime.now().date(),
                status="active",
                substitution_reason="Vida de teste para debug",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            db.add(test_life)
            await db.commit()
            await db.refresh(test_life)

            print(
                f"✅ Added test life: {person.name} to contract {contract.contract_number}"
            )
            print(f"   Life ID: {test_life.id}")
            print(f"   Status: {test_life.status}")

        except Exception as e:
            print(f"❌ Error adding test life: {e}")
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(add_test_lives())
