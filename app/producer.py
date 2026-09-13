import json
import time
from kafka import KafkaProducer

from app.data.known_cves import KNOWN_CVES

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

for entry in KNOWN_CVES:
    producer.send("cve-advisories", {"cve_id": entry["cve_id"]})
    print(f"Published {entry['cve_id']}")
    time.sleep(0.5)

producer.flush()