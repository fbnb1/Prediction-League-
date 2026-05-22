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

    # --- The Odds API (real football data provider) ---
    # When odds_api_key is set, TheOddsApiProvider is used; otherwise the
    # service falls back to the bundled MockFixtureProvider.
    odds_api_key: str = ""
    odds_api_base: str = "https://api.the-odds-api.com"
    # Comma-separated sport keys (e.g. "soccer_fifa_world_cup").
    # Empty -> auto-discover every in-season soccer competition. Discovery is
    # convenient but expensive (one paid request per competition on every
    # refresh) -- pin a single key for a quota-friendly deployment.
    odds_api_sports: str = ""

    # --- API-quota budgeting (free tier = 500 requests / month) ---
    # Each odds request costs 2 (markets x regions); each scores request 2.
    # 0 disables the periodic odds-refresh job (odds are pulled once at seed
    # time). For a whole-tournament run set e.g. 1440 (once a day) -> ~2/day.
    odds_refresh_minutes: int = 0
    # How often to poll for finished-match scores. The poll only spends quota
    # when a match actually kicked off > 1h ago, so quiet days cost nothing.
    results_poll_minutes: int = 720
    # Hard stop: once the provider reports fewer than this many requests left
    # for the month, no further API calls are made (cached data is served).
    odds_api_min_quota: int = 25
    outbox_poll_seconds: int = 5

    # Minutes before kickoff that picks lock (kept in sync with prediction).
    lock_offset_minutes: int = 15


settings = Settings()
