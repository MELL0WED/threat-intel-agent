from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    redis_host: str = "localhost"
    redis_port: int = 6379
    openai_api_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()