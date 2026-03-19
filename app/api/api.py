from fastapi import APIRouter

from app.api.endpoints import organizations, buildings, activities

api_router = APIRouter()

# Подключаем все маршруты из различных модулей
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(buildings.router, prefix="/buildings", tags=["buildings"])
api_router.include_router(activities.router, prefix="/activities", tags=["activities"])