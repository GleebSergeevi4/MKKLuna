"""
Скрипт для заполнения базы данных тестовыми данными.
"""
import sys
from typing import Dict, List

sys.path.append('.')

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.base import Base
from app.models.models import Building, Activity, Organization


def init_db():
    """Создание таблиц в базе данных"""
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы")


def populate_buildings(db: Session):
    """Заполнение таблицы зданий"""
    buildings_data = [
        {"address": "г. Москва, ул. Ленина 1, офис 3", "latitude": 55.7558, "longitude": 37.6173},
        {"address": "г. Москва, ул. Блюхера 32/1", "latitude": 55.7512, "longitude": 37.6184},
        {"address": "г. Санкт-Петербург, Невский проспект 28", "latitude": 59.9343, "longitude": 30.3351},
        {"address": "г. Новосибирск, ул. Красный проспект 1", "latitude": 55.0084, "longitude": 82.9357},
        {"address": "г. Екатеринбург, ул. Вайнера 9", "latitude": 56.8389, "longitude": 60.6057},
        {"address": "г. Казань, ул. Баумана 58", "latitude": 55.7887, "longitude": 49.1221},
    ]
    
    buildings = []
    for data in buildings_data:
        building = Building(**data)
        db.add(building)
        buildings.append(building)
    
    db.commit()
    print(f"Добавлено {len(buildings)} зданий")
    return buildings


def populate_activities(db: Session):
    """Заполнение таблицы видов деятельности"""
    level_1_names = ["Еда", "Автомобили", "Услуги"]
    level_1_map: Dict[str, Activity] = {}
    for name in level_1_names:
        activity = Activity(name=name, level=1)
        db.add(activity)
        db.flush()
        level_1_map[name] = activity

    level_2_data = [
        ("Мясная продукция", "Еда", 2),
        ("Молочная продукция", "Еда", 2),
        ("Хлебобулочные изделия", "Еда", 2),
        ("Грузовые", "Автомобили", 2),
        ("Легковые", "Автомобили", 2),
        ("Консалтинг", "Услуги", 2),
        ("Клининг", "Услуги", 2),
    ]
    level_2_map: Dict[str, Activity] = {}
    for name, parent_name, level in level_2_data:
        activity = Activity(name=name, parent_id=level_1_map[parent_name].id, level=level)
        db.add(activity)
        db.flush()
        level_2_map[name] = activity

    level_3_data = [
        ("Запчасти", "Легковые", 3),
        ("Аксессуары", "Легковые", 3),
    ]
    for name, parent_name, level in level_3_data:
        db.add(Activity(name=name, parent_id=level_2_map[parent_name].id, level=level))

    db.commit()
    
    print("Добавлено дерево видов деятельности")
    
    # Возвращаем все виды деятельности
    activities = db.query(Activity).all()
    return activities


def populate_organizations(db: Session, buildings, activities):
    """Заполнение таблицы организаций"""
    activity_by_name = {activity.name: activity for activity in activities}
    
    organizations_data = [
        {
            "name": 'ООО "Рога и Копыта"',
            "phone_numbers": "2-222-222, 3-333-333, 8-923-666-13-13",
            "building": buildings[0],
            "activities": [activity_by_name["Мясная продукция"], activity_by_name["Молочная продукция"]]
        },
        {
            "name": 'ИП "Мясной Двор"',
            "phone_numbers": "8-800-555-35-35, 2-111-111",
            "building": buildings[1],
            "activities": [activity_by_name["Мясная продукция"]]
        },
        {
            "name": 'ООО "Молочная Ферма"',
            "phone_numbers": "8-495-123-45-67",
            "building": buildings[0],
            "activities": [activity_by_name["Молочная продукция"]]
        },
        {
            "name": 'АО "АвтоМир"',
            "phone_numbers": "8-812-777-88-99, 8-812-777-88-00",
            "building": buildings[2],
            "activities": [
                activity_by_name["Автомобили"],
                activity_by_name["Запчасти"],
                activity_by_name["Аксессуары"],
            ]
        },
        {
            "name": 'ООО "ЗапчастиПлюс"',
            "phone_numbers": "8-383-456-78-90",
            "building": buildings[3],
            "activities": [activity_by_name["Запчасти"]]
        },
        {
            "name": 'ИП "АвтоАксессуары"',
            "phone_numbers": "8-343-987-65-43",
            "building": buildings[4],
            "activities": [activity_by_name["Аксессуары"]]
        },
        {
            "name": 'ООО "БизнесКонсалт"',
            "phone_numbers": "8-843-111-22-33, 8-843-111-22-34",
            "building": buildings[5],
            "activities": [activity_by_name["Консалтинг"]]
        },
        {
            "name": 'ООО "ЧистоПро"',
            "phone_numbers": "8-495-000-11-22",
            "building": buildings[1],
            "activities": [activity_by_name["Клининг"]]
        },
        {
            "name": 'ООО "ЕдаИАвто"',
            "phone_numbers": "8-800-100-20-30",
            "building": buildings[2],
            "activities": [activity_by_name["Еда"], activity_by_name["Автомобили"]]
        },
        {
            "name": 'ИП "Продукты и Услуги"',
            "phone_numbers": "8-900-123-45-67, 8-900-123-45-68",
            "building": buildings[3],
            "activities": [activity_by_name["Молочная продукция"], activity_by_name["Консалтинг"]]
        },
    ]
    
    organizations = []
    for data in organizations_data:
        org = Organization(
            name=data["name"],
            phone_numbers=data["phone_numbers"],
            building_id=data["building"].id
        )
        org.activities = data["activities"]
        db.add(org)
        organizations.append(org)
    
    db.commit()
    print(f"Добавлено {len(organizations)} организаций")
    return organizations


def main():
    """Главная функция для заполнения базы данных"""
    print("Начало заполнения базы данных тестовыми данными...\n")
    
    # Создаем таблицы
    init_db()
    
    # Создаем сессию
    db = SessionLocal()
    
    try:
        # Заполняем данными
        buildings = populate_buildings(db)
        activities = populate_activities(db)
        organizations = populate_organizations(db, buildings, activities)
        
        print("\nБаза данных успешно заполнена тестовыми данными!")
        print(f"  - Зданий: {len(buildings)}")
        print(f"  - Видов деятельности: {len(activities)}")
        print(f"  - Организаций: {len(organizations)}")
        
    except Exception as e:
        print(f"\nОшибка при заполнении базы данных: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()