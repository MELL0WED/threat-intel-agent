from testcontainers.community.qdrant import QdrantContainer
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.ingest import cve_to_point_id


def test_point_id_is_deterministic():
    id1 = cve_to_point_id("CVE-2021-44228")
    id2 = cve_to_point_id("CVE-2021-44228")
    assert id1 == id2


def test_different_cves_get_different_ids():
    id1 = cve_to_point_id("CVE-2021-44228")
    id2 = cve_to_point_id("CVE-2014-0160")
    assert id1 != id2


def test_duplicate_ingestion_does_not_create_duplicates():
    with QdrantContainer() as qdrant:
        client = qdrant.get_client()
        client.recreate_collection(
            collection_name="test_collection",
            vectors_config=VectorParams(size=4, distance=Distance.COSINE),
        )

        fake_vector = [0.1, 0.2, 0.3, 0.4]
        point_id = cve_to_point_id("CVE-2021-44228")

        client.upsert(
            collection_name="test_collection",
            points=[PointStruct(id=point_id, vector=fake_vector, payload={"cve_id": "CVE-2021-44228"})],
        )
        client.upsert(
            collection_name="test_collection",
            points=[PointStruct(id=point_id, vector=fake_vector, payload={"cve_id": "CVE-2021-44228"})],
        )

        count = client.count(collection_name="test_collection").count
        assert count == 1