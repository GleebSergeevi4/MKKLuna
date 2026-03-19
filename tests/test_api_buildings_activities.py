"""
Интеграционные тесты для API эндпоинтов зданий и видов деятельности.
"""
import pytest
from fastapi.testclient import TestClient

from app.models.models import Building, Activity


@pytest.mark.integration
class TestBuildingsAPI:
    """Тесты для API эндпоинтов зданий"""
    
    def test_get_buildings(
        self,
        client: TestClient,
        api_headers: dict,
        sample_buildings: list[Building]
    ):
        """Тест получения списка зданий"""
        response = client.get("/api/buildings/", headers=api_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("address" in b for b in data)
        assert all("latitude" in b for b in data)
        assert all("longitude" in b for b in data)
    
    def test_get_building_by_id(
        self,
        client: TestClient,
        api_headers: dict,
        sample_building: Building
    ):
        """Тест получения здания по ID"""
        response = client.get(
            f"/api/buildings/{sample_building.id}",
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_building.id
        assert data["address"] == sample_building.address
    
    def test_create_building(self, client: TestClient, api_headers: dict):
        """Тест создания здания"""
        building_data = {
            "address": "г. Москва, ул. Новая 100",
            "latitude": 55.7558,
            "longitude": 37.6173
        }
        
        response = client.post(
            "/api/buildings/",
            headers=api_headers,
            json=building_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["address"] == "г. Москва, ул. Новая 100"
        assert data["latitude"] == 55.7558
    
    def test_update_building(
        self,
        client: TestClient,
        api_headers: dict,
        sample_building: Building
    ):
        """Тест обновления здания"""
        update_data = {
            "address": "г. Москва, ул. Обновленная 200"
        }
        
        response = client.put(
            f"/api/buildings/{sample_building.id}",
            headers=api_headers,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == "г. Москва, ул. Обновленная 200"
    
    def test_delete_building(
        self,
        client: TestClient,
        api_headers: dict,
        sample_building: Building
    ):
        """Тест удаления здания"""
        response = client.delete(
            f"/api/buildings/{sample_building.id}",
            headers=api_headers
        )
        
        assert response.status_code == 204


@pytest.mark.integration
class TestActivitiesAPI:
    """Тесты для API эндпоинтов видов деятельности"""
    
    def test_get_activities(
        self,
        client: TestClient,
        api_headers: dict,
        sample_activity_tree: dict
    ):
        """Тест получения списка видов деятельности"""
        response = client.get("/api/activities/", headers=api_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("name" in a for a in data)
        assert all("level" in a for a in data)
    
    def test_get_activity_tree(
        self,
        client: TestClient,
        api_headers: dict,
        sample_activity_tree: dict
    ):
        """Тест получения дерева видов деятельности"""
        response = client.get("/api/activities/tree", headers=api_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # Один корневой элемент
        assert data[0]["name"] == "Еда"
        assert len(data[0]["children"]) == 2
    
    def test_get_activity_by_id(
        self,
        client: TestClient,
        api_headers: dict,
        sample_activity: Activity
    ):
        """Тест получения вида деятельности по ID"""
        response = client.get(
            f"/api/activities/{sample_activity.id}",
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_activity.id
        assert data["name"] == sample_activity.name
    
    def test_get_activity_children(
        self,
        client: TestClient,
        api_headers: dict,
        sample_activity_tree: dict
    ):
        """Тест получения дочерних видов деятельности"""
        root = sample_activity_tree["root"]
        
        response = client.get(
            f"/api/activities/{root.id}/children",
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(a["parent_id"] == root.id for a in data)
    
    def test_get_activity_descendants(
        self,
        client: TestClient,
        api_headers: dict,
        sample_activity_tree: dict
    ):
        """Тест получения всех потомков"""
        root = sample_activity_tree["root"]
        
        response = client.get(
            f"/api/activities/{root.id}/descendants",
            headers=api_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3  # root + 2 children
    
    def test_create_activity_root(self, client: TestClient, api_headers: dict):
        """Тест создания корневого вида деятельности"""
        activity_data = {
            "name": "Новая деятельность",
            "parent_id": None
        }
        
        response = client.post(
            "/api/activities/",
            headers=api_headers,
            json=activity_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Новая деятельность"
        assert data["level"] == 1
        assert data["parent_id"] is None
    
    def test_create_activity_with_parent(
        self,
        client: TestClient,
        api_headers: dict,
        sample_activity: Activity
    ):
        """Тест создания вида деятельности с родителем"""
        activity_data = {
            "name": "Дочерний вид",
            "parent_id": sample_activity.id
        }
        
        response = client.post(
            "/api/activities/",
            headers=api_headers,
            json=activity_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Дочерний вид"
        assert data["parent_id"] == sample_activity.id
        assert data["level"] == 2
    
    def test_create_activity_max_depth_exceeded(
        self,
        client: TestClient,
        api_headers: dict,
        db_session
    ):
        """Тест превышения максимальной глубины"""
        # Создаем 3 уровня
        level1 = Activity(name="L1", level=1)
        db_session.add(level1)
        db_session.commit()
        db_session.refresh(level1)
        
        level2 = Activity(name="L2", parent_id=level1.id, level=2)
        db_session.add(level2)
        db_session.commit()
        db_session.refresh(level2)
        
        level3 = Activity(name="L3", parent_id=level2.id, level=3)
        db_session.add(level3)
        db_session.commit()
        db_session.refresh(level3)
        
        # Пытаемся создать 4-й уровень
        activity_data = {
            "name": "L4",
            "parent_id": level3.id
        }
        
        response = client.post(
            "/api/activities/",
            headers=api_headers,
            json=activity_data
        )
        
        assert response.status_code == 400
    
    def test_update_activity(
        self,
        client: TestClient,
        api_headers: dict,
        sample_activity: Activity
    ):
        """Тест обновления вида деятельности"""
        update_data = {
            "name": "Обновленное название"
        }
        
        response = client.put(
            f"/api/activities/{sample_activity.id}",
            headers=api_headers,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Обновленное название"
    
    def test_delete_activity(
        self,
        client: TestClient,
        api_headers: dict,
        sample_activity: Activity
    ):
        """Тест удаления вида деятельности"""
        response = client.delete(
            f"/api/activities/{sample_activity.id}",
            headers=api_headers
        )
        
        assert response.status_code == 204
    
    def test_search_activities_by_name(
        self,
        client: TestClient,
        api_headers: dict,
        sample_activity_tree: dict
    ):
        """Тест поиска видов деятельности по названию"""
        response = client.get(
            "/api/activities/search/name",
            headers=api_headers,
            params={"name": "Мясн"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert "Мясная" in data[0]["name"]