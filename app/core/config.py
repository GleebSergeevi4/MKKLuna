from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # База данных
    DATABASE_URL: str

    # API настройки
    API_KEY: str
    API_KEY_NAME: str = "X-API-Key"

    # Настройки сервера
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Настройки приложения
    MAX_ACTIVITY_DEPTH: int = 3
    PROJECT_NAME: str = "Organization Directory API"
    DEBUG: bool = False
    
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()