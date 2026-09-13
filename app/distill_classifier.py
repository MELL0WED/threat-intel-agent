import json

import numpy as np
import torch
import torch.nn.functional as F
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

MODEL_NAME = "distilbert-base-uncased"
SOFT_LABELS_FILE = "app/data/classifier_train_subset_soft_labels.jsonl"
TEST_FILE = "app/data/classifier_test.jsonl"


class CVEDatasetWithSoftLabels(Dataset):
    """Same as the baseline dataset, but also carries the teacher's soft-label probabilities."""

    def __init__(self, filepath, tokenizer, max_length=256):
        self.examples = []
        with open(filepath) as f:
            for line in f:
                self.examples.append(json.loads(line))
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

        # Soft label vector, e.g. [0.2, 0.7, 0.1] for [MEDIUM, HIGH, CRITICAL]
        soft = record.get("soft_labels")
        if soft:
            item["soft_labels"] = torch.tensor([soft[label] for label in LABELS])
        else:
            item["soft_labels"] = torch.zeros(len(LABELS))  # unused for the control run
        return item


class DistillationTrainer(Trainer):
    """Same as a normal Trainer, except the loss is: hard-label loss + soft-label loss."""

    def __init__(self, *args, use_distillation=True, alpha=0.5, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_distillation = use_distillation
        self.alpha = alpha  # how much weight to give the soft-label loss vs. the hard-label loss

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        soft_labels = inputs.pop("soft_labels")
        labels = inputs["labels"]
        outputs = model(**{k: v for k, v in inputs.items() if k != "labels"})
        logits = outputs.logits

        hard_loss = F.cross_entropy(logits, labels)

        if self.use_distillation:
            student_log_probs = F.log_softmax(logits, dim=-1)
            soft_loss = F.kl_div(student_log_probs, soft_labels, reduction="batchmean")
            loss = (1 - self.alpha) * hard_loss + self.alpha * soft_loss
        else:
            loss = hard_loss

        return (loss, outputs) if return_outputs else loss


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


def train_one(use_distillation: bool, run_name: str):
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=len(LABELS))

    train_dataset = CVEDatasetWithSoftLabels(SOFT_LABELS_FILE, tokenizer)
    test_dataset = CVEDatasetWithSoftLabels(TEST_FILE, tokenizer)

    training_args = TrainingArguments(
        output_dir=f"app/models/{run_name}",
        num_train_epochs=4,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        eval_strategy="epoch",
        save_strategy="no",
        fp16=torch.cuda.is_available(),
        remove_unused_columns=False,
    )

    trainer = DistillationTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=compute_metrics,
        use_distillation=use_distillation,
    )

    trainer.train()

    print(f"\n=== Final evaluation: {run_name} ===")
    results = trainer.evaluate()
    for k, v in results.items():
        print(f"{k}: {v}")
    return results


def main():
    control_results = train_one(use_distillation=False, run_name="control_hard_labels_only")
    distilled_results = train_one(use_distillation=True, run_name="distilled_with_kd")

    print("\n=== Comparison ===")
    print(f"Control (hard labels only)  - Macro F1: {control_results['eval_f1_macro']:.4f}")
    print(f"Distilled (hard + KD loss)  - Macro F1: {distilled_results['eval_f1_macro']:.4f}")


if __name__ == "__main__":
    main()