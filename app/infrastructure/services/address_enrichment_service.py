"""
Serviço de enriquecimento de endereços
Integra com ViaCEP e serviço de geocoding para enriquecer endereços automaticamente
"""

import asyncio
from typing import Optional, Dict, Any
import httpx
from structlog import get_logger
from datetime import datetime

logger = get_logger()


class AddressEnrichmentService:
    """Serviço para enriquecimento automático de endereços"""
    
    def __init__(self):
        self.viacep_base_url = "https://viacep.com.br/ws"
        self.timeout = 10.0
        self.cache = {}  # Cache simples em memória
        
        # Mapeamento UF para código IBGE do estado
        self.ibge_state_codes = {
            'AC': 12, 'AL': 27, 'AP': 16, 'AM': 13, 'BA': 29, 'CE': 23,
            'DF': 53, 'ES': 32, 'GO': 52, 'MA': 21, 'MT': 51, 'MS': 50,
            'MG': 31, 'PA': 15, 'PB': 25, 'PR': 41, 'PE': 26, 'PI': 22,
            'RJ': 33, 'RN': 24, 'RS': 43, 'RO': 11, 'RR': 14, 'SC': 42,
            'SP': 35, 'SE': 28, 'TO': 17
        }

    async def consult_viacep(self, cep: str) -> Optional[Dict[str, Any]]:
        """Consulta ViaCEP para obter dados do CEP"""
        if not cep or len(cep.replace('-', '')) != 8:
            return None
            
        clean_cep = cep.replace('-', '')
        cache_key = f"viacep_{clean_cep}"
        
        # Verificar cache
        if cache_key in self.cache:
            logger.info("Using ViaCEP cache", cep=clean_cep)
            return self.cache[cache_key]
        
        try:
            logger.info("Consulting ViaCEP", cep=clean_cep)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.viacep_base_url}/{clean_cep}/json/")
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('erro'):
                    logger.warning("CEP not found in ViaCEP", cep=clean_cep)
                    return None
                
                # Cache resultado
                self.cache[cache_key] = data
                
                logger.info("ViaCEP consultation successful", cep=clean_cep, data=data)
                return data
                
        except Exception as error:
            logger.error("Error consulting ViaCEP", cep=clean_cep, error=str(error))
            return None

    async def geocode_address(self, full_address: str) -> Optional[Dict[str, Any]]:
        """Geocoding usando serviço interno"""
        try:
            logger.info("Starting geocoding", address=full_address)
            
            # Usar serviço interno de geocoding
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "http://localhost:8000/api/v1/geocoding/geocode",
                    json={"address": full_address}
                )
                
                if response.status_code == 200:
                    geo_data = response.json()
                    logger.info("Geocoding successful", latitude=geo_data.get('latitude'), longitude=geo_data.get('longitude'))
                    return geo_data
                else:
                    logger.warning("Geocoding failed", status=response.status_code)
                    return None
                    
        except Exception as error:
            logger.error("Error in geocoding", error=str(error))
            return None

    def get_ibge_state_code(self, uf: str) -> Optional[int]:
        """Retorna código IBGE do estado baseado na UF"""
        if not uf:
            return None
        return self.ibge_state_codes.get(uf.upper())

    async def enrich_address(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquece um endereço com dados do ViaCEP e geocoding
        
        Args:
            address_data: Dados básicos do endereço
            
        Returns:
            Dados do endereço enriquecidos
        """
        enriched_data = address_data.copy()
        
        # Verificar se já foi enriquecido
        if enriched_data.get('is_validated') and enriched_data.get('enrichment_source'):
            logger.info("Address already enriched, skipping", 
                       street=address_data.get('street'), 
                       enrichment_source=enriched_data.get('enrichment_source'))
            return enriched_data
        
        logger.info("Starting address enrichment", 
                   street=address_data.get('street'), 
                   zip_code=address_data.get('zip_code'))
        
        # 1. Enriquecimento com ViaCEP
        if address_data.get('zip_code'):
            viacep_data = await self.consult_viacep(address_data['zip_code'])
            
            if viacep_data:
                # Mesclar dados do ViaCEP - apenas enriquecer, não sobrescrever
                enriched_data.update({
                    'street': viacep_data.get('logradouro') or address_data.get('street', ''),
                    'neighborhood': viacep_data.get('bairro') or address_data.get('neighborhood', ''),
                    'city': viacep_data.get('localidade') or address_data.get('city', ''),
                    'state': viacep_data.get('uf') or address_data.get('state', ''),
                    'details': viacep_data.get('complemento') or address_data.get('details', ''),
                    
                    # Códigos oficiais do ViaCEP
                    'ibge_city_code': int(viacep_data['ibge']) if viacep_data.get('ibge') else address_data.get('ibge_city_code'),
                    'gia_code': viacep_data.get('gia') or address_data.get('gia_code'),
                    'siafi_code': viacep_data.get('siafi') or address_data.get('siafi_code'),
                    'area_code': viacep_data.get('ddd') or address_data.get('area_code'),
                    'ibge_state_code': self.get_ibge_state_code(viacep_data.get('uf')) or address_data.get('ibge_state_code'),
                    
                    # Metadados de enriquecimento
                    'enrichment_source': 'viacep',
                    'validation_source': 'viacep',
                    'is_validated': True,
                })
                
                logger.info("Address enriched with ViaCEP", 
                           ibge_city_code=enriched_data.get('ibge_city_code'),
                           gia_code=enriched_data.get('gia_code'))
        
        # 2. Geocoding
        if not enriched_data.get('latitude') or not enriched_data.get('longitude'):
            # Tentar múltiplas variações do endereço
            address_variations = [
                f"{enriched_data.get('street', '')}, {enriched_data.get('number', '')}, {enriched_data.get('neighborhood', '')}, {enriched_data.get('city', '')}, {enriched_data.get('state', '')}, Brasil",
                f"{enriched_data.get('street', '')}, {enriched_data.get('neighborhood', '')}, {enriched_data.get('city', '')}, {enriched_data.get('state', '')}, Brasil",
                f"{enriched_data.get('street', '')}, {enriched_data.get('city', '')}, {enriched_data.get('state', '')}, Brasil",
                f"{enriched_data.get('neighborhood', '')}, {enriched_data.get('city', '')}, {enriched_data.get('state', '')}, Brasil",
                f"{enriched_data.get('city', '')}, {enriched_data.get('state', '')}, Brasil"
            ]
            
            for address_variation in address_variations:
                # Limpar endereço (remover partes vazias)
                clean_address = ', '.join([part.strip() for part in address_variation.split(',') if part.strip()])
                
                if len(clean_address) > 10:  # Endereço mínimo válido
                    geo_data = await self.geocode_address(clean_address)
                    
                    if geo_data and geo_data.get('latitude') and geo_data.get('longitude'):
                        enriched_data.update({
                            'latitude': geo_data['latitude'],
                            'longitude': geo_data['longitude'],
                            'geocoding_accuracy': geo_data.get('geocoding_accuracy'),
                            'geocoding_source': geo_data.get('geocoding_source'),
                            'formatted_address': geo_data.get('formatted_address'),
                            'coordinates_source': 'nominatim'
                        })
                        
                        logger.info("Address geocoded successfully", 
                                   latitude=geo_data['latitude'], 
                                   longitude=geo_data['longitude'])
                        break
        
        logger.info("Address enrichment completed", 
                   enriched=bool(enriched_data.get('ibge_city_code')),
                   geocoded=bool(enriched_data.get('latitude')))
        
        return enriched_data

    async def enrich_multiple_addresses(self, addresses: list) -> list:
        """Enriquece múltiplos endereços em paralelo"""
        if not addresses:
            return addresses
        
        logger.info(f"Enriching {len(addresses)} addresses")
        
        # Processar endereços em paralelo
        tasks = [self.enrich_address(addr) for addr in addresses]
        enriched_addresses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar exceções e retornar resultados válidos
        result = []
        for i, addr in enumerate(enriched_addresses):
            if isinstance(addr, Exception):
                logger.error(f"Error enriching address {i}", error=str(addr))
                result.append(addresses[i])  # Retornar original em caso de erro
            else:
                result.append(addr)
        
        logger.info(f"Address enrichment completed for {len(result)} addresses")
        return result


# Instância singleton do serviço
address_enrichment_service = AddressEnrichmentService()