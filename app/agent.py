from typing import TypedDict

import torch
import requests
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from langgraph.graph import StateGraph, END

from app.config import settings
from app.ingest import COLLECTION_NAME

LABELS = ["MEDIUM", "HIGH", "CRITICAL"]
CLASSIFIER_PATH = "app/models/severity_classifier_final"
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"


class AgentState(TypedDict):
    question: str
    cve_id: str
    description: str
    severity: str
    escalate: bool
    answer: str


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
        LM_STUDIO_URL,
        json={
            "model": "meta-llama-3-8b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        },
        timeout=60,
    )
    response.raise_for_status()
    answer = response.json()["choices"][0]["message"]["content"].strip()
    state["answer"] = answer + escalation_note
    return state


def build_agent():
    graph = StateGraph(AgentState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("classify", classify_node)
    graph.add_node("generate", generate_node)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "classify")
    graph.add_edge("classify", "generate")
    graph.add_edge("generate", END)

    return graph.compile()


if __name__ == "__main__":
    agent = build_agent()
    result = agent.invoke({"question": "What vulnerability let attackers run code remotely through a Java logging library?"})
    print(f"CVE: {result['cve_id']}")
    print(f"Severity: {result['severity']}")
    print(f"Escalate: {result['escalate']}")
    print(f"\nAnswer:\n{result['answer']}")