"""
Конфигурация pytest и общие фикстуры для тестов.
"""
import pytest
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.models.models import Building, Activity, Organization


# Используем тестовую базу данных SQLite
TEST_DATABASE_URL = "sqlite:///./test.db"

# Создаем движок для тестовой БД
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Фикстура для создания тестовой сессии базы данных.
    Создает таблицы перед тестом и удаляет после.
    """
    # Создаем таблицы
    Base.metadata.create_all(bind=test_engine)
    
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Удаляем таблицы после теста
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Фикстура для создания тестового клиента FastAPI.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def api_headers() -> dict:
    """
    Фикстура с заголовками для API запросов (включая API ключ).
    """
    return {
        "X-API-Key": settings.API_KEY,
        "Content-Type": "application/json"
    }


@pytest.fixture
def sample_building(db_session: Session) -> Building:
    """
    Фикстура для создания тестового здания.
    """
    building = Building(
        address="г. Москва, ул. Тестовая 1",
        latitude=55.7558,
        longitude=37.6173
    )
    db_session.add(building)
    db_session.commit()
    db_session.refresh(building)
    return building


@pytest.fixture
def sample_buildings(db_session: Session) -> list[Building]:
    """
    Фикстура для создания нескольких тестовых зданий.
    """
    buildings = [
        Building(address="г. Москва, ул. Ленина 1", latitude=55.7558, longitude=37.6173),
        Building(address="г. Москва, ул. Пушкина 2", latitude=55.7512, longitude=37.6184),
        Building(address="г. Санкт-Петербург, Невский пр. 1", latitude=59.9343, longitude=30.3351),
    ]
    for building in buildings:
        db_session.add(building)
    db_session.commit()
    for building in buildings:
        db_session.refresh(building)
    return buildings


@pytest.fixture
def sample_activity(db_session: Session) -> Activity:
    """
    Фикстура для создания тестового вида деятельности.
    """
    activity = Activity(
        name="Тестовая деятельность",
        level=1
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    return activity


@pytest.fixture
def sample_activity_tree(db_session: Session) -> dict:
    """
    Фикстура для создания дерева видов деятельности.
    """
    # Уровень 1
    food = Activity(name="Еда", level=1)
    db_session.add(food)
    db_session.commit()
    db_session.refresh(food)
    
    # Уровень 2
    meat = Activity(name="Мясная продукция", parent_id=food.id, level=2)
    dairy = Activity(name="Молочная продукция", parent_id=food.id, level=2)
    db_session.add(meat)
    db_session.add(dairy)
    db_session.commit()
    db_session.refresh(meat)
    db_session.refresh(dairy)
    
    return {
        "root": food,
        "children": [meat, dairy]
    }


@pytest.fixture
def sample_organization(db_session: Session, sample_building: Building, sample_activity: Activity) -> Organization:
    """
    Фикстура для создания тестовой организации.
    """
    organization = Organization(
        name="ООО Тестовая компания",
        phone_numbers="8-800-555-35-35, 2-222-222",
        building_id=sample_building.id
    )
    organization.activities = [sample_activity]
    db_session.add(organization)
    db_session.commit()
    db_session.refresh(organization)
    return organization


@pytest.fixture
def sample_organizations(db_session: Session, sample_buildings: list[Building], sample_activity_tree: dict) -> list[Organization]:
    """
    Фикстура для создания нескольких тестовых организаций.
    """
    food = sample_activity_tree["root"]
    meat, dairy = sample_activity_tree["children"]
    
    organizations = [
        Organization(
            name="ООО Рога и Копыта",
            phone_numbers="2-222-222",
            building_id=sample_buildings[0].id
        ),
        Organization(
            name="ИП Мясной Двор",
            phone_numbers="8-800-555-35-35",
            building_id=sample_buildings[1].id
        ),
        Organization(
            name="ООО Молочная Ферма",
            phone_numbers="8-495-123-45-67",
            building_id=sample_buildings[0].id
        ),
    ]
    
    organizations[0].activities = [meat, dairy]
    organizations[1].activities = [meat]
    organizations[2].activities = [dairy]
    
    for org in organizations:
        db_session.add(org)
    db_session.commit()
    
    for org in organizations:
        db_session.refresh(org)
    
    return organizations