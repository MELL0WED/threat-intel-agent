import json
import time

import requests

from app.config import settings

INPUT_FILE = "app/data/classifier_train_subset.jsonl"
OUTPUT_FILE = "app/data/classifier_train_subset_soft_labels.jsonl"

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "openai/gpt-oss-120b"

SYSTEM_PROMPT = """You are a security severity classifier. Given a CVE description, \
estimate the probability that its severity is MEDIUM, HIGH, or CRITICAL.

Respond with ONLY a JSON object in this exact format, with probabilities summing to 1.0:
{"MEDIUM": 0.X, "HIGH": 0.X, "CRITICAL": 0.X}
No other text."""


def score_one(description: str) -> dict:
    response = requests.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {settings.groq_api_key}"},
        json={
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": description},
            ],
            "temperature": 0.0,
        },
        timeout=30,
    )
    if response.status_code != 200:
        print(f"Groq returned {response.status_code}: {response.text}")
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"].strip()
    content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    probs = json.loads(content)
    return probs


def main():
    records = []
    with open(INPUT_FILE) as f:
        for line in f:
            records.append(json.loads(line))

    results = []
    for i, record in enumerate(records):
        print(f"Scoring {i+1}/{len(records)}: {record['cve_id']}...")
        try:
            soft_labels = score_one(record["description"])
            record["soft_labels"] = soft_labels
            results.append(record)
        except Exception as e:
            print(f"  Failed on {record['cve_id']}: {e}")
        time.sleep(2.0)

    with open(OUTPUT_FILE, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    print(f"\nScored {len(results)}/{len(records)} examples. Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()