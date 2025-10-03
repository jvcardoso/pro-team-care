"""
Settings - Configuração centralizada e segura do sistema
RESOLVE PROBLEMA COM @ NA SENHA usando URL encoding
"""

import os
import secrets
from functools import lru_cache
from typing import List, Optional
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pydantic import Field, validator
from pydantic_settings import BaseSettings

# ✅ Carrega .env explicitamente antes da configuração
load_dotenv()


class Settings(BaseSettings):
    """
    Configurações da aplicação com validação Pydantic
    ✅ Resolve problema com @ na senha usando quote_plus
    """

    # =================================
    # CONFIGURAÇÕES BÁSICAS
    # =================================

    app_name: str = "Pro Team Care System"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")

    # =================================
    # CONFIGURAÇÕES DO BANCO DE DADOS
    # =================================

    # Componentes separados para facilitar encoding - ✅ Acesso direto ao ambiente
    db_connection: str = Field(
        default_factory=lambda: os.getenv("DB_CONNECTION", "postgresql+asyncpg")
    )
    db_host: str = Field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    db_port: int = Field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    db_username: str = Field(
        default_factory=lambda: os.getenv("DB_USERNAME", "postgres")
    )
    db_password: str = Field(
        default_factory=lambda: os.getenv("DB_PASSWORD", "")
    )  # ✅ Será encoded automaticamente
    db_database: str = Field(
        default_factory=lambda: os.getenv("DB_DATABASE", "database")
    )
    db_schema: str = Field(default_factory=lambda: os.getenv("DB_SCHEMA", "master"))

    # Pool de conexões
    db_pool_size: int = Field(default=5, env="DB_POOL_SIZE")
    db_pool_overflow: int = Field(default=10, env="DB_POOL_OVERFLOW")
    db_pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")

    @property
    def database_url(self) -> str:
        """
        ✅ RESOLVE PROBLEMA COM @ NA SENHA
        Constrói DATABASE_URL com encoding seguro da senha
        """
        # URL encode da senha para caracteres especiais (@, %, etc.)
        encoded_password = quote_plus(self.db_password)

        return (
            f"{self.db_connection}://"
            f"{self.db_username}:{encoded_password}@"
            f"{self.db_host}:{self.db_port}/"
            f"{self.db_database}"
        )

    @property
    def database_url_with_schema(self) -> str:
        """Database URL com schema para asyncpg"""
        return f"{self.database_url}?server_settings=search_path%3D{self.db_schema}"

    @property
    def database_url_sync(self) -> str:
        """DATABASE_URL para conexões síncronas (Alembic)"""
        encoded_password = quote_plus(self.db_password)

        return (
            f"postgresql://"
            f"{self.db_username}:{encoded_password}@"
            f"{self.db_host}:{self.db_port}/"
            f"{self.db_database}"
        )

    # =================================
    # CONFIGURAÇÕES DE SEGURANÇA
    # =================================

    # JWT Settings - ✅ Usando acesso direto ao ambiente devido a incompatibilidade do pydantic-settings
    secret_key: str = Field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", ""))
    algorithm: str = Field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    access_token_expire_minutes: int = Field(
        default_factory=lambda: int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    )

    # =================================
    # CONFIGURAÇÕES DO REDIS
    # =================================

    # Redis para cache de permissões
    redis_host: str = Field(
        default_factory=lambda: os.getenv("REDIS_HOST", "localhost")
    )
    redis_port: int = Field(
        default_factory=lambda: int(os.getenv("REDIS_PORT", "6379"))
    )
    redis_password: Optional[str] = Field(
        default_factory=lambda: os.getenv("REDIS_PASSWORD", None)
    )
    redis_db: int = Field(default_factory=lambda: int(os.getenv("REDIS_DB", "0")))
    redis_ssl: bool = Field(
        default_factory=lambda: os.getenv("REDIS_SSL", "false").lower() == "true"
    )

    @property
    def redis_url(self) -> str:
        """URL de conexão do Redis"""
        if self.redis_password:
            auth = f":{self.redis_password}@"
        else:
            auth = ""

        protocol = "rediss" if self.redis_ssl else "redis"
        return f"{protocol}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # =================================
    # CONFIGURAÇÕES DE CACHE
    # =================================

    # Configurações de cache para permissões
    cache_permission_ttl: int = Field(
        default_factory=lambda: int(os.getenv("CACHE_PERMISSION_TTL", "1800"))
    )  # 30 min
    cache_user_session_ttl: int = Field(
        default_factory=lambda: int(os.getenv("CACHE_USER_SESSION_TTL", "3600"))
    )  # 1 hora
    cache_enabled: bool = Field(
        default_factory=lambda: os.getenv("CACHE_ENABLED", "true").lower() == "true"
    )

    @validator("secret_key")
    def validate_jwt_secret(cls, v: str) -> str:
        """Valida se JWT secret tem tamanho adequado para segurança"""
        if len(v) < 32:
            raise ValueError(
                "❌ JWT secret key deve ter pelo menos 32 caracteres para segurança"
            )
        if v == "your-secret-key-here-make-it-very-long-and-random-256-bits":
            raise ValueError(
                "❌ JWT secret key padrão detectado! "
                "Use: python -c 'import secrets; print(secrets.token_hex(32))'"
            )
        return v

    # =================================
    # CONFIGURAÇÕES DE CORS
    # =================================

    allowed_origins: str = Field(
        default_factory=lambda: os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
        )
    )
    allowed_hosts: str = Field(
        default_factory=lambda: os.getenv(
            "ALLOWED_HOSTS", "localhost,127.0.0.1,testserver"
        )
    )
    cors_credentials: bool = Field(default=True, env="CORS_CREDENTIALS")

    @property
    def cors_origins_list(self) -> List[str]:
        """Converte CORS origins string para lista"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    @property
    def allowed_hosts_list(self) -> List[str]:
        """Converte allowed hosts string para lista"""
        return [host.strip() for host in self.allowed_hosts.split(",")]

    # =================================
    # CONFIGURAÇÕES DA API
    # =================================

    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")

    # =================================
    # CONFIGURAÇÕES DE LOGGING
    # =================================

    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json | text

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Valida nível de log"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level deve ser um de: {valid_levels}")
        return v.upper()

    # =================================
    # CONFIGURAÇÕES PAGBANK
    # =================================

    # PagBank API Configuration
    PAGBANK_TOKEN: str = Field(
        default_factory=lambda: os.getenv("PAGBANK_TOKEN", "")
    )
    PAGBANK_WEBHOOK_SECRET: str = Field(
        default_factory=lambda: os.getenv("PAGBANK_WEBHOOK_SECRET", "")
    )
    PAGBANK_ENVIRONMENT: str = Field(
        default_factory=lambda: os.getenv("PAGBANK_ENVIRONMENT", "sandbox")
    )

    # Application URLs for PagBank integration
    BASE_URL: str = Field(
        default_factory=lambda: os.getenv("BASE_URL", "http://192.168.11.83:8000")
    )
    FRONTEND_URL: str = Field(
        default_factory=lambda: os.getenv("FRONTEND_URL", "http://192.168.11.83:3000")
    )

    @validator("PAGBANK_ENVIRONMENT")
    def validate_pagbank_environment(cls, v: str) -> str:
        """Valida ambiente PagBank"""
        valid_environments = ["sandbox", "production"]
        if v.lower() not in valid_environments:
            raise ValueError(f"PAGBANK_ENVIRONMENT deve ser um de: {valid_environments}")
        return v.lower()

    # =================================
    # CONFIGURAÇÕES DE CACHE (Redis)
    # =================================

    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")
    cache_ttl: int = Field(default=300, env="CACHE_TTL")  # 5 minutos

    @property
    def redis_url(self) -> str:
        """Constrói Redis URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # =================================
    # CONFIGURAÇÕES DE SERVIÇOS EXTERNOS
    # =================================

    # ViaCEP
    viacep_base_url: str = Field(
        default="https://viacep.com.br/ws", env="VIACEP_BASE_URL"
    )
    viacep_timeout: int = Field(default=10, env="VIACEP_TIMEOUT")

    # ReceitaWS
    receita_ws_base_url: str = Field(
        default="https://www.receitaws.com.br/v1", env="RECEITA_WS_BASE_URL"
    )
    receita_ws_timeout: int = Field(default=15, env="RECEITA_WS_TIMEOUT")

    # =================================
    # CONFIGURAÇÕES DE EMAIL
    # =================================

    # SMTP Settings
    smtp_host: str = Field(default="192.168.11.64", env="SMTP_HOST")
    smtp_port: int = Field(default=25, env="SMTP_PORT")
    smtp_user: str = Field(default="", env="SMTP_USER")
    smtp_password: str = Field(default="", env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=False, env="SMTP_USE_TLS")
    smtp_use_ssl: bool = Field(default=False, env="SMTP_USE_SSL")
    send_emails: bool = Field(default=True, env="SEND_EMAILS")

    # Frontend URL para links nos emails
    frontend_url: str = Field(default="http://192.168.11.83:3000", env="FRONTEND_URL")

    # =================================
    # VALIDAÇÕES EXTRAS
    # =================================

    @validator("environment")
    def validate_environment(cls, v: str) -> str:
        """Valida ambiente válido"""
        valid_envs = ["development", "testing", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"Environment deve ser um de: {valid_envs}")
        return v

    @property
    def is_development(self) -> bool:
        """Check se está em desenvolvimento"""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check se está em produção"""
        return self.environment == "production"

    # =================================
    # CONFIGURAÇÃO DO PYDANTIC
    # =================================

    model_config = {
        "case_sensitive": False,
        "use_enum_values": True,
        "extra": "ignore",  # ✅ Ignora campos extras do .env
    }


def generate_secure_jwt_secret() -> str:
    """
    ✅ Gera JWT secret seguro de 256 bits (64 chars hex)
    Use: python -c "from config.settings import generate_secure_jwt_secret; print(generate_secure_jwt_secret())"
    """
    return secrets.token_hex(32)


@lru_cache()
def get_settings() -> Settings:
    """
    Instância singleton das configurações
    Cache para evitar reprocessamento
    """
    return Settings()


# Instância global das configurações
settings = get_settings()
