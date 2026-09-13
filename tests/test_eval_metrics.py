def calculate_hit_rate_at_k(results: list[tuple[str, list[str]]], k: int) -> float:
    """Given (expected_cve, retrieved_cve_ids) pairs, compute hit-rate@k."""
    hits = 0
    for expected, retrieved in results:
        if expected in retrieved[:k]:
            hits += 1
    return hits / len(results)


def test_hit_rate_at_1_perfect_score():
    results = [
        ("CVE-A", ["CVE-A", "CVE-B", "CVE-C"]),
        ("CVE-B", ["CVE-B", "CVE-A", "CVE-D"]),
    ]
    assert calculate_hit_rate_at_k(results, k=1) == 1.0


def test_hit_rate_at_1_partial_score():
    results = [
        ("CVE-A", ["CVE-B", "CVE-A", "CVE-C"]),  # correct answer at position 2, not 1
        ("CVE-B", ["CVE-B", "CVE-A", "CVE-D"]),  # correct at position 1
    ]
    assert calculate_hit_rate_at_k(results, k=1) == 0.5


def test_hit_rate_at_3_more_forgiving_than_at_1():
    results = [
        ("CVE-A", ["CVE-B", "CVE-C", "CVE-A"]),  # correct answer at position 3
    ]
    assert calculate_hit_rate_at_k(results, k=1) == 0.0
    assert calculate_hit_rate_at_k(results, k=3) == 1.0