from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer, CrossEncoder

from app.config import settings
from app.data.known_cves import KNOWN_CVES
from app.ingest import COLLECTION_NAME


def main():
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    reranker = CrossEncoder("BAAI/bge-reranker-base")
    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

    hits_at_1 = 0
    hits_at_3 = 0
    total = len(KNOWN_CVES)

    for entry in KNOWN_CVES:
        question = entry["question"]
        expected_cve = entry["cve_id"]

        # Stage 1: retrieve ALL documents (corpus is small, no reason to truncate)
        query_vector = embed_model.encode(question).tolist()
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=len(KNOWN_CVES),
        ).points

        # Stage 2: rerank the full set
        pairs = [(question, r.payload["description"]) for r in results]
        scores = reranker.predict(pairs)

        reranked = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
        retrieved_ids = [r.payload["cve_id"] for r, _ in reranked][:3]

        top1_correct = retrieved_ids[0] == expected_cve if retrieved_ids else False
        top3_correct = expected_cve in retrieved_ids

        hits_at_1 += int(top1_correct)
        hits_at_3 += int(top3_correct)

        status = "OK " if top1_correct else "MISS"
        print(f"[{status}] Expected {expected_cve}, got {retrieved_ids}")

    print(f"\nHit-rate@1 (reranked): {hits_at_1}/{total} = {hits_at_1/total:.1%}")
    print(f"Hit-rate@3 (reranked): {hits_at_3}/{total} = {hits_at_3/total:.1%}")


if __name__ == "__main__":
    main()