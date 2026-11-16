from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Neon Bank API"
    app_env: str = "development"
    database_url: str = "sqlite:///./neon_local.db"
    jwt_secret: str = "UNSAFE_LOCAL_ONLY_REPLACE_ME"
    jwt_issuer: str = "neon-bank-local"
    access_token_minutes: int = 30
    cors_origins: str = "http://localhost:3000"
    sandbox_mode: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self):
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]


settings = Settings()
