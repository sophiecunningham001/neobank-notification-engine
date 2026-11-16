from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Neon Bank Credit Union Sandbox"
    app_env: str = "development"
    database_url: str = "sqlite:///./neon_bank.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_issuer: str = "neon-bank"
    access_token_minutes: int = 360
    sandbox_mode: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
