import time
import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.data.known_cves import KNOWN_CVES

NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
COLLECTION_NAME = "cve_advisories"


def fetch_cve_description(cve_id: str) -> str:
    resp = requests.get(NVD_URL, params={"cveId": cve_id}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    vulns = data.get("vulnerabilities", [])
    if not vulns:
        raise ValueError(f"No data returned for {cve_id}")
    descriptions = vulns[0]["cve"]["descriptions"]
    for d in descriptions:
        if d["lang"] == "en":
            return d["value"]
    return descriptions[0]["value"]


def main():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    points = []
    for i, entry in enumerate(KNOWN_CVES):
        cve_id = entry["cve_id"]
        print(f"Fetching {cve_id}...")
        description = fetch_cve_description(cve_id)
        vector = model.encode(description).tolist()

        points.append(
            PointStruct(
                id=i,
                vector=vector,
                payload={"cve_id": cve_id, "description": description},
            )
        )
        time.sleep(6)  # stay under NVD's public rate limit (5 requests / 30s)

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Ingested {len(points)} CVEs into Qdrant.")


if __name__ == "__main__":
    main()