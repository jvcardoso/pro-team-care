import asyncio

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Importe os modelos e a sessão do seu projeto
# Os caminhos podem precisar de ajuste fino dependendo da estrutura exata
from app.infrastructure.database import async_session
from app.infrastructure.orm.models import Address, Company, People

COMPANY_ID_TO_AUDIT = 42


async def audit_address_data():
    """
    Busca os dados da empresa e seus endereços para auditoria.
    """
    print(f"--- Iniciando auditoria para a Empresa ID: {COMPANY_ID_TO_AUDIT} ---")

    async with async_session() as session:
        # Prepara a query para buscar a empresa e carregar seus endereços relacionados
        stmt = (
            select(Company)
            .where(Company.id == COMPANY_ID_TO_AUDIT)
            .options(selectinload(Company.people).selectinload(People.addresses))
        )

        result = await session.execute(stmt)
        company = result.scalar_one_or_none()

        if not company:
            print(f"ERRO: Empresa com ID {COMPANY_ID_TO_AUDIT} não encontrada.")
            return

        print(
            f"\nEmpresa encontrada: {company.people.trade_name or company.people.name} (CNPJ: {company.people.tax_id})"
        )

        if not company.people.addresses:
            print("AVISO: A empresa não possui endereços cadastrados.")
            return

        print("\n--- Endereços Encontrados ---")
        for i, addr in enumerate(company.people.addresses, 1):
            print(f"\n[ Endereço #{i} ]")
            print(f"  - CEP: {addr.zip_code}")
            print(f"  - Logradouro: {addr.street}")
            print(f"  - Número: {addr.number}")
            print(f"  - Bairro: {addr.neighborhood}")
            print(f"  - Cidade: {addr.city}")
            print(f"  - Estado: {addr.state}")
            print("-" * 20)
            print("  VERIFICAÇÃO DE ENRIQUECIMENTO:")

            # Verificar geolocalização
            if addr.latitude and addr.longitude:
                print(
                    f"  ✅ Geolocalização: Latitude={addr.latitude}, Longitude={addr.longitude}"
                )
            else:
                print("  ❌ Geolocalização: DADOS AUSENTES")

            # Verificar dados do ViaCEP
            viacep_fields = []
            if addr.ibge_city_code:
                viacep_fields.append(f"IBGE: {addr.ibge_city_code}")
            if addr.gia_code:
                viacep_fields.append(f"GIA: {addr.gia_code}")
            if addr.siafi_code:
                viacep_fields.append(f"SIAFI: {addr.siafi_code}")
            if addr.area_code:
                viacep_fields.append(f"DDD: {addr.area_code}")

            if viacep_fields:
                print(f"  ✅ ViaCEP: {', '.join(viacep_fields)}")
            else:
                print("  ❌ ViaCEP: DADOS AUSENTES")

            # Verificar outras informações de enriquecimento
            if addr.geocoding_source:
                print(f"  ✅ Fonte de geocoding: {addr.geocoding_source}")
            if addr.enrichment_source:
                print(f"  ✅ Fonte de enriquecimento: {addr.enrichment_source}")
            if addr.is_validated:
                print("  ✅ Endereço validado")
            else:
                print("  ❌ Endereço não validado")

        print("\n--- Auditoria Concluída ---")


if __name__ == "__main__":
    asyncio.run(audit_address_data())
