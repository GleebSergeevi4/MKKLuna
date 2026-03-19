"""
Unit тесты для CRUD операций со зданиями.
"""
import pytest
from sqlalchemy.orm import Session

from app.crud import building as crud_building
from app.schemas.schemas import BuildingCreate, BuildingUpdate
from app.models.models import Building


@pytest.mark.unit
class TestBuildingCRUD:
    """Тесты для CRUD операций со зданиями"""
    
    def test_create_building(self, db_session: Session):
        """Тест создания здания"""
        building_data = BuildingCreate(
            address="г. Москва, ул. Новая 123",
            latitude=55.7558,
            longitude=37.6173
        )
        
        building = crud_building.create_building(db_session, building_data)
        
        assert building.id is not None
        assert building.address == "г. Москва, ул. Новая 123"
        assert building.latitude == 55.7558
        assert building.longitude == 37.6173
    
    def test_get_building(self, db_session: Session, sample_building: Building):
        """Тест получения здания по ID"""
        building = crud_building.get_building(db_session, sample_building.id)
        
        assert building is not None
        assert building.id == sample_building.id
        assert building.address == sample_building.address
    
    def test_get_building_not_found(self, db_session: Session):
        """Тест получения несуществующего здания"""
        building = crud_building.get_building(db_session, 999)
        
        assert building is None
    
    def test_get_buildings(self, db_session: Session, sample_buildings: list[Building]):
        """Тест получения списка зданий"""
        buildings = crud_building.get_buildings(db_session, skip=0, limit=10)
        
        assert len(buildings) == 3
        assert all(isinstance(b, Building) for b in buildings)
    
    def test_get_buildings_pagination(self, db_session: Session, sample_buildings: list[Building]):
        """Тест пагинации списка зданий"""
        # Пропускаем первое здание
        buildings = crud_building.get_buildings(db_session, skip=1, limit=2)
        
        assert len(buildings) == 2
        assert buildings[0].id == sample_buildings[1].id
    
    def test_update_building(self, db_session: Session, sample_building: Building):
        """Тест обновления здания"""
        update_data = BuildingUpdate(
            address="г. Москва, ул. Обновленная 456",
            latitude=55.8558,
            longitude=37.7173
        )
        
        updated_building = crud_building.update_building(
            db_session,
            sample_building.id,
            update_data
        )
        
        assert updated_building is not None
        assert updated_building.id == sample_building.id
        assert updated_building.address == "г. Москва, ул. Обновленная 456"
        assert updated_building.latitude == 55.8558
        assert updated_building.longitude == 37.7173
    
    def test_update_building_partial(self, db_session: Session, sample_building: Building):
        """Тест частичного обновления здания"""
        original_lat = sample_building.latitude
        original_lon = sample_building.longitude
        
        update_data = BuildingUpdate(address="Новый адрес")
        
        updated_building = crud_building.update_building(
            db_session,
            sample_building.id,
            update_data
        )
        
        assert updated_building.address == "Новый адрес"
        assert updated_building.latitude == original_lat  # Не изменилась
        assert updated_building.longitude == original_lon  # Не изменилась
    
    def test_update_building_not_found(self, db_session: Session):
        """Тест обновления несуществующего здания"""
        update_data = BuildingUpdate(address="Тест")
        
        result = crud_building.update_building(db_session, 999, update_data)
        
        assert result is None
    
    def test_delete_building(self, db_session: Session, sample_building: Building):
        """Тест удаления здания"""
        building_id = sample_building.id
        
        result = crud_building.delete_building(db_session, building_id)
        
        assert result is True
        
        # Проверяем, что здание действительно удалено
        deleted_building = crud_building.get_building(db_session, building_id)
        assert deleted_building is None
    
    def test_delete_building_not_found(self, db_session: Session):
        """Тест удаления несуществующего здания"""
        result = crud_building.delete_building(db_session, 999)
        
        assert result is False
    
    def test_get_buildings_in_area(self, db_session: Session, sample_buildings: list[Building]):
        """Тест поиска зданий в прямоугольной области"""
        # Ищем здания в Москве
        buildings = crud_building.get_buildings_in_area(
            db_session,
            min_lat=55.75,
            max_lat=55.76,
            min_lon=37.61,
            max_lon=37.62
        )
        
        assert len(buildings) == 2  # Два здания в Москве
        assert all(55.75 <= b.latitude <= 55.76 for b in buildings)
        assert all(37.61 <= b.longitude <= 37.62 for b in buildings)
    
    def test_get_buildings_in_radius(self, db_session: Session, sample_buildings: list[Building]):
        """Тест поиска зданий в радиусе"""
        # Ищем здания в радиусе 1 км от первого здания
        center = sample_buildings[0]
        buildings = crud_building.get_buildings_in_radius(
            db_session,
            latitude=center.latitude,
            longitude=center.longitude,
            radius_meters=1000
        )
        
        # Должно найти минимум центральное здание
        assert len(buildings) >= 1
        assert any(b.id == center.id for b in buildings)
    
    def test_get_buildings_in_radius_empty(self, db_session: Session, sample_buildings: list[Building]):
        """Тест поиска зданий в радиусе с пустым результатом"""
        # Ищем в точке где нет зданий
        buildings = crud_building.get_buildings_in_radius(
            db_session,
            latitude=0.0,
            longitude=0.0,
            radius_meters=100
        )
        
        assert len(buildings) == 0