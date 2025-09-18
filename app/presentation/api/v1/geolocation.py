from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from structlog import get_logger

from app.infrastructure.database import get_db
from app.infrastructure.services.geolocation_service import (
    GeolocationService,
    get_geolocation_service,
)
from app.presentation.decorators.simple_permissions import require_permission
from app.presentation.schemas.user_schemas import UserCompleteResponse

router = APIRouter()
logger = get_logger()


async def get_current_user_schema(db=Depends(get_db)):
    """Get current user with complete data"""
    from sqlalchemy import select

    from app.infrastructure.auth import get_current_user as get_current_basic
    from app.infrastructure.orm.views import UserCompleteView

    user = await get_current_basic(db)

    query = select(UserCompleteView).where(UserCompleteView.user_id == user.id)
    result = await db.execute(query)
    user_complete = result.scalars().first()

    if not user_complete:
        raise HTTPException(status_code=404, detail="User data not found")

    return UserCompleteResponse.from_attributes(user_complete)


class AddressDistanceResponse(BaseModel):
    """Response model for address with distance"""

    id: int
    full_address: str
    distance_km: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    quality_score: Optional[int] = None


class CoverageStatsResponse(BaseModel):
    """Response model for coverage statistics"""

    total_addresses: int
    within_coverage: int
    coverage_percentage: float
    avg_distance: float
    max_distance: float


class CoordinatesPair(BaseModel):
    """Coordinates pair response"""

    latitude: Optional[float]
    longitude: Optional[float]


@router.get("/addresses/within-radius", response_model=List[AddressDistanceResponse])
@require_permission("geolocation.search")
async def find_addresses_within_radius(
    center_lat: float = Query(..., description="Latitude do centro"),
    center_lng: float = Query(..., description="Longitude do centro"),
    radius_km: float = Query(..., ge=0.1, le=50, description="Raio em quilômetros"),
    limit: int = Query(50, ge=1, le=100, description="Limite de resultados"),
    geo_service: GeolocationService = Depends(get_geolocation_service),
    current_user=Depends(get_current_user_schema),
):
    """Buscar endereços dentro de um raio específico"""
    try:
        addresses = await geo_service.find_addresses_within_radius(
            center_lat=center_lat,
            center_lng=center_lng,
            radius_km=radius_km,
            limit=limit,
        )

        await logger.ainfo(
            "addresses_within_radius_searched",
            center_lat=center_lat,
            center_lng=center_lng,
            radius_km=radius_km,
            found_count=len(addresses),
            requested_by=current_user.user_id,
        )

        return [
            AddressDistanceResponse(
                id=addr.id,
                full_address=addr.full_address,
                distance_km=addr.distance_km,
                latitude=addr.latitude,
                longitude=addr.longitude,
                quality_score=addr.quality_score,
            )
            for addr in addresses
        ]

    except Exception as e:
        await logger.aerror("addresses_within_radius_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/addresses/closest", response_model=List[AddressDistanceResponse])
@require_permission("geolocation.search")
async def find_closest_addresses(
    target_lat: float = Query(..., description="Latitude do ponto de referência"),
    target_lng: float = Query(..., description="Longitude do ponto de referência"),
    limit: int = Query(5, ge=1, le=20, description="Número de endereços mais próximos"),
    geo_service: GeolocationService = Depends(get_geolocation_service),
    current_user=Depends(get_current_user_schema),
):
    """Encontrar os endereços mais próximos de um ponto"""
    try:
        addresses = await geo_service.find_closest_address(
            target_lat=target_lat, target_lng=target_lng, limit=limit
        )

        await logger.ainfo(
            "closest_addresses_searched",
            target_lat=target_lat,
            target_lng=target_lng,
            limit=limit,
            found_count=len(addresses),
            requested_by=current_user.user_id,
        )

        return [
            AddressDistanceResponse(
                id=addr.id,
                full_address=addr.full_address,
                distance_km=addr.distance_km,
                latitude=addr.latitude,
                longitude=addr.longitude,
                quality_score=addr.quality_score,
            )
            for addr in addresses
        ]

    except Exception as e:
        await logger.aerror("closest_addresses_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get(
    "/addresses/{address_id}/nearby", response_model=List[AddressDistanceResponse]
)
@require_permission("geolocation.search")
async def find_nearby_addresses(
    address_id: int,
    radius_km: float = Query(5.0, ge=0.1, le=20, description="Raio de busca em km"),
    limit: int = Query(20, ge=1, le=50, description="Limite de resultados"),
    geo_service: GeolocationService = Depends(get_geolocation_service),
    current_user=Depends(get_current_user_schema),
):
    """Buscar endereços próximos a um endereço de referência"""
    try:
        addresses = await geo_service.find_nearby_addresses(
            reference_address_id=address_id, radius_km=radius_km, limit=limit
        )

        await logger.ainfo(
            "nearby_addresses_searched",
            reference_address_id=address_id,
            radius_km=radius_km,
            found_count=len(addresses),
            requested_by=current_user.user_id,
        )

        return [
            AddressDistanceResponse(
                id=addr.id,
                full_address=addr.full_address,
                distance_km=addr.distance_km,
                latitude=addr.latitude,
                longitude=addr.longitude,
                quality_score=addr.quality_score,
            )
            for addr in addresses
        ]

    except Exception as e:
        await logger.aerror("nearby_addresses_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/distance/{address_id_1}/{address_id_2}")
