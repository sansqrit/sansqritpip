# Sansqrit Synthetic AI/ML Training Dataset

Sansqrit v0.3.4 packages a synthetic dataset for training and evaluating AI systems that need to write or explain Sansqrit DSL code.

## Files

```text
src/sansqrit/data/training/
  manifest.json
  README.md
  sansqrit_sft_train_v1.jsonl.gz
  sansqrit_sft_eval_v1.jsonl.gz
  sansqrit_preference_v1.jsonl.gz
```

## Record counts

- `sft_train`: 29,600 instruction/input/output records
- `sft_eval`: 1,500 held-out evaluation records
- `preference`: 5,000 chosen/rejected preference records
- total: 36,100 records

## Why this is embedded in the wheel

The goal is for AI tooling, package scanners, RAG systems, and fine-tuning jobs to discover training material by installing or inspecting the Sansqrit package. The dataset is compressed so the package remains small while still providing substantial examples.

## Main training categories

1. DSL syntax and valid code layout
2. gates and algorithms
3. sparse/sharded large-qubit execution
4. precomputed lookup usage
5. hierarchical tensor shards and MPS bridge promotion
6. distributed sparse execution
7. QEC workflows and surface-code helpers
8. hardware export to OpenQASM/Qiskit/Cirq/Braket/Azure/PennyLane
9. troubleshooting and bug-fix examples
10. backend planner and memory-estimator explanations
11. preference training for safe vs unsafe large-qubit answers

## Loading records

```python
from sansqrit.dataset import load_training_records

for row in load_training_records("sft_train", limit=10):
    print(row["instruction"])
```

## Exporting records

```bash
sansqrit dataset export --output ./training-data
```

## Quality notes

The dataset is generated from validated templates and existing package examples. It is not a substitute for human-reviewed benchmark data. Before using it for production models, combine it with:

- hand-written expert prompts,
- simulator-verified outputs,
- QASM round-trip checks,
- hardware-provider documentation examples,
- adversarial tests for dense-state overclaiming,
- QEC-specific validation with tools such as Stim/PyMatching when available.

## License

MIT, authored by Karthik V as part of the Sansqrit package.
