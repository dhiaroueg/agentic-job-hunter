from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./jobhunter.db"
    EMAIL_SENDER: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_RECEIVER: str = ""
    MODEL_NAME: str = "gpt-4.1-mini"
    CV_PATH: str = "data/cv.pdf"
    JOBS_FILE: str = "data/jobs.json"
    REPORT_DIR: str = "reports"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USE_TLS: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
