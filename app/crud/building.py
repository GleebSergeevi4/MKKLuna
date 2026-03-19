from math import asin, cos, radians, sin, sqrt
from typing import List, Optional, cast

from sqlalchemy.orm import Session

from app.models.models import Building
from app.schemas.schemas import BuildingCreate, BuildingUpdate


EARTH_RADIUS_METERS = 6_371_000


def _haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Вычислить расстояние между двумя координатами в метрах."""
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    hav = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    return 2 * asin(sqrt(hav)) * EARTH_RADIUS_METERS


def get_building(db: Session, building_id: int) -> Optional[Building]:
    """Получить здание по ID"""
    return db.query(Building).filter(Building.id == building_id).first()


def get_buildings(db: Session, skip: int = 0, limit: int = 100) -> List[Building]:
    """Получить список зданий"""
    return db.query(Building).offset(skip).limit(limit).all()


def create_building(db: Session, building: BuildingCreate) -> Building:
    """Создать новое здание"""
    db_building = Building(**building.model_dump())
    db.add(db_building)
    db.commit()
    db.refresh(db_building)
    return db_building


def update_building(db: Session, building_id: int, building: BuildingUpdate) -> Optional[Building]:
    """Обновить здание"""
    db_building = get_building(db, building_id)
    if db_building is None:
        return None
    
    update_data = building.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_building, field, value)
    
    db.commit()
    db.refresh(db_building)
    return db_building


def delete_building(db: Session, building_id: int) -> bool:
    """Удалить здание"""
    db_building = get_building(db, building_id)
    if db_building is None:
        return False
    
    db.delete(db_building)
    db.commit()
    return True


def get_buildings_in_area(
    db: Session,
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float
) -> List[Building]:
    """Получить список зданий в прямоугольной области"""
    return db.query(Building).filter(
        Building.latitude >= min_lat,
        Building.latitude <= max_lat,
        Building.longitude >= min_lon,
        Building.longitude <= max_lon
    ).all()


def get_buildings_in_radius(
    db: Session,
    latitude: float,
    longitude: float,
    radius_meters: float
) -> List[Building]:
    """Получить список зданий в радиусе от точки."""
    all_buildings = db.query(Building).all()
    return [
        building
        for building in all_buildings
        if _haversine_distance_meters(  # type: ignore[arg-type]
            latitude,
            longitude,
            cast(float, building.latitude),
            cast(float, building.longitude),
        ) <= radius_meters
    ]