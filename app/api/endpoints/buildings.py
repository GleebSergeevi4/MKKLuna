from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_api_key
from app.schemas import schemas
from app.crud import building as crud_building

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.Building],
    summary="Получить список всех зданий",
    description="Возвращает список всех зданий с пагинацией"
)
async def read_buildings(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Получить список всех зданий"""
    buildings = crud_building.get_buildings(db, skip=skip, limit=limit)
    return buildings


@router.get(
    "/{building_id}",
    response_model=schemas.Building,
    summary="Получить здание по ID",
    description="Возвращает информацию о здании по его идентификатору"
)
async def read_building(
    building_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Получить здание по ID"""
    building = crud_building.get_building(db, building_id=building_id)
    if building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Здание не найдено"
        )
    return building


@router.post(
    "/",
    response_model=schemas.Building,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новое здание",
    description="Создает новое здание в системе"
)
async def create_building(
    building: schemas.BuildingCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Создать новое здание"""
    return crud_building.create_building(db=db, building=building)


@router.put(
    "/{building_id}",
    response_model=schemas.Building,
    summary="Обновить здание",
    description="Обновляет информацию о здании"
)
async def update_building(
    building_id: int,
    building: schemas.BuildingUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Обновить здание"""
    db_building = crud_building.update_building(
        db=db,
        building_id=building_id,
        building=building
    )
    if db_building is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Здание не найдено"
        )
    return db_building


@router.delete(
    "/{building_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить здание",
    description="Удаляет здание из системы"
)
async def delete_building(
    building_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Удалить здание"""
    success = crud_building.delete_building(db=db, building_id=building_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Здание не найдено"
        )
    return None