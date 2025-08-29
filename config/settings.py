import os
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    db_connection: str
    db_host: str
    db_port: int
    db_database: str
    db_username: str
    db_password: str
    db_schema: str

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Logging
    log_level: str = "INFO"
    
    # Security - Production values should be overridden by environment
    allowed_origins: str = "http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000,http://192.168.11.83:3000,http://192.168.11.83:8080"
    allowed_hosts: str = "localhost,127.0.0.1,192.168.11.83,*.local,testserver"
    
    # Cache (Redis)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    cache_ttl: int = 300  # 5 minutes default

    class Config:
        env_file = ".env"
        case_sensitive = False
        env_file_encoding = "utf-8"

    @property
    def database_url(self) -> str:
        """Generate database URL with properly encoded password"""
        encoded_password = quote_plus(self.db_password)
        return (
            f"{self.db_connection}://{self.db_username}:{encoded_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_database}"
        )

    @property
    def database_url_with_schema(self) -> str:
        """Database URL with schema parameter"""
        return f"{self.database_url}?options=-csearch_path%3D{self.db_schema}"


settings = Settings()