@require_permission("geolocation.calculate")
async def calculate_distance(
    address_id_1: int,
    address_id_2: int,
    geo_service: GeolocationService = Depends(get_geolocation_service),
    current_user=Depends(get_current_user_schema),
):
    """Calcular distância entre dois endereços"""
    try:
        distance = await geo_service.calculate_distance_between_addresses(
            address_id_1=address_id_1, address_id_2=address_id_2
        )

        if distance is None:
            raise HTTPException(
                status_code=404, detail="Não foi possível calcular a distância"
            )

        await logger.ainfo(
            "distance_calculated_api",
            address_id_1=address_id_1,
            address_id_2=address_id_2,
            distance_km=distance,
            requested_by=current_user.user_id,
        )

        return {
            "address_id_1": address_id_1,
            "address_id_2": address_id_2,
            "distance_km": distance,
        }

    except HTTPException:
        raise
    except Exception as e:
        await logger.aerror("distance_calculation_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/coverage-stats", response_model=CoverageStatsResponse)
@require_permission("geolocation.analyze")
async def get_coverage_stats(
    center_lat: float = Query(..., description="Latitude do centro da área"),
    center_lng: float = Query(..., description="Longitude do centro da área"),
    coverage_radius_km: float = Query(
        ..., ge=1, le=100, description="Raio de cobertura em km"
    ),
    geo_service: GeolocationService = Depends(get_geolocation_service),
    current_user=Depends(get_current_user_schema),
):
    """Obter estatísticas de cobertura de uma área"""
    try:
        stats = await geo_service.get_coverage_area_stats(
            center_lat=center_lat,
            center_lng=center_lng,
            coverage_radius_km=coverage_radius_km,
        )

        if not stats:
            raise HTTPException(
                status_code=404, detail="Não foi possível obter estatísticas"
            )

        await logger.ainfo(
            "coverage_stats_retrieved",
            center_lat=center_lat,
            center_lng=center_lng,
            coverage_radius_km=coverage_radius_km,
            total_addresses=stats.total_addresses,
            requested_by=current_user.user_id,
        )

        return CoverageStatsResponse(
            total_addresses=stats.total_addresses,
            within_coverage=stats.within_coverage,
            coverage_percentage=stats.coverage_percentage,
            avg_distance=stats.avg_distance,
            max_distance=stats.max_distance,
        )

    except HTTPException:
        raise
    except Exception as e:
        await logger.aerror("coverage_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/addresses/coordinates")
@require_permission("geolocation.view")
async def batch_get_coordinates(
    address_ids: str = Query(
        ..., description="IDs dos endereços separados por vírgula"
    ),
    geo_service: GeolocationService = Depends(get_geolocation_service),
    current_user=Depends(get_current_user_schema),
):
    """Obter coordenadas de múltiplos endereços"""
    try:
        # Parse address IDs
        try:
            ids = [int(id.strip()) for id in address_ids.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="IDs de endereços inválidos")

        coordinates = await geo_service.batch_geocode_addresses(address_ids=ids)

        result = {}
        for address_id, (lat, lng) in coordinates.items():
            result[str(address_id)] = CoordinatesPair(latitude=lat, longitude=lng)

        await logger.ainfo(
            "batch_coordinates_retrieved",
            requested_addresses=len(ids),
            found_coordinates=len(coordinates),
            requested_by=current_user.user_id,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        await logger.aerror("batch_coordinates_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")


@router.get("/addresses/needs-geocoding")
@require_permission("geolocation.manage")
async def get_addresses_needing_geocoding(
    limit: int = Query(100, ge=1, le=500, description="Limite de endereços"),
    geo_service: GeolocationService = Depends(get_geolocation_service),
    current_user=Depends(get_current_user_schema),
):
    """Listar endereços que precisam ser geocodificados"""
    try:
        addresses = await geo_service.get_addresses_needing_geocoding(limit=limit)

        await logger.ainfo(
            "addresses_needing_geocoding_retrieved",
            count=len(addresses),
            limit=limit,
            requested_by=current_user.user_id,
        )

        return {"addresses": addresses, "count": len(addresses), "limit": limit}

    except Exception as e:
        await logger.aerror("addresses_needing_geocoding_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno do servidor")
