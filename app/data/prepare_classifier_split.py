import json
from sklearn.model_selection import train_test_split

INPUT_FILE = "app/data/classifier_dataset.jsonl"
TRAIN_FILE = "app/data/classifier_train.jsonl"
TEST_FILE = "app/data/classifier_test.jsonl"

# LOW merged into MEDIUM due to severe class imbalance (12/979 examples — too few
# to train or evaluate reliably even with stratified splitting).
SEVERITY_MERGE_MAP = {
    "LOW": "MEDIUM",
    "MEDIUM": "MEDIUM",
    "HIGH": "HIGH",
    "CRITICAL": "CRITICAL",
}
LABELS = ["MEDIUM", "HIGH", "CRITICAL"]


def main():
    records = []
    with open(INPUT_FILE) as f:
        for line in f:
            record = json.loads(line)
            record["severity"] = SEVERITY_MERGE_MAP[record["severity"]]
            records.append(record)

    labels = [r["severity"] for r in records]

    train, test = train_test_split(
        records,
        test_size=0.2,
        stratify=labels,
        random_state=42,
    )

    with open(TRAIN_FILE, "w") as f:
        for r in train:
            f.write(json.dumps(r) + "\n")
    with open(TEST_FILE, "w") as f:
        for r in test:
            f.write(json.dumps(r) + "\n")

    print(f"Train: {len(train)} examples, Test: {len(test)} examples")


if __name__ == "__main__":
    main()