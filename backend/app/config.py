from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./coffeerun.db"
    admin_email: str = "admin@example.com"
    resend_api_key: str = ""
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_expiry_days: int = 7
    magic_link_expiry_minutes: int = 15
    frontend_url: str = "http://localhost:5173"
    sentry_dsn: str = ""
    environment: str = "development"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
