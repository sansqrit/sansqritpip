# Sansqrit Synthetic Training Dataset

Packaged compressed JSONL datasets for AI/ML training on Sansqrit DSL.

## Manifest
```json
{
  "dataset": "sansqrit-synthetic-training-v1",
  "author": "Karthik V",
  "license": "MIT",
  "created_utc": "2026-04-26T12:28:31.200136+00:00",
  "description": "Extensive synthetic instruction, code, explanation, troubleshooting, QEC, hardware-export and preference dataset for training AI models to understand and generate Sansqrit quantum DSL programs.",
  "files": [
    {
      "name": "sansqrit_sft_train_v1.jsonl.gz",
      "schema": "instruction-input-output-v1",
      "records": 29600
    },
    {
      "name": "sansqrit_sft_eval_v1.jsonl.gz",
      "schema": "instruction-input-output-v1",
      "records": 1500
    },
    {
      "name": "sansqrit_preference_v1.jsonl.gz",
      "schema": "preference-v1",
      "records": 5000
    }
  ],
  "total_records": 36100,
  "topics": [
    "DSL syntax",
    "gates",
    "circuits",
    "algorithms",
    "large qubit sparse/sharded execution",
    "hierarchical tensor shards",
    "precomputed lookups",
    "distributed computing",
    "QEC",
    "surface codes",
    "hardware exports",
    "QASM",
    "troubleshooting",
    "backend selection",
    "bug fixing",
    "preference training",
    "DSL to Python",
    "safe dense-state warnings"
  ],
  "schemas": {
    "instruction-input-output-v1": {
      "fields": [
        "id",
        "dataset",
        "schema",
        "language",
        "task_type",
        "instruction",
        "input",
        "output",
        "tags",
        "difficulty",
        "split",
        "source",
        "author",
        "license",
        "quality_notes"
      ]
    },
    "preference-v1": {
      "fields": [
        "id",
        "dataset",
        "schema",
        "language",
        "prompt",
        "chosen",
        "rejected",
        "tags",
        "split",
        "source",
        "author",
        "license",
        "quality_notes"
      ]
    }
  },
  "intended_use": "Fine-tuning, supervised instruction tuning, DPO/preference training, retrieval-augmented generation, evaluation, prompt engineering and documentation-aware AI model training for Sansqrit DSL.",
  "limitations": "Synthetic data is generated from templates and package examples. It should be supplemented with human-reviewed traces and verified circuit outputs before safety-critical use."
}
```

## Usage
```python
from sansqrit.dataset import dataset_info, load_training_records
print(dataset_info())
for row in load_training_records("sft_train", limit=3):
    print(row["instruction"])
```

## Real-world scenario corpus v1

This release embeds `sansqrit_real_world_scenarios_v1.jsonl.gz`, a 500-record high-quality synthetic corpus by Karthik V. Each record contains a practical scenario question, a backend-selection answer, and runnable Sansqrit code. The scenarios cover climate, smart grid, finance, cybersecurity, logistics, quantum networking, PQC migration, QEC, hardware export, chemistry/materials/QML patterns, and 120+ qubit sparse or tensor-network workflows.

Records are intentionally written to teach AI models when to choose sparse/sharded, hierarchical tensor shards, MPS, stabilizer, QEC, hardware export, lookup profiling, or safe dense-state rejection.
