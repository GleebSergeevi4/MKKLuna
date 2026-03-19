from typing import Iterable, List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models.models import Organization, Activity, Building
from app.schemas.schemas import OrganizationCreate, OrganizationUpdate
from app.crud.building import get_buildings_in_radius, get_buildings_in_area
from app.crud.activity import get_activity_descendants


def _organizations_query(db: Session):
    return db.query(Organization).options(
        joinedload(Organization.building),
        joinedload(Organization.activities)
    )


def _serialize_phones(phone_numbers: Iterable[str]) -> str:
    return ", ".join(phone_numbers)


def _validate_building(db: Session, building_id: int) -> None:
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise ValueError("Здание не найдено")


def _fetch_activities_or_error(db: Session, activity_ids: List[int]) -> List[Activity]:
    activities = db.query(Activity).filter(Activity.id.in_(activity_ids)).all()
    if len(activities) != len(activity_ids):
        raise ValueError("Один или несколько видов деятельности не найдены")
    return activities


def get_organization(db: Session, organization_id: int) -> Optional[Organization]:
    """Получить организацию по ID с загруженными связями"""
    return _organizations_query(db).filter(Organization.id == organization_id).first()


def get_organizations(db: Session, skip: int = 0, limit: int = 100) -> List[Organization]:
    """Получить список организаций"""
    return _organizations_query(db).offset(skip).limit(limit).all()


def create_organization(db: Session, organization: OrganizationCreate) -> Organization:
    """Создать новую организацию"""
    _validate_building(db, organization.building_id)
    activities = _fetch_activities_or_error(db, organization.activity_ids)
    
    # Создаем организацию
    db_organization = Organization(
        name=organization.name,
        phone_numbers=_serialize_phones(organization.phone_numbers),
        building_id=organization.building_id
    )
    
    # Добавляем виды деятельности
    db_organization.activities = activities
    
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)
    
    return get_organization(db, db_organization.id)


def update_organization(
    db: Session,
    organization_id: int,
    organization: OrganizationUpdate
) -> Optional[Organization]:
    """Обновить организацию"""
    db_organization = get_organization(db, organization_id)
    if db_organization is None:
        return None
    
    update_data = organization.model_dump(exclude_unset=True)
    
    # Обновляем виды деятельности, если указаны
    if "activity_ids" in update_data:
        activity_ids = update_data.pop("activity_ids")
        activities = _fetch_activities_or_error(db, activity_ids)
        db_organization.activities = activities
    
    # Обновляем номера телефонов, если указаны
    if "phone_numbers" in update_data:
        phone_numbers = update_data.pop("phone_numbers")
        db_organization.phone_numbers = _serialize_phones(phone_numbers)
    
    # Проверяем здание, если обновляется
    if "building_id" in update_data:
        _validate_building(db, update_data["building_id"])
    
    # Обновляем остальные поля
    for field, value in update_data.items():
        setattr(db_organization, field, value)
    
    db.commit()
    db.refresh(db_organization)
    return get_organization(db, organization_id)


def delete_organization(db: Session, organization_id: int) -> bool:
    """Удалить организацию"""
    db_organization = get_organization(db, organization_id)
    if db_organization is None:
        return False
    
    db.delete(db_organization)
    db.commit()
    return True


def get_organizations_by_building(db: Session, building_id: int) -> List[Organization]:
    """Получить все организации в конкретном здании"""
    return _organizations_query(db).filter(Organization.building_id == building_id).all()


def get_organizations_by_activity(
    db: Session,
    activity_id: int,
    include_descendants: bool = False
) -> List[Organization]:
    """
    Получить все организации с указанным видом деятельности.
    Если include_descendants=True, включает организации со всеми дочерними видами деятельности.
    """
    organization_query = _organizations_query(db).join(Organization.activities)
    if include_descendants:
        descendants = get_activity_descendants(db, activity_id)
        activity_ids = [activity.id for activity in descendants]
        return organization_query.filter(Activity.id.in_(activity_ids)).distinct().all()

    return organization_query.filter(Activity.id == activity_id).all()


def get_organizations_by_location_radius(
    db: Session,
    latitude: float,
    longitude: float,
    radius_meters: float
) -> List[Organization]:
    """Получить организации в радиусе от точки"""
    buildings = get_buildings_in_radius(db, latitude, longitude, radius_meters)
    building_ids = [building.id for building in buildings]

    if not building_ids:
        return []

    return _organizations_query(db).filter(Organization.building_id.in_(building_ids)).all()


def get_organizations_by_location_area(
    db: Session,
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float
) -> List[Organization]:
    """Получить организации в прямоугольной области"""
    buildings = get_buildings_in_area(db, min_lat, max_lat, min_lon, max_lon)
    building_ids = [building.id for building in buildings]

    if not building_ids:
        return []

    return _organizations_query(db).filter(Organization.building_id.in_(building_ids)).all()


def search_organizations_by_name(db: Session, name: str) -> List[Organization]:
    """Поиск организаций по названию"""
    return _organizations_query(db).filter(Organization.name.ilike(f"%{name}%")).all()