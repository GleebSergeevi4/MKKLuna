from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from typing import Callable

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.api.api import api_router

# Настраиваем логирование
logger = setup_logging()
api_logger = get_logger("app.api")
error_logger = get_logger("app.error")


def create_application() -> FastAPI:
    """
    Фабрика для создания экземпляра FastAPI
    """
    logger.info("Инициализация приложения FastAPI")
    
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description="API для справочника организаций, зданий и деятельности",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    
    # Настраиваем CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # В продакшене лучше указать конкретные домены
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Middleware для логирования запросов
    @application.middleware("http")
    async def log_requests(request: Request, call_next: Callable):
        """Логирование всех HTTP запросов"""
        start_time = time.time()
        
        # Логируем входящий запрос
        api_logger.info(
            "Запрос: %s %s от %s",
            request.method,
            request.url.path,
            request.client.host if request.client else "unknown",
        )
        
        try:
            response = await call_next(request)
            
            # Вычисляем время обработки
            process_time = time.time() - start_time
            
            # Логируем ответ
            api_logger.info(
                "Ответ: %s %s [%s] за %.3fs",
                request.method,
                request.url.path,
                response.status_code,
                process_time,
            )
            
            return response
            
        except Exception as exc:
            process_time = time.time() - start_time
            error_logger.error(
                "Ошибка при обработке запроса %s %s за %.3fs: %s",
                request.method,
                request.url.path,
                process_time,
                str(exc),
                exc_info=True
            )
            
            # Возвращаем ошибку 500
            return JSONResponse(
                status_code=500,
                content={"detail": "Внутренняя ошибка сервера"}
            )
    
    # Обработчик исключений
    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Глобальный обработчик исключений"""
        error_logger.error(
            "Необработанное исключение для %s %s: %s",
            request.method,
            request.url.path,
            str(exc),
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Внутренняя ошибка сервера"}
        )
    
    # Подключаем маршруты API
    application.include_router(api_router, prefix="/api")
    logger.info("API маршруты зарегистрированы")
    
    @application.get("/", include_in_schema=False)
    async def root():
        """
        Корневой маршрут, редиректит на документацию
        """
        return {"message": "Добро пожаловать в API справочника организаций. Перейдите к /api/docs для документации."}
    
    @application.get("/health", include_in_schema=False)
    async def health_check():
        """
        Health check endpoint для мониторинга
        """
        return {"status": "healthy", "service": settings.PROJECT_NAME}
    
    logger.info("Приложение FastAPI успешно инициализировано")
    return application


app = create_application()