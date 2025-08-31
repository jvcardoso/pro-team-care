from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import asyncio
from structlog import get_logger

logger = get_logger()

router = APIRouter()

class GeocodingRequest(BaseModel):
    address: str

class GeocodingResponse(BaseModel):
    latitude: float
    longitude: float
    formatted_address: str
    geocoding_accuracy: str
    geocoding_source: str
    api_data: Optional[Dict[Any, Any]] = None

class GeocodingService:
    def __init__(self):
        self.request_delay = 1.0  # Rate limiting para Nominatim (1s entre requests)
        self.last_request_time = 0.0
        
    async def respect_rate_limit(self):
        """Rate limiting para respeitar políticas da API"""
        import time
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            wait_time = self.request_delay - time_since_last
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def calculate_accuracy(self, nominatim_result: dict) -> str:
        """Calcular precisão baseada no tipo de lugar encontrado"""
        address = nominatim_result.get('address', {})
        
        # Precisão baseada no nível de detalhe do endereço
        if address.get('house_number'):
            return 'house'  # Mais preciso
        elif address.get('road'):
            return 'street'
        elif address.get('postcode'):
            return 'postal_code'
        elif address.get('suburb') or address.get('neighbourhood'):
            return 'sublocality'
        elif address.get('city') or address.get('town') or address.get('village'):
            return 'locality'
        elif address.get('state'):
            return 'administrative_area'
        
        return 'approximate'
    
    async def nominatim_geocode(self, address: str) -> dict:
        """Geocoding usando Nominatim (OpenStreetMap)"""
        await self.respect_rate_limit()
        
        params = {
            'format': 'json',
            'q': address,
            'addressdetails': '1',
            'limit': '1',
            'countrycodes': 'br',  # Restringir ao Brasil
            'accept-language': 'pt-BR,pt,en'
        }
        
        headers = {
            'User-Agent': 'ProTeamCare/1.0 (contato@proteamcare.com)'  # Identificação obrigatória
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    'https://nominatim.openstreetmap.org/search',
                    params=params,
                    headers=headers
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Nominatim API error: {response.status_code}"
                    )
                
                data = response.json()
                
                if not data:
                    raise HTTPException(
                        status_code=404,
                        detail="Endereço não encontrado"
                    )
                
                result = data[0]
                
                return {
                    'latitude': float(result['lat']),
                    'longitude': float(result['lon']),
                    'formatted_address': result['display_name'],
                    'geocoding_accuracy': self.calculate_accuracy(result),
                    'geocoding_source': 'nominatim',
                    'api_data': {
                        'nominatim': {
                            'place_id': result.get('place_id'),
                            'osm_type': result.get('osm_type'),
                            'osm_id': result.get('osm_id'),
                            'licence': result.get('licence'),
                            'boundingbox': result.get('boundingbox'),
                            'address_details': result.get('address')
                        }
                    }
                }
                
            except httpx.TimeoutException:
                logger.error("Timeout na consulta Nominatim", address=address)
                raise HTTPException(
                    status_code=408,
                    detail="Timeout na consulta de geocoding"
                )
            except httpx.RequestError as e:
                logger.error("Erro de rede no Nominatim", error=str(e), address=address)
                raise HTTPException(
                    status_code=503,
                    detail="Serviço de geocoding indisponível"
                )

# Instância do serviço
geocoding_service = GeocodingService()

@router.post("/geocode", response_model=GeocodingResponse)
async def geocode_address(request: GeocodingRequest):
    """
    Converter endereço em coordenadas geográficas usando OpenStreetMap/Nominatim
    
    - **address**: Endereço completo para geocoding
    
    Retorna latitude, longitude e dados adicionais de geolocalização.
    """
    try:
        logger.info("Iniciando geocoding", address=request.address)
        
        if not request.address or not request.address.strip():
            raise HTTPException(
                status_code=400,
                detail="Endereço não pode estar vazio"
            )
        
        result = await geocoding_service.nominatim_geocode(request.address.strip())
        
        logger.info(
            "Geocoding concluído com sucesso",
            address=request.address,
            latitude=result['latitude'],
            longitude=result['longitude'],
            accuracy=result['geocoding_accuracy']
        )
        
        return GeocodingResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erro inesperado no geocoding", error=str(e), address=request.address)
        raise HTTPException(
            status_code=500,
            detail="Erro interno no serviço de geocoding"
        )

@router.get("/health")
async def geocoding_health():
    """Health check do serviço de geocoding"""
    return {
        "status": "healthy",
        "service": "geocoding",
        "provider": "nominatim"
    }