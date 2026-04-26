# Sansqrit Real-World Scenario Corpus v1

Author: **Karthik V**

Version: **0.3.4** package data extension

This document describes the embedded 500-record real-world scenario corpus for training AI models to write Sansqrit code from user prompts. Each scenario contains a natural-language question, an answer/explanation, a complete Sansqrit program, backend-selection notes, qubit count, and tags.

## Research-aligned scenario categories

- Hybrid quantum algorithms for chemistry, optimization, and machine learning.
- Backend selection patterns: sparse/sharded, stabilizer, matrix-product-state/tensor-network, density/noise, GPU/cloud exports, and QEC.
- QEC/surface-code workflows, syndrome extraction, and decoder interfaces.
- Hardware/cloud export workflows for IBM/Qiskit, AWS Braket, Azure Quantum, Cirq, PennyLane, and OpenQASM.
- Safe large-qubit teaching: 120+ logical qubits are represented by sparse, sharded, stabilizer, or low-entanglement tensor methods, not by dense `2^n` vectors.

## Domain coverage

- `aerospace`: 20 scenarios
- `agriculture`: 20 scenarios
- `climate_risk`: 20 scenarios
- `cybersecurity`: 20 scenarios
- `drug_discovery`: 20 scenarios
- `fraud`: 20 scenarios
- `genomics`: 20 scenarios
- `hardware_calibration`: 20 scenarios
- `healthcare`: 20 scenarios
- `iot_edge`: 20 scenarios
- `manufacturing`: 20 scenarios
- `materials`: 20 scenarios
- `portfolio`: 20 scenarios
- `pqc_migration`: 20 scenarios
- `qec_satellite`: 20 scenarios
- `quantum_network`: 20 scenarios
- `robotics`: 20 scenarios
- `satellite`: 20 scenarios
- `seismology`: 20 scenarios
- `semiconductor`: 20 scenarios
- `smart_grid`: 20 scenarios
- `supply_chain`: 20 scenarios
- `telecom`: 20 scenarios
- `traffic`: 20 scenarios
- `water_network`: 20 scenarios

## Packaged files

- `sansqrit/data/training/sansqrit_real_world_scenarios_v1.jsonl.gz`
- 500 example `.sq` files: `examples/301_...` through `examples/800_...`
- Python access: `sansqrit.scenarios.load_scenarios()`
- CLI access: `sansqrit scenarios info`, `sansqrit scenarios sample`, `sansqrit scenarios export`

## Python usage

```python
from sansqrit.scenarios import scenario_info, load_scenarios
print(scenario_info())
for row in load_scenarios(limit=2):
    print(row["question"])
    print(row["sansqrit_code"])
```

## CLI usage

```bash
sansqrit scenarios info
sansqrit scenarios sample -n 5 --domain smart_grid
sansqrit scenarios export --output scenarios.jsonl --limit 500
sansqrit dataset sample --split real_world_scenarios -n 3
```

## Example record schema

```json
{
  "id": "SQ-RW-001",
  "domain": "climate_risk",
  "question": "...",
  "answer": "...",
  "sansqrit_code": "simulate(...) { ... }",
  "expected_backend": "sharded sparse state with static lookup",
  "qubits": 128,
  "tags": ["real-world", "climate_risk", "sharded", "large-qubit"]
}
```

## Quality rules used

1. The scenario must state the practical problem and constraints.
2. The answer must include backend reasoning, not just code.
3. 120+ qubit examples must avoid false dense-state claims.
4. Programs must use existing Sansqrit syntax and compile through the translator.
5. Dataset rows must be useful for instruction tuning, RAG, and evaluation.
