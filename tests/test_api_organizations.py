"""
Интеграционные тесты для API эндпоинтов организаций.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.models import Organization, Building, Activity


@pytest.mark.integration
class TestOrganizationsAPI:
    """Тесты для API эндпоинтов организаций"""
    
    def test_get_organizations(
        self,
        client: TestClient,
        api_headers: dict,
        sample_organizations: list[Organization]
    ):
        """Тест получения списка организаций"""
        response = client.get("/api/organizations/", headers=api_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("name" in org for org in data)
        assert all("building" in org for org in data)
        assert all("activities" in org for org in data)
    
    def test_get_organizations_without_api_key(self, client: TestClient):
        """Тест доступа без API ключа"""
        response = client.get("/api/organizations/")
        
        assert response.status_code == 403
    
    def test_get_organizations_invalid_api_key(self, client: TestClient):
        """Тест доступа с неверным API ключом"""
        headers = {"X-API-Key": "invalid_key"}
        response = client.get("/api/organizations/", headers=headers)
        
        assert response.status_code == 403
    
    def test_get_organization_by_id(
        self,
        client: TestClient,
        api_headers: dict,
        sample_organization: Organization
    ):
        """Тест получения организации по ID"""
        response = client.get(
            f"/api/organizations/{sample_organization.id}",
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_organization.id
        assert data["name"] == sample_organization.name
        assert "building" in data
        assert "activities" in data
    
    def test_get_organization_not_found(self, client: TestClient, api_headers: dict):
        """Тест получения несуществующей организации"""
        response = client.get("/api/organizations/999", headers=api_headers)
        
        assert response.status_code == 404
    
    def test_create_organization(
        self,
        client: TestClient,
        api_headers: dict,
        sample_building: Building,
        sample_activity: Activity
    ):
        """Тест создания организации"""
        org_data = {
            "name": "ООО Новая компания",
            "phone_numbers": ["8-800-555-35-35"],
            "building_id": sample_building.id,
            "activity_ids": [sample_activity.id]
        }
        
        response = client.post(
            "/api/organizations/",
            headers=api_headers,
            json=org_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "ООО Новая компания"
        assert "8-800-555-35-35" in data["phone_numbers"]
        assert data["building_id"] == sample_building.id
    
    def test_create_organization_validation_error(
        self,
        client: TestClient,
        api_headers: dict
    ):
        """Тест валидации при создании организации"""
        # Без обязательных полей
        org_data = {
            "name": "Тест"
        }
        
        response = client.post(
            "/api/organizations/",
            headers=api_headers,
            json=org_data
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_update_organization(
        self,
        client: TestClient,
        api_headers: dict,
        sample_organization: Organization
    ):
        """Тест обновления организации"""
        update_data = {
            "name": "ООО Обновленная"
        }
        
        response = client.put(
            f"/api/organizations/{sample_organization.id}",
            headers=api_headers,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "ООО Обновленная"
    
    def test_update_organization_not_found(self, client: TestClient, api_headers: dict):
        """Тест обновления несуществующей организации"""
        update_data = {"name": "Тест"}
        
        response = client.put(
            "/api/organizations/999",
            headers=api_headers,
            json=update_data
        )
        
        assert response.status_code == 404
    
    def test_delete_organization(
        self,
        client: TestClient,
        api_headers: dict,
        sample_organization: Organization
    ):
        """Тест удаления организации"""
        org_id = sample_organization.id
        
        response = client.delete(
            f"/api/organizations/{org_id}",
            headers=api_headers
        )
        
        assert response.status_code == 204
        
        # Проверяем, что организация удалена
        get_response = client.get(
            f"/api/organizations/{org_id}",
            headers=api_headers
        )
        assert get_response.status_code == 404
    
    def test_get_organizations_by_building(
        self,
        client: TestClient,
        api_headers: dict,
        sample_organizations: list[Organization],
        sample_buildings: list[Building]
    ):
        """Тест получения организаций по зданию"""
        building = sample_buildings[0]
        
        response = client.get(
            f"/api/organizations/building/{building.id}",
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(org["building_id"] == building.id for org in data)
    
    def test_get_organizations_by_activity(
        self,
        client: TestClient,
        api_headers: dict,
        sample_organizations: list[Organization],
        sample_activity_tree: dict
    ):
        """Тест получения организаций по виду деятельности"""
        meat = sample_activity_tree["children"][0]
        
        response = client.get(
            f"/api/organizations/activity/{meat.id}",
            headers=api_headers,
            params={"include_descendants": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_get_organizations_by_activity_with_descendants(
        self,
        client: TestClient,
        api_headers: dict,
        sample_organizations: list[Organization],
        sample_activity_tree: dict
    ):
        """Тест получения организаций с вложенными видами деятельности"""
        root = sample_activity_tree["root"]
        
        response = client.get(
            f"/api/organizations/activity/{root.id}",
            headers=api_headers,
            params={"include_descendants": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
    
    def test_search_organizations_by_location_radius(
        self,
        client: TestClient,
        api_headers: dict,
        sample_organizations: list[Organization],
        sample_buildings: list[Building]
    ):
        """Тест поиска организаций в радиусе"""
        center = sample_buildings[0]
        location_data = {
            "latitude": center.latitude,
            "longitude": center.longitude,
            "radius": 1000
        }
        
        response = client.post(
            "/api/organizations/search/location",
            headers=api_headers,
            json=location_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
    
    def test_search_organizations_by_location_area(
        self,
        client: TestClient,
        api_headers: dict,
        sample_organizations: list[Organization]
    ):
        """Тест поиска организаций в прямоугольной области"""
        location_data = {
            "latitude": 55.7558,
            "longitude": 37.6173,
            "min_latitude": 55.75,
            "max_latitude": 55.76,
            "min_longitude": 37.61,
            "max_longitude": 37.62
        }
        
        response = client.post(
            "/api/organizations/search/location",
            headers=api_headers,
            json=location_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
    
    def test_search_organizations_by_name(
        self,
        client: TestClient,
        api_headers: dict,
        sample_organizations: list[Organization]
    ):
        """Тест поиска организаций по названию"""
        response = client.get(
            "/api/organizations/search/name",
            headers=api_headers,
            params={"name": "Рога"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Рога и Копыта" in data[0]["name"]
    
    def test_pagination(
        self,
        client: TestClient,
        api_headers: dict,
        sample_organizations: list[Organization]
    ):
        """Тест пагинации"""
        response = client.get(
            "/api/organizations/",
            headers=api_headers,
            params={"skip": 1, "limit": 1}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1