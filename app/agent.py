from typing import TypedDict

import torch
import requests
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from langgraph.graph import StateGraph, END
import hashlib
import json

import redis

from app.config import settings
from app.ingest import COLLECTION_NAME

LABELS = ["MEDIUM", "HIGH", "CRITICAL"]
CLASSIFIER_PATH = "app/models/severity_classifier_final"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

class AgentState(TypedDict):
    question: str
    cve_id: str
    description: str
    severity: str
    escalate: bool
    answer: str
    _cache_hit: bool

embed_model = SentenceTransformer("all-MiniLM-L6-v2")
qdrant_client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

classifier_tokenizer = AutoTokenizer.from_pretrained(CLASSIFIER_PATH)
classifier_model = AutoModelForSequenceClassification.from_pretrained(CLASSIFIER_PATH)


def retrieve_node(state: AgentState) -> AgentState:
    query_vector = embed_model.encode(state["question"]).tolist()
    results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=1,
    ).points
    top = results[0]
    state["cve_id"] = top.payload["cve_id"]
    state["description"] = top.payload["description"]
    return state


def classify_node(state: AgentState) -> AgentState:
    inputs = classifier_tokenizer(
        state["description"], truncation=True, padding=True, max_length=256, return_tensors="pt"
    )
    with torch.no_grad():
        logits = classifier_model(**inputs).logits
    predicted_id = logits.argmax(dim=-1).item()
    state["severity"] = LABELS[predicted_id]
    state["escalate"] = state["severity"] == "CRITICAL"
    return state


def generate_node(state: AgentState) -> AgentState:
    escalation_note = (
        "\n\nNOTE: This is CRITICAL severity — flag for immediate security team review."
        if state["escalate"] else ""
    )
    prompt = (
        f"Question: {state['question']}\n\n"
        f"Relevant CVE: {state['cve_id']}\n"
        f"Description: {state['description']}\n"
        f"Severity: {state['severity']}\n\n"
        f"Answer the question using this information, in 2-3 sentences."
    )
    response = requests.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {settings.groq_api_key}"},
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        },
        timeout=30,
    )
    response.raise_for_status()
    answer = response.json()["choices"][0]["message"]["content"].strip()
    state["answer"] = answer + escalation_note
    return state

def route_after_cache(state: AgentState) -> str:
    return END if state["_cache_hit"] else "retrieve"


def build_agent():
    graph = StateGraph(AgentState)
    graph.add_node("cache_lookup", cache_lookup_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("classify", classify_node)
    graph.add_node("generate", generate_node)
    graph.add_node("cache_store", cache_store_node)

    graph.set_entry_point("cache_lookup")
    graph.add_conditional_edges("cache_lookup", route_after_cache, {"retrieve": "retrieve", END: END})
    graph.add_edge("retrieve", "classify")
    graph.add_edge("classify", "generate")
    graph.add_edge("generate", "cache_store")
    graph.add_edge("cache_store", END)

    return graph.compile()

redis_client = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)

CACHE_SIMILARITY_THRESHOLD = 0.95  # how close a new question must be to a cached one to count as "the same"


def cache_lookup_node(state: AgentState) -> AgentState:
    query_vector = embed_model.encode(state["question"]).tolist()

    # Check against all cached question embeddings stored in Redis
    cached_keys = redis_client.keys("cache:*")
    for key in cached_keys:
        cached_entry = json.loads(redis_client.get(key))
        cached_vector = cached_entry["embedding"]
        similarity = _cosine_similarity(query_vector, cached_vector)
        if similarity >= CACHE_SIMILARITY_THRESHOLD:
            state["cve_id"] = cached_entry["cve_id"]
            state["severity"] = cached_entry["severity"]
            state["escalate"] = cached_entry["escalate"]
            state["answer"] = cached_entry["answer"] + "\n[from cache]"
            state["_cache_hit"] = True
            return state

    state["_cache_hit"] = False
    return state


def _cosine_similarity(a, b):
    import numpy as np
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def cache_store_node(state: AgentState) -> AgentState:
    query_vector = embed_model.encode(state["question"]).tolist()
    cache_key = f"cache:{hashlib.md5(state['question'].encode()).hexdigest()}"
    redis_client.set(
        cache_key,
        json.dumps({
            "embedding": query_vector,
            "cve_id": state["cve_id"],
            "severity": state["severity"],
            "escalate": state["escalate"],
            "answer": state["answer"],
        }),
        ex=3600,  # cache expires after 1 hour
    )
    return state

if __name__ == "__main__":
    agent = build_agent()
    result = agent.invoke({"question": "What vulnerability let attackers run code remotely through a Java logging library?"})
    print(f"CVE: {result['cve_id']}")
    print(f"Severity: {result['severity']}")
    print(f"Escalate: {result['escalate']}")
    print(f"\nAnswer:\n{result['answer']}")