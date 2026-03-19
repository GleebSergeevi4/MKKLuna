from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table, CheckConstraint, event
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
from app.models.base import Base
from app.core.config import settings


# Ассоциативная таблица для связи многие-ко-многим между организациями и видами деятельности
organization_activity = Table(
    'organization_activity',
    Base.metadata,
    Column('organization_id', Integer, ForeignKey('organizations.id', ondelete='CASCADE'), primary_key=True),
    Column('activity_id', Integer, ForeignKey('activities.id', ondelete='CASCADE'), primary_key=True)
)


class Building(Base):
    """
    Модель для зданий.
    Содержит информацию об адресе и географических координатах.
    """
    __tablename__ = 'buildings'

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Связь с организациями
    organizations = relationship("Organization", back_populates="building", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Building(id={self.id}, address='{self.address}')>"


class Activity(Base):
    """
    Модель для видов деятельности.
    Древовидная структура с ограничением на глубину вложенности (3 уровня).
    """
    __tablename__ = 'activities'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey('activities.id', ondelete='CASCADE'), nullable=True)
    level = Column(Integer, nullable=False, default=1)

    # Самоссылающаяся связь для древовидной структуры
    parent = relationship("Activity", remote_side=[id], back_populates="children")
    children = relationship("Activity", back_populates="parent", cascade="all, delete-orphan")

    # Связь с организациями через ассоциативную таблицу
    organizations = relationship(
        "Organization",
        secondary=organization_activity,
        back_populates="activities"
    )

    # Ограничение на максимальный уровень вложенности
    __table_args__ = (
        CheckConstraint(f'level <= {settings.MAX_ACTIVITY_DEPTH}', name='check_max_level'),
    )

    @validates('parent_id')
    def validate_parent(self, key, parent_id):
        """
        Валидация родительского элемента и уровня вложенности.
        """
        if parent_id is not None:
            # Проверяем уровень вложенности через родителя
            from sqlalchemy.orm import Session
            session = Session.object_session(self)
            if session:
                parent = session.query(Activity).filter(Activity.id == parent_id).first()
                if parent:
                    self.level = parent.level + 1
                    if self.level > settings.MAX_ACTIVITY_DEPTH:
                        raise ValueError(f"Максимальный уровень вложенности ({settings.MAX_ACTIVITY_DEPTH}) превышен")
        else:
            self.level = 1
        return parent_id

    def __repr__(self):
        return f"<Activity(id={self.id}, name='{self.name}', level={self.level})>"

    def get_all_descendants(self):
        """
        Получить все дочерние элементы (рекурсивно).
        """
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants


class Organization(Base):
    """
    Модель для организаций.
    Содержит информацию об организации, её местоположении и видах деятельности.
    """
    __tablename__ = 'organizations'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    phone_numbers = Column(String, nullable=False)  # Храним как строку через запятую
    building_id = Column(Integer, ForeignKey('buildings.id', ondelete='CASCADE'), nullable=False)

    # Связь с зданием
    building = relationship("Building", back_populates="organizations")

    # Связь с видами деятельности через ассоциативную таблицу
    activities = relationship(
        "Activity",
        secondary=organization_activity,
        back_populates="organizations"
    )

    @hybrid_property
    def phone_list(self):
        """
        Получить список номеров телефонов.
        """
        return [phone.strip() for phone in self.phone_numbers.split(',') if phone.strip()]

    @phone_list.setter
    def phone_list(self, value):
        """
        Установить список номеров телефонов.
        """
        if isinstance(value, list):
            self.phone_numbers = ', '.join(value)
        else:
            self.phone_numbers = value

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"


# Обработчик события для автоматического вычисления уровня при установке родителя
@event.listens_for(Activity.parent, 'set')
def receive_parent_set(target, value, oldvalue, initiator):
    """
    Автоматически устанавливает уровень при назначении родителя.
    """
    if value is not None:
        target.level = value.level + 1
        if target.level > settings.MAX_ACTIVITY_DEPTH:
            raise ValueError(f"Максимальный уровень вложенности ({settings.MAX_ACTIVITY_DEPTH}) превышен")
    else:
        target.level = 1