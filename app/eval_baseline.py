from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.data.known_cves import KNOWN_CVES
from app.ingest import COLLECTION_NAME


def main():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

    hits_at_1 = 0
    hits_at_3 = 0
    total = len(KNOWN_CVES)

    for entry in KNOWN_CVES:
        question = entry["question"]
        expected_cve = entry["cve_id"]

        query_vector = model.encode(question).tolist()
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=3,
        ).points
        retrieved_ids = [r.payload["cve_id"] for r in results]

        top1_correct = retrieved_ids[0] == expected_cve if retrieved_ids else False
        top3_correct = expected_cve in retrieved_ids

        hits_at_1 += int(top1_correct)
        hits_at_3 += int(top3_correct)

        status = "✓" if top1_correct else "✗"
        print(f"{status} Expected {expected_cve}, got {retrieved_ids}")

    print(f"\nHit-rate@1: {hits_at_1}/{total} = {hits_at_1/total:.1%}")
    print(f"Hit-rate@3: {hits_at_3}/{total} = {hits_at_3/total:.1%}")


if __name__ == "__main__":
    main()