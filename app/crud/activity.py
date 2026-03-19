from collections import deque
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import Activity
from app.schemas.schemas import ActivityCreate, ActivityUpdate
from app.core.config import settings


def get_activity(db: Session, activity_id: int) -> Optional[Activity]:
    """Получить вид деятельности по ID"""
    return db.query(Activity).filter(Activity.id == activity_id).first()


def get_activities(db: Session, skip: int = 0, limit: int = 100) -> List[Activity]:
    """Получить список видов деятельности"""
    return db.query(Activity).offset(skip).limit(limit).all()


def get_root_activities(db: Session) -> List[Activity]:
    """Получить корневые виды деятельности (уровень 1)"""
    return db.query(Activity).filter(Activity.parent_id.is_(None)).all()


def get_activity_children(db: Session, activity_id: int) -> List[Activity]:
    """Получить дочерние виды деятельности"""
    return db.query(Activity).filter(Activity.parent_id == activity_id).all()


def get_activity_descendants(db: Session, activity_id: int) -> List[Activity]:
    """
    Получить все вложенные виды деятельности (рекурсивно)
    """
    root = get_activity(db, activity_id)
    if not root:
        return []

    descendants: List[Activity] = []
    queue = deque([root])
    while queue:
        current = queue.popleft()
        descendants.append(current)
        queue.extend(get_activity_children(db, current.id))

    return descendants


def create_activity(db: Session, activity: ActivityCreate) -> Activity:
    """Создать новый вид деятельности"""
    # Определяем уровень вложенности
    level = 1
    if activity.parent_id is not None:
        parent = get_activity(db, activity.parent_id)
        if parent is None:
            raise ValueError("Родительский вид деятельности не найден")
        level = parent.level + 1
        if level > settings.MAX_ACTIVITY_DEPTH:
            raise ValueError(
                f"Превышен максимальный уровень вложенности ({settings.MAX_ACTIVITY_DEPTH})"
            )
    
    db_activity = Activity(
        name=activity.name,
        parent_id=activity.parent_id,
        level=level
    )
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity


def update_activity(db: Session, activity_id: int, activity: ActivityUpdate) -> Optional[Activity]:
    """Обновить вид деятельности"""
    db_activity = get_activity(db, activity_id)
    if db_activity is None:
        return None
    
    update_data = activity.model_dump(exclude_unset=True)
    
    # Если обновляется parent_id, пересчитываем уровень
    if "parent_id" in update_data:
        new_parent_id = update_data["parent_id"]
        if new_parent_id is not None:
            parent = get_activity(db, new_parent_id)
            if parent is None:
                raise ValueError("Родительский вид деятельности не найден")
            
            # Проверяем, не создаст ли это циклическую ссылку
            if new_parent_id == activity_id:
                raise ValueError("Вид деятельности не может быть родителем самого себя")
            
            # Проверяем уровень вложенности
            new_level = parent.level + 1
            if new_level > settings.MAX_ACTIVITY_DEPTH:
                raise ValueError(
                    f"Превышен максимальный уровень вложенности ({settings.MAX_ACTIVITY_DEPTH})"
                )
            
            db_activity.level = new_level
        else:
            db_activity.level = 1
    
    # Обновляем остальные поля
    for field, value in update_data.items():
        if field != "parent_id" or value is not None:
            setattr(db_activity, field, value)

    # Обновляем уровни всех дочерних элементов до commit,
    # чтобы применить изменения одной транзакцией.
    _update_children_levels(db, db_activity)
    
    db.commit()
    db.refresh(db_activity)

    return db_activity


def _update_children_levels(db: Session, activity: Activity):
    """Рекурсивно обновить уровни всех дочерних элементов"""
    children = get_activity_children(db, activity.id)
    for child in children:
        child.level = activity.level + 1
        _update_children_levels(db, child)


def delete_activity(db: Session, activity_id: int) -> bool:
    """Удалить вид деятельности"""
    db_activity = get_activity(db, activity_id)
    if db_activity is None:
        return False
    
    db.delete(db_activity)
    db.commit()
    return True


def search_activities_by_name(db: Session, name: str) -> List[Activity]:
    """Поиск видов деятельности по названию"""
    return db.query(Activity).filter(Activity.name.ilike(f"%{name}%")).all()