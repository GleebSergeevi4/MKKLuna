from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional


def _split_phones(value: str) -> List[str]:
    return [phone.strip() for phone in value.split(',') if phone.strip()]


# ==================== Building Schemas ====================

class BuildingBase(BaseModel):
    """Базовая схема для здания"""
    address: str = Field(..., description="Адрес здания", min_length=1)
    latitude: float = Field(..., description="Широта", ge=-90, le=90)
    longitude: float = Field(..., description="Долгота", ge=-180, le=180)


class BuildingCreate(BuildingBase):
    """Схема для создания здания"""
    pass


class BuildingUpdate(BaseModel):
    """Схема для обновления здания"""
    address: Optional[str] = Field(None, description="Адрес здания", min_length=1)
    latitude: Optional[float] = Field(None, description="Широта", ge=-90, le=90)
    longitude: Optional[float] = Field(None, description="Долгота", ge=-180, le=180)


class Building(BuildingBase):
    """Схема для отображения здания"""
    id: int

    class Config:
        from_attributes = True


# ==================== Activity Schemas ====================

class ActivityBase(BaseModel):
    """Базовая схема для вида деятельности"""
    name: str = Field(..., description="Название вида деятельности", min_length=1)
    parent_id: Optional[int] = Field(None, description="ID родительского вида деятельности")


class ActivityCreate(ActivityBase):
    """Схема для создания вида деятельности"""
    pass


class ActivityUpdate(BaseModel):
    """Схема для обновления вида деятельности"""
    name: Optional[str] = Field(None, description="Название вида деятельности", min_length=1)
    parent_id: Optional[int] = Field(None, description="ID родительского вида деятельности")


class Activity(ActivityBase):
    """Схема для отображения вида деятельности"""
    id: int
    level: int = Field(..., description="Уровень вложенности (1-3)")

    class Config:
        from_attributes = True


class ActivityTree(Activity):
    """Схема для отображения дерева видов деятельности"""
    children: List['ActivityTree'] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ==================== Organization Schemas ====================

class OrganizationBase(BaseModel):
    """Базовая схема для организации"""
    name: str = Field(..., description="Название организации", min_length=1)
    phone_numbers: List[str] = Field(..., description="Список номеров телефонов", min_length=1)
    building_id: int = Field(..., description="ID здания")
    activity_ids: List[int] = Field(..., description="Список ID видов деятельности", min_length=1)

    @field_validator('phone_numbers')
    @classmethod
    def validate_phones(cls, v):
        if not v or len(v) == 0:
            raise ValueError('Должен быть указан хотя бы один номер телефона')
        # Убираем пустые строки
        return [phone.strip() for phone in v if phone.strip()]

    @field_validator('activity_ids')
    @classmethod
    def validate_activities(cls, v):
        if not v or len(v) == 0:
            raise ValueError('Должен быть указан хотя бы один вид деятельности')
        return v


class OrganizationCreate(OrganizationBase):
    """Схема для создания организации"""
    pass


class OrganizationUpdate(BaseModel):
    """Схема для обновления организации"""
    name: Optional[str] = Field(None, description="Название организации", min_length=1)
    phone_numbers: Optional[List[str]] = Field(None, description="Список номеров телефонов")
    building_id: Optional[int] = Field(None, description="ID здания")
    activity_ids: Optional[List[int]] = Field(None, description="Список ID видов деятельности")

    @field_validator('phone_numbers')
    @classmethod
    def validate_phones(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError('Должен быть указан хотя бы один номер телефона')
        if v is not None:
            return [phone.strip() for phone in v if phone.strip()]
        return v

    @field_validator('activity_ids')
    @classmethod
    def validate_activities(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError('Должен быть указан хотя бы один вид деятельности')
        return v


class Organization(BaseModel):
    """Схема для отображения организации"""
    id: int
    name: str
    phone_numbers: List[str]
    building_id: int
    building: Building
    activities: List[Activity]

    class Config:
        from_attributes = True

    @field_validator('phone_numbers', mode='before')
    @classmethod
    def parse_phone_numbers(cls, v):
        if isinstance(v, str):
            return _split_phones(v)
        return v


class OrganizationList(BaseModel):
    """Схема для списка организаций"""
    id: int
    name: str
    phone_numbers: List[str]
    building: Building
    activities: List[Activity]

    class Config:
        from_attributes = True

    @field_validator('phone_numbers', mode='before')
    @classmethod
    def parse_phone_numbers(cls, v):
        if isinstance(v, str):
            return _split_phones(v)
        return v


# ==================== Search Schemas ====================

class LocationSearch(BaseModel):
    """Схема для поиска по местоположению"""
    latitude: float = Field(..., description="Широта центральной точки", ge=-90, le=90)
    longitude: float = Field(..., description="Долгота центральной точки", ge=-180, le=180)
    radius: Optional[float] = Field(None, description="Радиус поиска в метрах", gt=0)
    min_latitude: Optional[float] = Field(None, description="Минимальная широта для прямоугольной области", ge=-90, le=90)
    max_latitude: Optional[float] = Field(None, description="Максимальная широта для прямоугольной области", ge=-90, le=90)
    min_longitude: Optional[float] = Field(None, description="Минимальная долгота для прямоугольной области", ge=-180, le=180)
    max_longitude: Optional[float] = Field(None, description="Максимальная долгота для прямоугольной области", ge=-180, le=180)

    @model_validator(mode='after')
    def validate_search_type(self):
        has_radius = self.radius is not None
        has_rectangle = all(
            value is not None
            for value in (
                self.min_latitude,
                self.max_latitude,
                self.min_longitude,
                self.max_longitude,
            )
        )

        if not has_radius and not has_rectangle:
            raise ValueError('Должен быть указан либо радиус поиска, либо координаты прямоугольной области')

        if has_radius and has_rectangle:
            raise ValueError('Можно указать либо радиус поиска, либо прямоугольную область, но не оба параметра одновременно')

        return self


# Обновляем forward references для рекурсивных моделей
ActivityTree.model_rebuild()