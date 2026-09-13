import json

import numpy as np
import torch
from sklearn.metrics import classification_report
from torch.utils.data import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)

LABELS = ["MEDIUM", "HIGH", "CRITICAL"]
LABEL_TO_ID = {label: i for i, label in enumerate(LABELS)}
ID_TO_LABEL = {i: label for label, i in LABEL_TO_ID.items()}

MODEL_NAME = "distilbert-base-uncased"


class CVEDataset(Dataset):
    def __init__(self, filepath, tokenizer, max_length=256):
        self.examples = []
        with open(filepath) as f:
            for line in f:
                record = json.loads(line)
                self.examples.append(record)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        record = self.examples[idx]
        encoding = self.tokenizer(
            record["description"],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        item = {k: v.squeeze(0) for k, v in encoding.items()}
        item["labels"] = torch.tensor(LABEL_TO_ID[record["severity"]])
        return item


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    report = classification_report(
        labels, predictions, target_names=LABELS, output_dict=True, zero_division=0
    )
    return {
        "accuracy": report["accuracy"],
        "f1_medium": report["MEDIUM"]["f1-score"],
        "f1_high": report["HIGH"]["f1-score"],
        "f1_critical": report["CRITICAL"]["f1-score"],
        "f1_macro": report["macro avg"]["f1-score"],
    }


def main():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=len(LABELS)
    )

    train_dataset = CVEDataset("app/data/classifier_train.jsonl", tokenizer)
    test_dataset = CVEDataset("app/data/classifier_test.jsonl", tokenizer)

    training_args = TrainingArguments(
        output_dir="app/models/severity_classifier",
        num_train_epochs=4,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        fp16=torch.cuda.is_available(),  # use your GPU's mixed-precision if available
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=compute_metrics,
    )

    trainer.train()

    print("\nFinal evaluation on test set:")
    results = trainer.evaluate()
    for k, v in results.items():
        print(f"{k}: {v}")

    trainer.save_model("app/models/severity_classifier_final")


if __name__ == "__main__":
    main()