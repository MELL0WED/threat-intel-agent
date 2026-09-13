from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    redis_host: str = "localhost"
    redis_port: int = 6379
    openai_api_key: str = ""
    nvd_api_key: str = "B6014940-311B-4E14-8D27-5C9969F78D2D"

    class Config:
        env_file = ".env"


settings = Settings()