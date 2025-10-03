#!/usr/bin/env python3
"""
Script para criar empresas de home care no banco de desenvolvimento
Cria 10 empresas com dados realistas para testes
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import async_session
from app.infrastructure.repositories.company_repository import CompanyRepository
from app.presentation.schemas.company import (
    AddressCreate,
    CompanyBase,
    CompanyCreate,
    EmailCreate,
    PeopleCreate,
    PhoneCreate,
    PhoneType,
    EmailType,
    AddressType,
    PersonStatus,
    PersonType,
)
from config.settings import settings


# Dados das empresas de home care
COMPANIES_DATA = [
    {
        "cnpj": "97267511461006",
        "name": "Home Care Vida Plena LTDA",
        "trade_name": "Home Care Vida Plena",
        "city": "São Paulo",
        "state": "SP",
        "zip_code": "01234-567",
        "street": "Rua da Saúde",
        "number": "123",
        "neighborhood": "Centro",
    },
    {
        "cnpj": "88521150466042",
        "name": "Assistência Domiciliar Total LTDA",
        "trade_name": "Assistência Domiciliar Total",
        "city": "Rio de Janeiro",
        "state": "RJ",
        "zip_code": "20000-000",
        "street": "Avenida Atlântica",
        "number": "456",
        "neighborhood": "Copacabana",
    },
    {
        "cnpj": "19964416689814",
        "name": "Cuidar Home Care LTDA",
        "trade_name": "Cuidar Home Care",
        "city": "Belo Horizonte",
        "state": "MG",
        "zip_code": "30100-000",
        "street": "Rua da Bahia",
        "number": "789",
        "neighborhood": "Centro",
    },
    {
        "cnpj": "57509983631286",
        "name": "Vida em Casa Assistência LTDA",
        "trade_name": "Vida em Casa",
        "city": "Porto Alegre",
        "state": "RS",
        "zip_code": "90000-000",
        "street": "Rua dos Andradas",
        "number": "101",
        "neighborhood": "Centro Histórico",
    },
    {
        "cnpj": "96765049423099",
        "name": "Home Care Bem Estar LTDA",
        "trade_name": "Home Care Bem Estar",
        "city": "Salvador",
        "state": "BA",
        "zip_code": "40000-000",
        "street": "Rua Chile",
        "number": "234",
        "neighborhood": "Centro",
    },
    {
        "cnpj": "15359820374815",
        "name": "Assistência Médica Domiciliar LTDA",
        "trade_name": "Assistência Médica Domiciliar",
        "city": "Brasília",
        "state": "DF",
        "zip_code": "70000-000",
        "street": "SGAS 905",
        "number": "567",
        "neighborhood": "Asa Sul",
    },
    {
        "cnpj": "64768938934026",
        "name": "Home Care São Paulo LTDA",
        "trade_name": "Home Care São Paulo",
        "city": "São Paulo",
        "state": "SP",
        "zip_code": "04567-890",
        "street": "Alameda Santos",
        "number": "890",
        "neighborhood": "Jardins",
    },
    {
        "cnpj": "45487877332190",
        "name": "Cuidados Especiais Home LTDA",
        "trade_name": "Cuidados Especiais Home",
        "city": "Curitiba",
        "state": "PR",
        "zip_code": "80000-000",
        "street": "Rua XV de Novembro",
        "number": "111",
        "neighborhood": "Centro",
    },
    {
        "cnpj": "64942732129704",
        "name": "Vida Ativa Home Care LTDA",
        "trade_name": "Vida Ativa Home Care",
        "city": "Recife",
        "state": "PE",
        "zip_code": "50000-000",
        "street": "Rua do Bom Jesus",
        "number": "222",
        "neighborhood": "Boa Vista",
    },
    {
        "cnpj": "68953590220577",
        "name": "Home Care Familiar LTDA",
        "trade_name": "Home Care Familiar",
        "city": "Fortaleza",
        "state": "CE",
        "zip_code": "60000-000",
        "street": "Avenida Monsenhor Tabosa",
        "number": "333",
        "neighborhood": "Centro",
    },
]


def generate_phone_numbers(base_number: str) -> List[PhoneCreate]:
    """Gera números de telefone realistas baseados no CNPJ"""
    # Gera números brasileiros realistas
    ddd_options = ["11", "21", "31", "41", "51", "61", "71", "81", "91"]
    ddd = ddd_options[int(base_number[-2:]) % len(ddd_options)]

    phones = [
        PhoneCreate(
            number=f"{ddd}9{base_number[-8:-4]}{base_number[-4:]}",
            type=PhoneType.COMMERCIAL,
            is_principal=True,
            is_active=True,
            is_whatsapp=True,
            accepts_whatsapp_marketing=True,
            accepts_whatsapp_notifications=True,
            contact_priority=1,
            can_receive_calls=True,
            can_receive_sms=True,
            extension=None,
            phone_name=None,
            whatsapp_name=None,
            carrier=None,
        ),
        PhoneCreate(
            number=f"{ddd}{base_number[-8:-4]}{base_number[-4:]}",
            type=PhoneType.LANDLINE,
            is_principal=False,
            is_active=True,
            contact_priority=2,
            can_receive_calls=True,
            can_receive_sms=False,
            extension=None,
            phone_name=None,
            whatsapp_name=None,
            carrier=None,
        ),
    ]
    return phones


def generate_emails(company_name: str) -> List[EmailCreate]:
    """Gera emails realistas baseados no nome da empresa"""
    # Limpa o nome da empresa para criar email
    clean_name = (
        company_name.lower()
        .replace(" ", "")
        .replace("ç", "c")
        .replace("ã", "a")
        .replace("õ", "o")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("á", "a")
        .replace("é", "e")
        .replace("ltda", "")
        .replace("home", "")
        .replace("care", "")
        .strip()
    )

    emails = [
        EmailCreate(
            email_address=f"contato@{clean_name}homecare.com.br",
            type=EmailType.WORK,
            is_principal=True,
        ),
        EmailCreate(
            email_address=f"admin@{clean_name}homecare.com.br",
            type=EmailType.WORK,
            is_principal=False,
        ),
    ]
    return emails


def generate_address(company_data: dict) -> List[AddressCreate]:
    """Gera endereço realista"""
    return [
        AddressCreate(
            street=company_data["street"],
            number=company_data["number"],
            details=None,
            neighborhood=company_data["neighborhood"],
            city=company_data["city"],
            state=company_data["state"],
            zip_code=company_data["zip_code"],
            country="BR",
            type=AddressType.COMMERCIAL,
            is_principal=True,
        )
    ]


async def create_company(db: AsyncSession, company_data: dict) -> None:
    """Cria uma empresa no banco de dados"""
    try:
        # Cria o repositório
        repo = CompanyRepository(db)

        # Gera dados realistas
        phones = generate_phone_numbers(company_data["cnpj"])
        emails = generate_emails(company_data["name"])
        addresses = generate_address(company_data)

        # Cria o objeto CompanyCreate
        company_create = CompanyCreate(
            people=PeopleCreate(
                person_type=PersonType.PJ,
                name=company_data["name"],
                trade_name=company_data["trade_name"],
                tax_id=company_data["cnpj"],
                status=PersonStatus.ACTIVE,
                description=f"Empresa especializada em cuidados domiciliares em {company_data['city']}",
                secondary_tax_id=None,
                tax_regime=None,
                legal_nature=None,
                municipal_registration=None,
            ),
            company=CompanyBase(),
            phones=phones,
            emails=emails,
            addresses=addresses,
        )

        # Cria a empresa
        result = await repo.create_company(company_create)

        print(f"✅ Empresa criada: {result.people.name}")
        print(f"   CNPJ: {result.people.tax_id}")
        print(f"   Telefones: {len(result.phones)}")
        print(f"   Emails: {len(result.emails)}")
        print(f"   Endereços: {len(result.addresses)}")
        print()

    except Exception as e:
        print(f"❌ Erro ao criar empresa {company_data['name']}: {e}")
        raise


async def main():
    """Função principal"""
    print("🚀 Iniciando criação de empresas de home care...")
    print(f"📊 Serão criadas {len(COMPANIES_DATA)} empresas")
    print()

    async with async_session() as db:
        for i, company_data in enumerate(COMPANIES_DATA, 1):
            print(f"[{i}/{len(COMPANIES_DATA)}] Criando empresa...")
            await create_company(db, company_data)

    print("🎉 Todas as empresas foram criadas com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())