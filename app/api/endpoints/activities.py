from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_api_key
from app.schemas import schemas
from app.crud import activity as crud_activity

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.Activity],
    summary="Получить список всех видов деятельности",
    description="Возвращает список всех видов деятельности с пагинацией"
)
async def read_activities(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Получить список всех видов деятельности"""
    activities = crud_activity.get_activities(db, skip=skip, limit=limit)
    return activities


@router.get(
    "/tree",
    response_model=List[schemas.ActivityTree],
    summary="Получить дерево видов деятельности",
    description="Возвращает иерархическое дерево всех видов деятельности"
)
async def read_activity_tree(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Получить дерево видов деятельности"""
    root_activities = crud_activity.get_root_activities(db)
    
    def build_tree(activity):
        """Рекурсивно строим дерево"""
        children = crud_activity.get_activity_children(db, activity.id)
        return schemas.ActivityTree(
            id=activity.id,
            name=activity.name,
            parent_id=activity.parent_id,
            level=activity.level,
            children=[build_tree(child) for child in children]
        )
    
    return [build_tree(activity) for activity in root_activities]


@router.get(
    "/{activity_id}",
    response_model=schemas.Activity,
    summary="Получить вид деятельности по ID",
    description="Возвращает информацию о виде деятельности по его идентификатору"
)
async def read_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Получить вид деятельности по ID"""
    activity = crud_activity.get_activity(db, activity_id=activity_id)
    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вид деятельности не найден"
        )
    return activity


@router.get(
    "/{activity_id}/children",
    response_model=List[schemas.Activity],
    summary="Получить дочерние виды деятельности",
    description="Возвращает список непосредственных дочерних видов деятельности"
)
async def read_activity_children(
    activity_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Получить дочерние виды деятельности"""
    activity = crud_activity.get_activity(db, activity_id=activity_id)
    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вид деятельности не найден"
        )
    
    children = crud_activity.get_activity_children(db, activity_id=activity_id)
    return children


@router.get(
    "/{activity_id}/descendants",
    response_model=List[schemas.Activity],
    summary="Получить все вложенные виды деятельности",
    description="Возвращает список всех вложенных видов деятельности (рекурсивно)"
)
async def read_activity_descendants(
    activity_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Получить все вложенные виды деятельности"""
    activity = crud_activity.get_activity(db, activity_id=activity_id)
    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вид деятельности не найден"
        )
    
    descendants = crud_activity.get_activity_descendants(db, activity_id=activity_id)
    return descendants


@router.post(
    "/",
    response_model=schemas.Activity,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый вид деятельности",
    description="Создает новый вид деятельности в системе. "
                "Уровень вложенности ограничен 3 уровнями"
)
async def create_activity(
    activity: schemas.ActivityCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Создать новый вид деятельности"""
    try:
        return crud_activity.create_activity(db=db, activity=activity)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{activity_id}",
    response_model=schemas.Activity,
    summary="Обновить вид деятельности",
    description="Обновляет информацию о виде деятельности"
)
async def update_activity(
    activity_id: int,
    activity: schemas.ActivityUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Обновить вид деятельности"""
    try:
        db_activity = crud_activity.update_activity(
            db=db,
            activity_id=activity_id,
            activity=activity
        )
        if db_activity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Вид деятельности не найден"
            )
        return db_activity
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить вид деятельности",
    description="Удаляет вид деятельности из системы"
)
async def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Удалить вид деятельности"""
    success = crud_activity.delete_activity(db=db, activity_id=activity_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вид деятельности не найден"
        )
    return None


@router.get(
    "/search/name",
    response_model=List[schemas.Activity],
    summary="Поиск видов деятельности по названию",
    description="Поиск видов деятельности по части названия (регистронезависимый)"
)
async def search_activities_by_name(
    name: str = Query(..., min_length=1, description="Название или часть названия вида деятельности"),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """Поиск видов деятельности по названию"""
    activities = crud_activity.search_activities_by_name(db, name=name)
    return activities