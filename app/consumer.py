import json
import time
from kafka import KafkaConsumer
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.ingest import fetch_cve_description, cve_to_point_id, COLLECTION_NAME

consumer = KafkaConsumer(
    "cve-advisories",
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="earliest",
)

model = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

print("Consumer listening for new advisories...")
for message in consumer:
    cve_id = message.value["cve_id"]
    print(f"Consumed {cve_id}, fetching + embedding...")
    description = fetch_cve_description(cve_id)
    vector = model.encode(description).tolist()

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[{"id": cve_to_point_id(cve_id), "vector": vector,
                 "payload": {"cve_id": cve_id, "description": description}}],
    )
    print(f"Ingested {cve_id}")
    time.sleep(6)