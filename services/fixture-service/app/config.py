from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration, overridable via environment variables."""

    model_config = SettingsConfigDict(case_sensitive=False)

    fixture_db_url: str = "postgresql+psycopg://fixture:fixture@fixture-db:5432/fixture"

    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"

    admin_api_key: str = "dev-admin-key-change-me"

    odds_refresh_minutes: int = 15
    outbox_poll_seconds: int = 5


settings = Settings()
