import json
import time
from datetime import datetime, timedelta

import requests

from app.config import settings

NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
OUTPUT_FILE = "app/data/classifier_dataset.jsonl"


def fetch_cve_batch(start_date: str, end_date: str, start_index: int, results_per_page: int = 200) -> dict:
    headers = {"apiKey": settings.nvd_api_key} if settings.nvd_api_key else {}
    params = {
        "pubStartDate": start_date,
        "pubEndDate": end_date,
        "resultsPerPage": results_per_page,
        "startIndex": start_index,
    }
    resp = requests.get(NVD_URL, params=params, headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"NVD returned {resp.status_code}: {resp.text}")
    resp.raise_for_status()
    return resp.json()


def extract_severity(cve_entry: dict) -> str | None:
    metrics = cve_entry.get("metrics", {})
    for version_key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        if version_key in metrics:
            return metrics[version_key][0]["cvssData"].get(
                "baseSeverity"
            ) or metrics[version_key][0].get("baseSeverity")
    return None


def extract_description(cve_entry: dict) -> str | None:
    for d in cve_entry.get("descriptions", []):
        if d["lang"] == "en":
            return d["value"]
    return None


def daterange_windows(start: datetime, end: datetime, window_days: int = 119):
    """Yield (window_start, window_end) pairs, each <= window_days apart."""
    current = start
    while current < end:
        window_end = min(current + timedelta(days=window_days), end)
        yield current, window_end
        current = window_end


def main():
    all_records = []
    target_count = 800  # aim a bit above 500 to allow for filtered-out incomplete records

    overall_start = datetime(2021, 1, 1)
    overall_end = datetime(2023, 12, 31)

    for window_start, window_end in daterange_windows(overall_start, overall_end):
        if len(all_records) >= target_count:
            break

        start_str = window_start.strftime("%Y-%m-%dT%H:%M:%S.000")
        end_str = window_end.strftime("%Y-%m-%dT%H:%M:%S.999")
        print(f"Window {start_str} to {end_str}")

        start_index = 0
        while len(all_records) < target_count:
            print(f"  Fetching batch at index {start_index}...")
            data = fetch_cve_batch(start_str, end_str, start_index)
            vulns = data.get("vulnerabilities", [])
            total_results = data.get("totalResults", 0)

            if not vulns:
                break

            for entry in vulns:
                cve = entry["cve"]
                severity = extract_severity(cve)
                description = extract_description(cve)
                if severity and description:
                    all_records.append({
                        "cve_id": cve["id"],
                        "description": description,
                        "severity": severity,
                    })

            start_index += 200
            time.sleep(0.6)

            if start_index >= total_results:
                break  # exhausted this window

    print(f"Collected {len(all_records)} labeled CVEs.")
    with open(OUTPUT_FILE, "w") as f:
        for record in all_records:
            f.write(json.dumps(record) + "\n")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()