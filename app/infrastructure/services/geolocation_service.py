"""
Geolocation Service - Integração com Functions PostgreSQL de Geolocalização
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import structlog
from sqlalchemy import text

logger = structlog.get_logger()


@dataclass
class AddressDistance:
    """Resultado de busca de endereços por distância"""

    id: int
    full_address: str
    distance_km: float
    latitude: Optional[float]
    longitude: Optional[float]
    quality_score: Optional[int]


@dataclass
class CoverageStats:
    """Estatísticas de área de cobertura"""

    total_addresses: int
    within_coverage: int
    coverage_percentage: float
    avg_distance: float
    max_distance: float


class GeolocationService:
    """
    Serviço de geolocalização que integra com functions PostgreSQL
    Implementa busca por raio, cálculo de distâncias e análise de cobertura
    """

    def __init__(self, session):
        self.session = session

    async def find_addresses_within_radius(
        self, center_lat: float, center_lng: float, radius_km: float, limit: int = 50
    ) -> List[AddressDistance]:
        """
        Busca endereços dentro de um raio específico
        Function: fn_find_addresses_within_radius
        """
        try:
            query = text(
                """
                SELECT * FROM master.fn_find_addresses_within_radius(
                    :center_lat, :center_lng, :radius_km
                )
                LIMIT :limit
            """
            )

            result = await self.session.execute(
                query,
                {
                    "center_lat": center_lat,
                    "center_lng": center_lng,
                    "radius_km": radius_km,
                    "limit": limit,
                },
            )

            addresses = []
            for row in result.fetchall():
                addresses.append(
                    AddressDistance(
                        id=row.id,
                        full_address=row.full_address,
                        distance_km=float(row.distance_km or 0),
                        latitude=float(row.latitude) if row.latitude else None,
                        longitude=float(row.longitude) if row.longitude else None,
                        quality_score=row.quality_score,
                    )
                )

            await logger.ainfo(
                "addresses_within_radius_found",
                center_lat=center_lat,
                center_lng=center_lng,
                radius_km=radius_km,
                count=len(addresses),
            )

            return addresses

        except Exception as e:
            await logger.aerror(
                "addresses_within_radius_failed",
                center_lat=center_lat,
                center_lng=center_lng,
                radius_km=radius_km,
                error=str(e),
            )
            return []

    async def find_closest_address(
        self, target_lat: float, target_lng: float, limit: int = 5
    ) -> List[AddressDistance]:
        """
        Encontra os endereços mais próximos de um ponto
        Function: fn_find_closest_address
        """
        try:
            query = text(
                """
                SELECT * FROM master.fn_find_closest_address(
                    :target_lat, :target_lng, :limit
                )
            """
            )

            result = await self.session.execute(
                query,
                {"target_lat": target_lat, "target_lng": target_lng, "limit": limit},
            )

            addresses = []
            for row in result.fetchall():
                addresses.append(
                    AddressDistance(
                        id=row.id,
                        full_address=row.full_address,
                        distance_km=float(row.distance_km or 0),
                        latitude=float(row.latitude) if row.latitude else None,
                        longitude=float(row.longitude) if row.longitude else None,
                        quality_score=row.quality_score,
                    )
                )

            await logger.ainfo(
                "closest_addresses_found",
                target_lat=target_lat,
                target_lng=target_lng,
                count=len(addresses),
            )

            return addresses

        except Exception as e:
            await logger.aerror(
                "closest_addresses_failed",
                target_lat=target_lat,
                target_lng=target_lng,
                error=str(e),
            )
            return []

    async def find_nearby_addresses(
        self, reference_address_id: int, radius_km: float = 5.0, limit: int = 20
    ) -> List[AddressDistance]:
        """
        Busca endereços próximos a um endereço de referência
        Function: fn_find_nearby_addresses
        """
        try:
            query = text(
                """
                SELECT * FROM master.fn_find_nearby_addresses(
                    :reference_id, :radius_km
                )
                LIMIT :limit
            """
            )

            result = await self.session.execute(
                query,
                {
                    "reference_id": reference_address_id,
                    "radius_km": radius_km,
                    "limit": limit,
                },
            )

            addresses = []
            for row in result.fetchall():
                addresses.append(
                    AddressDistance(
                        id=row.id,
                        full_address=row.full_address,
                        distance_km=float(row.distance_km or 0),
                        latitude=float(row.latitude) if row.latitude else None,
                        longitude=float(row.longitude) if row.longitude else None,
                        quality_score=row.quality_score,
                    )
                )

            await logger.ainfo(
                "nearby_addresses_found",
                reference_id=reference_address_id,
                radius_km=radius_km,
                count=len(addresses),
            )

            return addresses

        except Exception as e:
            await logger.aerror(
                "nearby_addresses_failed",
                reference_id=reference_address_id,
                radius_km=radius_km,
                error=str(e),
            )
            return []

    async def calculate_distance_between_addresses(
        self, address_id_1: int, address_id_2: int
    ) -> Optional[float]:
        """
        Calcula distância entre dois endereços
        Function: fn_calculate_distance_between_addresses
        """
        try:
            query = text(
                """
                SELECT master.fn_calculate_distance_between_addresses(
                    :address_id_1, :address_id_2
                )
            """
            )

            result = await self.session.execute(
                query, {"address_id_1": address_id_1, "address_id_2": address_id_2}
            )

            distance = result.scalar()
            distance_km = float(distance) if distance else None

            await logger.ainfo(
                "distance_calculated",
                address_id_1=address_id_1,
                address_id_2=address_id_2,
                distance_km=distance_km,
            )

            return distance_km

        except Exception as e:
            await logger.aerror(
                "distance_calculation_failed",
                address_id_1=address_id_1,
                address_id_2=address_id_2,
                error=str(e),
            )
            return None

    async def get_coverage_area_stats(
        self, center_lat: float, center_lng: float, coverage_radius_km: float
    ) -> Optional[CoverageStats]:
        """
        Obtém estatísticas de área de cobertura
        Function: fn_coverage_area_stats
        """
        try:
            query = text(
                """
                SELECT * FROM master.fn_coverage_area_stats(
                    :center_lat, :center_lng, :coverage_radius_km
                )
            """
            )

            result = await self.session.execute(
                query,
                {
                    "center_lat": center_lat,
                    "center_lng": center_lng,
                    "coverage_radius_km": coverage_radius_km,
                },
            )

            row = result.fetchone()

            if row:
                stats = CoverageStats(
                    total_addresses=row.total_addresses or 0,
                    within_coverage=row.within_coverage or 0,
                    coverage_percentage=float(row.coverage_percentage or 0),
                    avg_distance=float(row.avg_distance or 0),
                    max_distance=float(row.max_distance or 0),
                )

                await logger.ainfo(
                    "coverage_stats_calculated",
                    center_lat=center_lat,
                    center_lng=center_lng,
                    coverage_radius_km=coverage_radius_km,
                    total_addresses=stats.total_addresses,
                    within_coverage=stats.within_coverage,
                    coverage_percentage=stats.coverage_percentage,
                )

                return stats

            return None

        except Exception as e:
            await logger.aerror(
                "coverage_stats_failed",
                center_lat=center_lat,
                center_lng=center_lng,
                coverage_radius_km=coverage_radius_km,
                error=str(e),
            )
            return None

    async def batch_geocode_addresses(
        self, address_ids: List[int]
    ) -> Dict[int, Tuple[Optional[float], Optional[float]]]:
        """
        Busca coordenadas em lote para múltiplos endereços
        """
        try:
            from sqlalchemy import select

            from app.infrastructure.orm.models import Address

            query = select(Address.id, Address.latitude, Address.longitude).where(
                Address.id.in_(address_ids)
            )

            result = await self.session.execute(query)

            coordinates = {}
            for row in result.fetchall():
                lat = float(row.latitude) if row.latitude else None
                lng = float(row.longitude) if row.longitude else None
                coordinates[row.id] = (lat, lng)

            await logger.ainfo(
                "batch_geocode_completed",
                requested_ids=len(address_ids),
                found_coordinates=len(coordinates),
            )

            return coordinates

        except Exception as e:
            await logger.aerror(
                "batch_geocode_failed", address_ids_count=len(address_ids), error=str(e)
            )
            return {}

    async def get_addresses_needing_geocoding(
        self, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Busca endereços que precisam ser geocodificados
        """
        try:
            from sqlalchemy import select

            from app.infrastructure.orm.models import Address

            query = (
                select(
                    Address.id,
                    Address.street,
                    Address.number,
                    Address.neighborhood,
                    Address.city,
                    Address.state,
                    Address.zip_code,
                )
                .where(
                    Address.latitude.is_(None),
                    Address.longitude.is_(None),
                    Address.deleted_at.is_(None),
                )
                .limit(limit)
            )

            result = await self.session.execute(query)

            addresses = []
            for row in result.fetchall():
                addresses.append(
                    {
                        "id": row.id,
                        "full_address": f"{row.street}, {row.number}, {row.neighborhood}, {row.city}, {row.state}, {row.zip_code}",
                        "street": row.street,
                        "number": row.number,
                        "neighborhood": row.neighborhood,
                        "city": row.city,
                        "state": row.state,
                        "zip_code": row.zip_code,
                    }
                )

            await logger.ainfo(
                "addresses_needing_geocoding", count=len(addresses), limit=limit
            )

            return addresses

        except Exception as e:
            await logger.aerror(
                "get_addresses_needing_geocoding_failed", limit=limit, error=str(e)
            )
            return []


# Função de conveniência para dependency injection
async def get_geolocation_service(db) -> GeolocationService:
    """Factory function for GeolocationService"""
    return GeolocationService(db)
