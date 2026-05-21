from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration, overridable via environment variables."""

    model_config = SettingsConfigDict(case_sensitive=False)

    prediction_db_url: str = (
        "postgresql+psycopg://prediction:prediction@prediction-db:5432/prediction"
    )

    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"

    admin_api_key: str = "dev-admin-key-change-me"

    jwt_secret: str = "dev-jwt-secret-change-me"
    jwt_ttl_hours: int = 24

    fixture_service_url: str = "http://fixture-service:8000"

    lock_offset_minutes: int = 15
    fixture_sync_minutes: int = 10
    lock_poll_seconds: int = 30

    # Built-in account seeded on startup.
    seed_admin_username: str = "admin"
    seed_admin_password: str = "Internet@123"

    # Shared default pool; every newly registered user joins it automatically.
    default_pool_id: str = "grp-default-pool"
    default_pool_name: str = "World Cup 2026 — Default Pool"


settings = Settings()
