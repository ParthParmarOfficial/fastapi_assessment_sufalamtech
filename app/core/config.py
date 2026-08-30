from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    WEBHOOK_SECRET: str = "super-secret-key"
    APP_ENV: str = "development"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
