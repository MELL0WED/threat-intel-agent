from fastapi import FastAPI
from pydantic import BaseModel

from app.config import settings
from app.agent import build_agent

app = FastAPI(title="Security Threat-Intel Agent")

agent = build_agent()


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "qdrant_target": f"{settings.qdrant_host}:{settings.qdrant_port}",
        "redis_target": f"{settings.redis_host}:{settings.redis_port}",
    }


class QueryRequest(BaseModel):
    question: str


@app.post("/query")
def query(request: QueryRequest):
    result = agent.invoke({"question": request.question})
    return {
        "cve_id": result["cve_id"],
        "severity": result["severity"],
        "escalate": result["escalate"],
        "answer": result["answer"],
    }