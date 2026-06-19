from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ai_mode: str = "mock"
    ai_model: str = "mock"
    database_url: str = "sqlite:///./tickets.db"
    dataset_path: str = "./dataset/tickets.csv"
    auto_ingest_on_start: bool = True

    anthropic_api_key: str = ""
    groq_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
