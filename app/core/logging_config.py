"""
Модуль конфигурации логирования для приложения.
Настраивает структурированное логирование с ротацией файлов.
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

from app.core.config import settings


# Создаем директорию для логов
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


def setup_logging():
    """
    Настройка системы логирования приложения.
    
    Создает логгеры для:
    - Общих логов приложения (app.log)
    - Логов API запросов (api.log)
    - Логов базы данных (db.log)
    - Логов ошибок (error.log)
    """
    
    # Формат логов
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Консольный вывод
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    
    # === Главный логгер приложения ===
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    app_logger.handlers.clear()
    
    # Файловый обработчик для общих логов (с ротацией)
    app_file_handler = RotatingFileHandler(
        LOGS_DIR / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    app_file_handler.setLevel(logging.DEBUG)
    app_file_handler.setFormatter(log_format)
    
    app_logger.addHandler(console_handler)
    app_logger.addHandler(app_file_handler)
    
    # === Логгер для API запросов ===
    api_logger = logging.getLogger("app.api")
    api_logger.setLevel(logging.INFO)
    
    api_file_handler = RotatingFileHandler(
        LOGS_DIR / "api.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    api_file_handler.setLevel(logging.INFO)
    api_file_handler.setFormatter(log_format)
    api_logger.addHandler(api_file_handler)
    
    # === Логгер для базы данных ===
    db_logger = logging.getLogger("app.database")
    db_logger.setLevel(logging.INFO)
    
    db_file_handler = RotatingFileHandler(
        LOGS_DIR / "db.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    db_file_handler.setLevel(logging.INFO)
    db_file_handler.setFormatter(log_format)
    db_logger.addHandler(db_file_handler)
    
    # === Логгер для ошибок ===
    error_logger = logging.getLogger("app.error")
    error_logger.setLevel(logging.ERROR)
    
    error_file_handler = RotatingFileHandler(
        LOGS_DIR / "error.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(log_format)
    error_logger.addHandler(error_file_handler)
    
    # Отключаем дублирование логов SQLAlchemy в консоли
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    app_logger.info("=" * 80)
    app_logger.info(f"Приложение {settings.PROJECT_NAME} запущено")
    app_logger.info(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    app_logger.info(f"Режим отладки: {settings.DEBUG}")
    app_logger.info("=" * 80)
    
    return app_logger


def get_logger(name: str) -> logging.Logger:
    """
    Получить логгер по имени.
    
    Args:
        name: Имя логгера (например, 'app.api', 'app.database')
    
    Returns:
        logging.Logger: Настроенный логгер
    """
    return logging.getLogger(name)