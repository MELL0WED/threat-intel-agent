import json
import random

INPUT_FILE = "app/data/classifier_train.jsonl"
OUTPUT_FILE = "app/data/classifier_train_subset.jsonl"
SUBSET_SIZE = 250

random.seed(42)


def main():
    records = []
    with open(INPUT_FILE) as f:
        for line in f:
            records.append(json.loads(line))

    subset = random.sample(records, SUBSET_SIZE)

    with open(OUTPUT_FILE, "w") as f:
        for r in subset:
            f.write(json.dumps(r) + "\n")

    print(f"Sampled {len(subset)} examples to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()