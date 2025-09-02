"""
External Service Interfaces - Contratos para serviços externos
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class CNPJServiceInterface(ABC):
    """Interface para consulta de CNPJ"""
    
    @abstractmethod
    async def consult_cnpj(self, cnpj: str) -> Optional[Dict[str, Any]]:
        """Consultar CNPJ na Receita Federal"""
        pass


class GeoCodingServiceInterface(ABC):
    """Interface para geocoding"""
    
    @abstractmethod
    async def geocode_address(self, address: str) -> Optional[Dict[str, Any]]:
        """Converter endereço em coordenadas"""
        pass
    
    @abstractmethod
    async def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """Converter coordenadas em endereço"""
        pass


class ViaCEPServiceInterface(ABC):
    """Interface para consulta ViaCEP"""
    
    @abstractmethod
    async def consult_cep(self, cep: str) -> Optional[Dict[str, Any]]:
        """Consultar CEP no ViaCEP"""
        pass