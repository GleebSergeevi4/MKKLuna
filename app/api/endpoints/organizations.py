from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_api_key
from app.schemas import schemas
from app.crud import organization as crud_organization

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.OrganizationList],
    summary="Получить список всех организаций",
    description="Возвращает список всех организаций с пагинацией"
)
async def read_organizations(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Получить список всех организаций"""
    organizations = crud_organization.get_organizations(db, skip=skip, limit=limit)
    return organizations


@router.get(
    "/{organization_id}",
    response_model=schemas.Organization,
    summary="Получить организацию по ID",
    description="Возвращает информацию об организации по её идентификатору"
)
async def read_organization(
    organization_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Получить организацию по ID"""
    organization = crud_organization.get_organization(db, organization_id=organization_id)
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Организация не найдена"
        )
    return organization


@router.post(
    "/",
    response_model=schemas.Organization,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую организацию",
    description="Создает новую организацию в системе"
)
async def create_organization(
    organization: schemas.OrganizationCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Создать новую организацию"""
    try:
        return crud_organization.create_organization(db=db, organization=organization)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{organization_id}",
    response_model=schemas.Organization,
    summary="Обновить организацию",
    description="Обновляет информацию об организации"
)
async def update_organization(
    organization_id: int,
    organization: schemas.OrganizationUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Обновить организацию"""
    try:
        db_organization = crud_organization.update_organization(
            db=db,
            organization_id=organization_id,
            organization=organization
        )
        if db_organization is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Организация не найдена"
            )
        return db_organization
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить организацию",
    description="Удаляет организацию из системы"
)
async def delete_organization(
    organization_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Удалить организацию"""
    success = crud_organization.delete_organization(db=db, organization_id=organization_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Организация не найдена"
        )
    return None


@router.get(
    "/building/{building_id}",
    response_model=List[schemas.OrganizationList],
    summary="Получить организации в здании",
    description="Возвращает список всех организаций, находящихся в конкретном здании"
)
async def read_organizations_by_building(
    building_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Получить все организации в конкретном здании"""
    organizations = crud_organization.get_organizations_by_building(db, building_id=building_id)
    return organizations


@router.get(
    "/activity/{activity_id}",
    response_model=List[schemas.OrganizationList],
    summary="Получить организации по виду деятельности",
    description="Возвращает список всех организаций с указанным видом деятельности. "
                "Параметр include_descendants позволяет включить организации со всеми вложенными видами деятельности"
)
async def read_organizations_by_activity(
    activity_id: int,
    include_descendants: bool = Query(
        True,
        description="Включить организации со всеми вложенными видами деятельности"
    ),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Получить все организации с указанным видом деятельности"""
    organizations = crud_organization.get_organizations_by_activity(
        db,
        activity_id=activity_id,
        include_descendants=include_descendants
    )
    return organizations


@router.post(
    "/search/location",
    response_model=List[schemas.OrganizationList],
    summary="Поиск организаций по местоположению",
    description="Поиск организаций в радиусе или прямоугольной области относительно указанной точки. "
                "Укажите либо radius (радиус в метрах), либо координаты прямоугольной области "
                "(min_latitude, max_latitude, min_longitude, max_longitude)"
)
async def search_organizations_by_location(
    location: schemas.LocationSearch,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Поиск организаций по местоположению"""
    if location.radius is not None:
        # Поиск в радиусе
        organizations = crud_organization.get_organizations_by_location_radius(
            db,
            latitude=location.latitude,
            longitude=location.longitude,
            radius_meters=location.radius
        )
    else:
        # Поиск в прямоугольной области
        organizations = crud_organization.get_organizations_by_location_area(
            db,
            min_lat=location.min_latitude,
            max_lat=location.max_latitude,
            min_lon=location.min_longitude,
            max_lon=location.max_longitude
        )
    
    return organizations


@router.get(
    "/search/name",
    response_model=List[schemas.OrganizationList],
    summary="Поиск организаций по названию",
    description="Поиск организаций по части названия (регистронезависимый)"
)
async def search_organizations_by_name(
    name: str = Query(..., min_length=1, description="Название или часть названия организации"),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Поиск организаций по названию"""
    organizations = crud_organization.search_organizations_by_name(db, name=name)
    return organizations