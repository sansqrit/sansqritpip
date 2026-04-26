

# v0.3.4 Real-World Scenario Training Corpus

Sansqrit now embeds a 500-record real-world scenario corpus authored by **Karthik V**. It is designed for AI/ML model training so models can learn to answer user prompts with valid Sansqrit code, backend reasoning, safety notes, and troubleshooting guidance.

Packaged resources:

```text
sansqrit/data/training/sansqrit_real_world_scenarios_v1.jsonl.gz
examples/301_scenario_...sq through examples/800_scenario_...sq
docs/REAL_WORLD_SCENARIO_CORPUS.md
```

CLI usage:

```bash
sansqrit scenarios info
sansqrit scenarios sample -n 5 --domain smart_grid
sansqrit scenarios export --output scenarios.jsonl --limit 500
sansqrit dataset sample --split real_world_scenarios -n 3
```

Python usage:

```python
from sansqrit.scenarios import scenario_info, load_scenarios
print(scenario_info())
for row in load_scenarios(limit=3):
    print(row["question"])
    print(row["sansqrit_code"])
```

The scenario set covers climate, energy, finance, cybersecurity, logistics, healthcare, genomics, materials, drug discovery, telecom, quantum networking, post-quantum cryptography migration, quantum error correction, hardware export, and 120+ qubit sparse/tensor/stabilizer workflows.

Important modeling lesson: for 120+ qubit examples, Sansqrit teaches AI models to select sparse/sharded, hierarchical tensor shards, MPS, stabilizer, or QEC strategies instead of falsely claiming arbitrary dense state-vector simulation is feasible.
