from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration, overridable via environment variables."""

    model_config = SettingsConfigDict(case_sensitive=False)

    # Shared with prediction-service so the BFF can verify JWTs without a
    # round-trip back to it.
    jwt_secret: str = "dev-jwt-secret-change-me"

    prediction_url: str = "http://prediction-service:8000"
    fixture_url: str = "http://fixture-service:8000"
    ledger_url: str = "http://ledger-service:8080"

    # Forwarded to the ledger admin API when proxying deposit writes.
    admin_api_key: str = "dev-admin-key-change-me"

    http_timeout_seconds: float = 10.0


settings = Settings()
