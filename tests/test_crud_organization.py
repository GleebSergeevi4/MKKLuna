"""
Unit тесты для CRUD операций с организациями.
"""
import pytest
from sqlalchemy.orm import Session

from app.crud import organization as crud_organization
from app.schemas.schemas import OrganizationCreate, OrganizationUpdate
from app.models.models import Organization, Building, Activity


@pytest.mark.unit
class TestOrganizationCRUD:
    """Тесты для CRUD операций с организациями"""
    
    def test_create_organization(self, db_session: Session, sample_building: Building, sample_activity: Activity):
        """Тест создания организации"""
        org_data = OrganizationCreate(
            name="ООО Тестовая",
            phone_numbers=["8-800-555-35-35", "2-222-222"],
            building_id=sample_building.id,
            activity_ids=[sample_activity.id]
        )
        
        org = crud_organization.create_organization(db_session, org_data)
        
        assert org.id is not None
        assert org.name == "ООО Тестовая"
        assert "8-800-555-35-35" in org.phone_numbers
        assert org.building_id == sample_building.id
        assert len(org.activities) == 1
        assert org.activities[0].id == sample_activity.id
    
    def test_create_organization_multiple_activities(
        self,
        db_session: Session,
        sample_building: Building,
        sample_activity_tree: dict
    ):
        """Тест создания организации с несколькими видами деятельности"""
        activities = sample_activity_tree["children"]
        activity_ids = [a.id for a in activities]
        
        org_data = OrganizationCreate(
            name="ООО Многопрофильная",
            phone_numbers=["8-800-100-20-30"],
            building_id=sample_building.id,
            activity_ids=activity_ids
        )
        
        org = crud_organization.create_organization(db_session, org_data)
        
        assert len(org.activities) == 2
        assert set(a.id for a in org.activities) == set(activity_ids)
    
    def test_create_organization_building_not_found(self, db_session: Session, sample_activity: Activity):
        """Тест создания организации с несуществующим зданием"""
        org_data = OrganizationCreate(
            name="Тест",
            phone_numbers=["123"],
            building_id=999,
            activity_ids=[sample_activity.id]
        )
        
        with pytest.raises(ValueError, match="Здание не найдено"):
            crud_organization.create_organization(db_session, org_data)
    
    def test_create_organization_activity_not_found(self, db_session: Session, sample_building: Building):
        """Тест создания организации с несуществующим видом деятельности"""
        org_data = OrganizationCreate(
            name="Тест",
            phone_numbers=["123"],
            building_id=sample_building.id,
            activity_ids=[999]
        )
        
        with pytest.raises(ValueError, match="деятельности не найдены"):
            crud_organization.create_organization(db_session, org_data)
    
    def test_get_organization(self, db_session: Session, sample_organization: Organization):
        """Тест получения организации по ID"""
        org = crud_organization.get_organization(db_session, sample_organization.id)
        
        assert org is not None
        assert org.id == sample_organization.id
        assert org.name == sample_organization.name
        assert org.building is not None  # Проверяем загрузку связей
        assert len(org.activities) > 0
    
    def test_get_organization_not_found(self, db_session: Session):
        """Тест получения несуществующей организации"""
        org = crud_organization.get_organization(db_session, 999)
        
        assert org is None
    
    def test_get_organizations(self, db_session: Session, sample_organizations: list[Organization]):
        """Тест получения списка организаций"""
        orgs = crud_organization.get_organizations(db_session, skip=0, limit=10)
        
        assert len(orgs) == 3
        assert all(isinstance(o, Organization) for o in orgs)
        assert all(o.building is not None for o in orgs)  # Проверяем eager loading
    
    def test_get_organizations_pagination(self, db_session: Session, sample_organizations: list[Organization]):
        """Тест пагинации списка организаций"""
        orgs = crud_organization.get_organizations(db_session, skip=1, limit=1)
        
        assert len(orgs) == 1
    
    def test_update_organization(
        self,
        db_session: Session,
        sample_organization: Organization,
        sample_building: Building
    ):
        """Тест обновления организации"""
        update_data = OrganizationUpdate(
            name="ООО Обновленная",
            phone_numbers=["8-900-100-20-30"]
        )
        
        updated = crud_organization.update_organization(
            db_session,
            sample_organization.id,
            update_data
        )
        
        assert updated.name == "ООО Обновленная"
        assert "8-900-100-20-30" in updated.phone_numbers
    
    def test_update_organization_activities(
        self,
        db_session: Session,
        sample_organization: Organization,
        sample_activity_tree: dict
    ):
        """Тест обновления видов деятельности организации"""
        new_activities = sample_activity_tree["children"]
        new_activity_ids = [a.id for a in new_activities]
        
        update_data = OrganizationUpdate(activity_ids=new_activity_ids)
        
        updated = crud_organization.update_organization(
            db_session,
            sample_organization.id,
            update_data
        )
        
        assert len(updated.activities) == 2
        assert set(a.id for a in updated.activities) == set(new_activity_ids)
    
    def test_update_organization_not_found(self, db_session: Session):
        """Тест обновления несуществующей организации"""
        update_data = OrganizationUpdate(name="Тест")
        
        result = crud_organization.update_organization(db_session, 999, update_data)
        
        assert result is None
    
    def test_delete_organization(self, db_session: Session, sample_organization: Organization):
        """Тест удаления организации"""
        org_id = sample_organization.id
        
        result = crud_organization.delete_organization(db_session, org_id)
        
        assert result is True
        
        # Проверяем удаление
        deleted = crud_organization.get_organization(db_session, org_id)
        assert deleted is None
    
    def test_delete_organization_not_found(self, db_session: Session):
        """Тест удаления несуществующей организации"""
        result = crud_organization.delete_organization(db_session, 999)
        
        assert result is False
    
    def test_get_organizations_by_building(
        self,
        db_session: Session,
        sample_organizations: list[Organization],
        sample_buildings: list[Building]
    ):
        """Тест получения организаций по зданию"""
        building = sample_buildings[0]
        orgs = crud_organization.get_organizations_by_building(db_session, building.id)
        
        # В первом здании две организации
        assert len(orgs) == 2
        assert all(o.building_id == building.id for o in orgs)
    
    def test_get_organizations_by_activity(
        self,
        db_session: Session,
        sample_organizations: list[Organization],
        sample_activity_tree: dict
    ):
        """Тест получения организаций по виду деятельности"""
        meat = sample_activity_tree["children"][0]
        orgs = crud_organization.get_organizations_by_activity(
            db_session,
            meat.id,
            include_descendants=False
        )
        
        # Две организации с мясной продукцией
        assert len(orgs) == 2
    
    def test_get_organizations_by_activity_with_descendants(
        self,
        db_session: Session,
        sample_organizations: list[Organization],
        sample_activity_tree: dict
    ):
        """Тест получения организаций по виду деятельности с потомками"""
        root = sample_activity_tree["root"]
        orgs = crud_organization.get_organizations_by_activity(
            db_session,
            root.id,
            include_descendants=True
        )
        
        # Все три организации имеют виды деятельности из дерева "Еда"
        assert len(orgs) == 3
    
    def test_get_organizations_by_location_radius(
        self,
        db_session: Session,
        sample_organizations: list[Organization],
        sample_buildings: list[Building]
    ):
        """Тест поиска организаций в радиусе"""
        center = sample_buildings[0]
        orgs = crud_organization.get_organizations_by_location_radius(
            db_session,
            latitude=center.latitude,
            longitude=center.longitude,
            radius_meters=1000
        )
        
        # Должны найти организации в ближайших зданиях
        assert len(orgs) >= 2
    
    def test_get_organizations_by_location_area(
        self,
        db_session: Session,
        sample_organizations: list[Organization],
        sample_buildings: list[Building]
    ):
        """Тест поиска организаций в прямоугольной области"""
        # Область, покрывающая московские здания
        orgs = crud_organization.get_organizations_by_location_area(
            db_session,
            min_lat=55.75,
            max_lat=55.76,
            min_lon=37.61,
            max_lon=37.62
        )
        
        # Должны найти организации в московских зданиях
        assert len(orgs) == 3
    
    def test_search_organizations_by_name(
        self,
        db_session: Session,
        sample_organizations: list[Organization]
    ):
        """Тест поиска организаций по названию"""
        orgs = crud_organization.search_organizations_by_name(db_session, "Рога")
        
        assert len(orgs) == 1
        assert "Рога и Копыта" in orgs[0].name
    
    def test_search_organizations_by_name_case_insensitive(
        self,
        db_session: Session,
        sample_organizations: list[Organization]
    ):
        """Тест регистронезависимого поиска"""
        orgs = crud_organization.search_organizations_by_name(db_session, "мясной")
        
        assert len(orgs) == 1
        assert "Мясной" in orgs[0].name
    
    def test_search_organizations_by_name_no_results(self, db_session: Session):
        """Тест поиска без результатов"""
        orgs = crud_organization.search_organizations_by_name(db_session, "НесуществующаяОрганизация")
        
        assert len(orgs) == 0