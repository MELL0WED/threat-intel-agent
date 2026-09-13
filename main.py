from fastapi import FastAPI

from app.config import settings

app = FastAPI(title="Security Threat-Intel Agent")


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "qdrant_target": f"{settings.qdrant_host}:{settings.qdrant_port}",
        "redis_target": f"{settings.redis_host}:{settings.redis_port}",
    }