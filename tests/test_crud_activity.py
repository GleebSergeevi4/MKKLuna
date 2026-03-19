"""
Unit тесты для CRUD операций с видами деятельности.
"""
import pytest
from sqlalchemy.orm import Session

from app.crud import activity as crud_activity
from app.schemas.schemas import ActivityCreate, ActivityUpdate
from app.models.models import Activity
from app.core.config import settings


@pytest.mark.unit
class TestActivityCRUD:
    """Тесты для CRUD операций с видами деятельности"""
    
    def test_create_activity_root(self, db_session: Session):
        """Тест создания корневого вида деятельности"""
        activity_data = ActivityCreate(
            name="Новая деятельность",
            parent_id=None
        )
        
        activity = crud_activity.create_activity(db_session, activity_data)
        
        assert activity.id is not None
        assert activity.name == "Новая деятельность"
        assert activity.parent_id is None
        assert activity.level == 1
    
    def test_create_activity_with_parent(self, db_session: Session, sample_activity: Activity):
        """Тест создания вида деятельности с родителем"""
        activity_data = ActivityCreate(
            name="Дочерняя деятельность",
            parent_id=sample_activity.id
        )
        
        activity = crud_activity.create_activity(db_session, activity_data)
        
        assert activity.id is not None
        assert activity.name == "Дочерняя деятельность"
        assert activity.parent_id == sample_activity.id
        assert activity.level == 2
    
    def test_create_activity_max_depth_exceeded(self, db_session: Session):
        """Тест превышения максимальной глубины вложенности"""
        # Создаем 3 уровня
        level1 = Activity(name="Уровень 1", level=1)
        db_session.add(level1)
        db_session.commit()
        db_session.refresh(level1)
        
        level2 = Activity(name="Уровень 2", parent_id=level1.id, level=2)
        db_session.add(level2)
        db_session.commit()
        db_session.refresh(level2)
        
        level3 = Activity(name="Уровень 3", parent_id=level2.id, level=3)
        db_session.add(level3)
        db_session.commit()
        db_session.refresh(level3)
        
        # Пытаемся создать 4-й уровень
        activity_data = ActivityCreate(
            name="Уровень 4",
            parent_id=level3.id
        )
        
        with pytest.raises(ValueError, match="максимальный уровень"):
            crud_activity.create_activity(db_session, activity_data)
    
    def test_create_activity_parent_not_found(self, db_session: Session):
        """Тест создания деятельности с несуществующим родителем"""
        activity_data = ActivityCreate(
            name="Тест",
            parent_id=999
        )
        
        with pytest.raises(ValueError, match="не найден"):
            crud_activity.create_activity(db_session, activity_data)
    
    def test_get_activity(self, db_session: Session, sample_activity: Activity):
        """Тест получения вида деятельности по ID"""
        activity = crud_activity.get_activity(db_session, sample_activity.id)
        
        assert activity is not None
        assert activity.id == sample_activity.id
        assert activity.name == sample_activity.name
    
    def test_get_activity_not_found(self, db_session: Session):
        """Тест получения несуществующего вида деятельности"""
        activity = crud_activity.get_activity(db_session, 999)
        
        assert activity is None
    
    def test_get_activities(self, db_session: Session, sample_activity_tree: dict):
        """Тест получения списка видов деятельности"""
        activities = crud_activity.get_activities(db_session, skip=0, limit=10)
        
        assert len(activities) == 3  # root + 2 children
        assert all(isinstance(a, Activity) for a in activities)
    
    def test_get_root_activities(self, db_session: Session, sample_activity_tree: dict):
        """Тест получения корневых видов деятельности"""
        root_activities = crud_activity.get_root_activities(db_session)
        
        assert len(root_activities) == 1
        assert root_activities[0].name == "Еда"
        assert root_activities[0].level == 1
        assert root_activities[0].parent_id is None
    
    def test_get_activity_children(self, db_session: Session, sample_activity_tree: dict):
        """Тест получения дочерних видов деятельности"""
        root = sample_activity_tree["root"]
        children = crud_activity.get_activity_children(db_session, root.id)
        
        assert len(children) == 2
        assert all(c.parent_id == root.id for c in children)
        assert all(c.level == 2 for c in children)
    
    def test_get_activity_descendants(self, db_session: Session, sample_activity_tree: dict):
        """Тест получения всех потомков"""
        root = sample_activity_tree["root"]
        descendants = crud_activity.get_activity_descendants(db_session, root.id)
        
        # Должен включать сам элемент и его детей
        assert len(descendants) == 3
        assert descendants[0].id == root.id
    
    def test_update_activity(self, db_session: Session, sample_activity: Activity):
        """Тест обновления вида деятельности"""
        update_data = ActivityUpdate(name="Обновленное название")
        
        updated_activity = crud_activity.update_activity(
            db_session,
            sample_activity.id,
            update_data
        )
        
        assert updated_activity is not None
        assert updated_activity.name == "Обновленное название"
        assert updated_activity.level == sample_activity.level
    
    def test_update_activity_change_parent(self, db_session: Session, sample_activity_tree: dict):
        """Тест изменения родителя"""
        root = sample_activity_tree["root"]
        child = sample_activity_tree["children"][0]
        
        # Создаем новый корневой элемент
        new_root = Activity(name="Новый корень", level=1)
        db_session.add(new_root)
        db_session.commit()
        db_session.refresh(new_root)
        
        # Меняем родителя
        update_data = ActivityUpdate(parent_id=new_root.id)
        updated = crud_activity.update_activity(db_session, child.id, update_data)
        
        assert updated.parent_id == new_root.id
        assert updated.level == 2
    
    def test_update_activity_self_parent(self, db_session: Session, sample_activity: Activity):
        """Тест попытки сделать элемент родителем самого себя"""
        update_data = ActivityUpdate(parent_id=sample_activity.id)
        
        with pytest.raises(ValueError, match="не может быть родителем самого себя"):
            crud_activity.update_activity(db_session, sample_activity.id, update_data)
    
    def test_update_activity_not_found(self, db_session: Session):
        """Тест обновления несуществующего вида деятельности"""
        update_data = ActivityUpdate(name="Тест")
        
        result = crud_activity.update_activity(db_session, 999, update_data)
        
        assert result is None
    
    def test_delete_activity(self, db_session: Session, sample_activity: Activity):
        """Тест удаления вида деятельности"""
        activity_id = sample_activity.id
        
        result = crud_activity.delete_activity(db_session, activity_id)
        
        assert result is True
        
        # Проверяем, что деятельность удалена
        deleted = crud_activity.get_activity(db_session, activity_id)
        assert deleted is None
    
    def test_delete_activity_cascade(self, db_session: Session, sample_activity_tree: dict):
        """Тест каскадного удаления (родитель удаляет детей)"""
        root = sample_activity_tree["root"]
        child_ids = [c.id for c in sample_activity_tree["children"]]
        
        # Удаляем корневой элемент
        crud_activity.delete_activity(db_session, root.id)
        
        # Проверяем, что дети тоже удалены
        for child_id in child_ids:
            assert crud_activity.get_activity(db_session, child_id) is None
    
    def test_delete_activity_not_found(self, db_session: Session):
        """Тест удаления несуществующего вида деятельности"""
        result = crud_activity.delete_activity(db_session, 999)
        
        assert result is False
    
    def test_search_activities_by_name(self, db_session: Session, sample_activity_tree: dict):
        """Тест поиска видов деятельности по названию"""
        # Ищем по части слова
        activities = crud_activity.search_activities_by_name(db_session, "Мясн")
        
        assert len(activities) == 1
        assert activities[0].name == "Мясная продукция"
    
    def test_search_activities_by_name_case_insensitive(self, db_session: Session, sample_activity_tree: dict):
        """Тест регистронезависимого поиска"""
        activities = crud_activity.search_activities_by_name(db_session, "ЕДА")
        
        assert len(activities) == 1
        assert activities[0].name == "Еда"
    
    def test_search_activities_by_name_no_results(self, db_session: Session):
        """Тест поиска без результатов"""
        activities = crud_activity.search_activities_by_name(db_session, "НесуществующаяДеятельность")
        
        assert len(activities) == 0