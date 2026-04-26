from __future__ import annotations
import gzip, hashlib, json, random, re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "sansqrit" / "data" / "training"
EXAMPLES = ROOT / "examples"
OUT.mkdir(parents=True, exist_ok=True)
random.seed(42690)

VERSION = "sansqrit-synthetic-training-v1"
LICENSE = "MIT"
AUTHOR = "Karthik V"

records = []
preferences = []
eval_records = []
seen = set()

def clean(s: str) -> str:
    return re.sub(r"[ \t]+\n", "\n", s.strip())

def rid(prefix: str, data: str) -> str:
    return prefix + "_" + hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]

def add(task_type, instruction, output, input_text="", tags=(), difficulty="medium", split="train", source="synthetic-template"):
    instruction = clean(instruction)
    output = clean(output)
    input_text = clean(input_text)
    key = (task_type, instruction, input_text, output)
    if key in seen:
        return
    seen.add(key)
    rec = {
        "id": rid("sqt", task_type + instruction + input_text + output),
        "dataset": VERSION,
        "schema": "instruction-input-output-v1",
        "language": "sansqrit",
        "task_type": task_type,
        "instruction": instruction,
        "input": input_text,
        "output": output,
        "tags": list(tags),
        "difficulty": difficulty,
        "split": split,
        "source": source,
        "author": AUTHOR,
        "license": LICENSE,
        "quality_notes": "Synthetic record generated from validated Sansqrit DSL patterns; review required for production fine-tuning.",
    }
    if split == "eval":
        eval_records.append(rec)
    else:
        records.append(rec)

# Ingest existing examples as high quality seeds
for p in sorted(EXAMPLES.glob("*.sq")):
    code = p.read_text(encoding="utf-8").strip()
    stem = p.stem
    title = re.sub(r"^\d+_", "", stem).replace("_", " ")
    tags = ["canonical-example"] + [x for x in title.split()[:6]]
    add("code_generation", f"Write a Sansqrit program for: {title}.", code, tags=tags, difficulty="hard" if any(x in stem for x in ["120", "128", "150", "qec", "hierarchical", "distributed"]) else "medium", source="package-example")
    add("code_explanation", f"Explain what the Sansqrit example {p.name} does.", f"This program demonstrates {title}. It uses Sansqrit DSL syntax and can be run with `sansqrit run {p.name}`.\n\n```sansqrit\n{code}\n```", tags=tags+["explanation"], source="package-example")

single_gates = ["H", "X", "Y", "Z", "S", "Sdg", "T", "Tdg", "SX", "SXdg"]
param_gates = [("Rx", "theta"), ("Ry", "theta"), ("Rz", "theta"), ("Phase", "theta")]
two_gates = ["CNOT", "CX", "CZ", "CY", "CH", "CSX", "SWAP", "iSWAP", "ECR", "MS"]
backends = [
    ("sparse", "oracle-style sparse amplitude simulation"),
    ("sharded", "large sparse simulation across shards"),
    ("hierarchical", "120+ qubit block tensor shards with MPS bridge promotion"),
    ("stabilizer", "Clifford circuits with hundreds or thousands of qubits"),
    ("mps", "low-entanglement chain-like circuits"),
    ("density", "small noisy circuits and density-matrix noise studies"),
    ("gpu", "dense small/medium circuits when CuPy/CUDA is installed"),
    ("distributed", "multi-node sparse worker coordination"),
]
real_domains = [
    ("climate sensor anomaly flags", "X(q[3])\n    X(q[41])\n    X(q[90])", "climate"),
    ("power-grid fault localization", "X(q[12])\n    X(q[73])\n    X(q[149])", "power-grid"),
    ("finance portfolio risk flags", "X(q[5])\n    X(q[66])\n    X(q[127])", "finance"),
    ("cybersecurity threat graph", "H(q[0])\n    CNOT(q[0], q[32])\n    CNOT(q[32], q[96])", "cybersecurity"),
    ("supply-chain route activation", "X(q[10])\n    X(q[88])\n    H(q[0])\n    CNOT(q[0], q[119])", "logistics"),
    ("satellite QEC communication link", "l = qec_logical('shor9', base=0)\n    qec_encode(l)\n    qec_inject_error(l, 'X', 4)\n    print(qec_syndrome_and_correct(l, ancilla_base=20))", "satellite-qec"),
    ("robotics sparse path planning", "X(q[22])\n    X(q[88])\n    Rz(q[22], PI / 8)\n    H(q[0])\n    CNOT(q[0], q[88])", "robotics"),
    ("telecom hierarchical block routing", "block_a = shard('block_a', 0, 9)\n    block_b = shard('block_b', 10, 19)\n    apply_block('H', block_a)\n    X(q[17])\n    CNOT(q[9], q[10])", "telecom"),
]

# Basic syntax and gates
for n in [1, 2, 3, 4, 5, 8, 10, 12, 16, 24, 32, 64, 120, 128, 150, 256, 1000]:
    for gate in single_gates:
        q = min(n-1, random.randrange(max(1, min(n, 24))))
        code = f"simulate({n}, engine=\"auto\") {{\n    q = quantum_register({n})\n    {gate}(q[{q}])\n    print(probabilities())\n}}"
        add("code_generation", f"Write Sansqrit code that allocates {n} qubits and applies {gate} to qubit {q}.", code, tags=["gate", gate, f"{n}q"], difficulty="easy" if n <= 5 else "medium")

for n in [2, 3, 5, 10, 20, 120, 150]:
    for gate in two_gates:
        a, b = 0, min(n-1, 1)
        code = f"simulate({n}, engine=\"auto\") {{\n    q = quantum_register({n})\n    H(q[{a}])\n    {gate}(q[{a}], q[{b}])\n    print(engine_nnz())\n}}"
        add("code_generation", f"Create a Sansqrit {n}-qubit circuit using {gate} between q[{a}] and q[{b}].", code, tags=["two-qubit", gate, f"{n}q"], difficulty="medium")

for n in [1, 2, 4, 10, 120]:
    for gate, param in param_gates:
        angle = random.choice(["PI / 2", "PI / 4", "PI / 8", "0.125", "theta"])
        header = "theta = PI / 7\n    " if angle == "theta" else ""
        code = f"simulate({n}, engine=\"sparse\") {{\n    q = quantum_register({n})\n    {header}{gate}(q[0], {angle})\n    print(probabilities())\n}}"
        add("code_generation", f"Write Sansqrit using parameterized gate {gate} with angle {angle}.", code, tags=["parameterized", gate], difficulty="medium")

# Backend recommendation and architecture Q&A
for backend, purpose in backends:
    add("backend_selection", f"When should I use the Sansqrit `{backend}` backend?", f"Use `engine=\"{backend}\"` for {purpose}. In Sansqrit, prefer `engine=\"auto\"` when you want the planner to choose automatically. Always use sparse/sharded/hierarchical/stabilizer/MPS approaches for 120+ logical qubits unless the circuit is provably small or structured.", tags=["backend", backend, "architecture"], difficulty="medium")
    code = f"simulate(120, engine=\"{backend}\") {{\n    q = quantum_register(120)\n    X(q[119])\n    H(q[0])\n    CNOT(q[0], q[1])\n    print(plan_backend(120, []))\n}}"
    add("code_generation", f"Show a 120-qubit Sansqrit template using the {backend} backend.", code, tags=["backend", backend, "120q"], difficulty="hard")

architecture_answers = [
    ("Explain why dense 120-qubit simulation is not realistic.", "A dense 120-qubit state has 2^120 complex amplitudes. Sansqrit can address 120+ logical qubits, but it must use sparse, sharded, stabilizer, MPS, hierarchical tensor, or distributed representations when the circuit has structure. Lookup tables reduce overhead but do not remove exponential dense memory growth."),
    ("Explain how precomputed lookup data is used in Sansqrit.", "Sansqrit ships packaged lookup files under `sansqrit/data/`. Static gates use precomputed matrices; <=10-qubit embedded transition tables accelerate small blocks; larger registers use sparse basis-key updates plus small static matrix lookups. Dynamic parameterized gates use runtime computation or cacheable compiled kernels."),
    ("Explain how hierarchical tensor shards handle 120 qubits.", "Sansqrit can split 120 qubits into 10-qubit dense blocks for local operations. Cross-block gates are not ignored: when a bridge entangles blocks, the runtime promotes to an MPS/tensor representation or falls back to sparse global updates so results remain accurate."),
    ("Explain how distributed sparse execution works.", "The distributed backend partitions sparse basis amplitudes across workers. Local gates can be processed per shard; cross-shard operations require communication, merge/repartition, or an MPS/tensor bridge. Distributed execution helps with large sparse maps but does not make fully dense 120-qubit states feasible."),
    ("Explain how QEC is represented in Sansqrit.", "The QEC layer exposes logical qubits, stabilizer codes, syndrome circuits, decoders, logical gates, and encode/syndrome/correct/decode workflows. It includes bit-flip, phase-flip, repetition, Shor9, Steane7, five-qubit, and surface-code helper abstractions."),
]
for instr, out in architecture_answers:
    add("explanation", instr, out, tags=["architecture", "explanation"], difficulty="hard")

# Real-world large-qubit application code records
for n in [120, 121, 124, 128, 132, 140, 144, 150, 160, 256, 1000]:
    for title, body, domain in real_domains:
        engine = "stabilizer" if "graph" in domain or n >= 1000 else ("hierarchical" if n >= 120 and "telecom" in domain else "sharded")
        code = f"# {n}-qubit {title} in Sansqrit.\nsimulate({n}, engine=\"{engine}\", n_shards=16, workers=4, use_lookup=true) {{\n    q = quantum_register({n})\n    {body}\n    print(\"domain\", \"{domain}\")\n    print(\"nonzero amplitudes\", engine_nnz())\n    print(lookup_profile())\n}}"
        add("real_world_large_qubit_program", f"Write a Sansqrit program for a {n}-qubit {title} application.", code, tags=["real-world", domain, f"{n}q", engine], difficulty="hard")

# QEC code generation records
qec_codes = ["bit_flip", "phase_flip", "repetition3", "shor9", "steane7", "five_qubit", "surface3"]
for code_name in qec_codes:
    engine = "density" if code_name in ["bit_flip", "phase_flip"] else "sparse"
    n = {"bit_flip":6, "phase_flip":6, "repetition3":6, "shor9":24, "steane7":20, "five_qubit":16, "surface3":25}.get(code_name, 12)
    code = f"simulate({n}, engine=\"{engine}\") {{\n    q = quantum_register({n})\n    logical = qec_logical(\"{code_name}\", base=0)\n    qec_encode(logical)\n    qec_inject_error(logical, \"X\", 1)\n    syndrome = qec_syndrome(logical, ancilla_base={max(3, n//2)})\n    correction = qec_correct(logical, syndrome)\n    print(syndrome)\n    print(correction)\n}}"
    add("qec_code_generation", f"Create a Sansqrit QEC program using the {code_name} code with syndrome extraction and correction.", code, tags=["qec", code_name, "syndrome", "correction"], difficulty="hard")
    add("qec_explanation", f"Explain the Sansqrit QEC workflow for {code_name}.", f"For `{code_name}`, Sansqrit creates a logical qubit with `qec_logical`, encodes it with `qec_encode`, extracts stabilizer syndrome bits with `qec_syndrome`, decodes them with the registered decoder via `qec_correct`, and can optionally decode with `qec_decode`. Use density/noise backends for small noisy studies and stabilizer/sparse backends for larger structural tests.", tags=["qec", code_name, "explanation"], difficulty="hard")

# Hardware export records
providers = ["openqasm2", "openqasm3", "qiskit", "cirq", "braket", "azure", "pennylane", "ibm"]
for provider in providers:
    code = f"simulate(5, engine=\"sparse\") {{\n    q = quantum_register(5)\n    H(q[0])\n    CNOT(q[0], q[1])\n    Rz(q[2], PI / 4)\n    payload = export_hardware(\"{provider}\")\n    print(payload)\n}}"
    add("hardware_export", f"Write Sansqrit code that exports a circuit for {provider}.", code, tags=["hardware", provider, "export"], difficulty="medium")
    add("hardware_explanation", f"How does Sansqrit export to {provider}?", f"Use `export_hardware(\"{provider}\")` inside a `simulate` block after building the circuit. For cloud/hardware workflows, Sansqrit usually emits OpenQASM 2/3 or provider SDK payloads, and users submit those payloads through Qiskit, Cirq, Braket, Azure Quantum, or PennyLane depending on installed extras.", tags=["hardware", provider], difficulty="medium")

# Troubleshooting records
troubles = [
    ("lookup files are missing", "Run `sansqrit doctor` and check `sansqrit/data/lookup_*.json*` inside the installed package. Reinstall the wheel if package data is missing."),
    ("120-qubit dense circuit is too slow", "Use `engine=\"auto\"` or `estimate_qubits(120)`. Avoid `H_all` on non-Clifford circuits unless using stabilizer/MPS/tensor methods that preserve structure."),
    ("cross-block hierarchical result is wrong", "Ensure bridge gates promote to MPS or sparse global mode. Do not keep entangled blocks as independent 10-qubit vectors."),
    ("GPU backend unavailable", "Install the optional GPU extra and a CUDA-compatible CuPy build, then run `sansqrit backends` to verify availability."),
    ("distributed worker cannot connect", "Start `sansqrit worker --host 0.0.0.0 --port 8765`, verify firewall rules, and pass worker addresses to the distributed backend."),
]
for symptom, fix in troubles:
    add("troubleshooting", f"Troubleshoot Sansqrit issue: {symptom}.", f"Symptom: {symptom}\nCause/Fix: {fix}", tags=["troubleshooting"], difficulty="medium")

# Buggy to fixed records
bug_templates = [
    ("q = quantum_register(2)\nCNOT(q[0])", "q = quantum_register(2)\nCNOT(q[0], q[1])", "CNOT requires a control and target qubit."),
    ("simulate(120, engine=\"sparse\") {\n    q = quantum_register(120)\n    H_all(q)\n}", "simulate(120, engine=\"stabilizer\") {\n    q = quantum_register(120)\n    H_all(q)\n    print(measure_all())\n}", "For Clifford-only H_all on 120 qubits, use the stabilizer backend instead of dense sparse expansion."),
    ("simulate(6, engine=\"sparse\") {\n    q = quantum_register(6)\n    noise_bit_flip(q[0], 0.01)\n}", "simulate(6, engine=\"density\") {\n    q = quantum_register(6)\n    noise_bit_flip(q[0], 0.01)\n}", "Noise channels require the density backend."),
    ("logical = qec_logical(\"shor\")", "logical = qec_logical(\"shor9\", base=0)", "Use the registered Sansqrit code name `shor9`."),
]
for bad, good, note in bug_templates:
    add("bug_fix", "Fix this incorrect Sansqrit program and explain the fix.", f"Corrected code:\n```sansqrit\n{good}\n```\nExplanation: {note}", input_text=f"```sansqrit\n{bad}\n```", tags=["bug-fix", "syntax"], difficulty="medium")

# Generate many structured variants for SFT scale
algorithms = [
    ("Bell state", "q = quantum_register(2)\n    H(q[0])\n    CNOT(q[0], q[1])\n    print(measure_all())", 2),
    ("GHZ state", "q = quantum_register(3)\n    H(q[0])\n    CNOT(q[0], q[1])\n    CNOT(q[1], q[2])\n    print(probabilities())", 3),
    ("QFT", "q = quantum_register(5)\n    X(q[0])\n    qft(q)\n    print(probabilities())", 5),
    ("Grover search", "print(grover_search(oracle_target=5, n_qubits=3))", 3),
    ("QAOA MaxCut", "print(qaoa_maxcut(edges=[(0,1),(1,2),(2,3)], p=2))", 4),
    ("VQE H2", "print(vqe_h2(theta=0.2))", 4),
    ("teleportation", "print(teleport(alpha=1.0, beta=0.0))", 3),
    ("BB84 QKD", "print(bb84_qkd(bits=[1,0,1,1], bases=[0,1,0,1]))", 8),
]
verbs = ["Write", "Create", "Generate", "Show", "Draft", "Produce"]
styles = ["minimal", "well-commented", "diagnostic", "hardware-exportable", "lookup-profiled", "AI-training-friendly"]
for i in range(8000):
    name, body, nq = random.choice(algorithms)
    style = random.choice(styles)
    verb = random.choice(verbs)
    backend = random.choice(["auto", "sparse", "sharded", "stabilizer", "mps"])
    comments = f"# {style} {name} example\n" if style != "minimal" else ""
    extra = "\n    print(lookup_profile())" if style == "lookup-profiled" else ("\n    print(export_qasm3())" if style == "hardware-exportable" else "")
    code = f"{comments}simulate({max(nq, 2)}, engine=\"{backend}\") {{\n    {body}{extra}\n}}"
    add("code_generation", f"{verb} a {style} Sansqrit program for {name} using the {backend} backend.", code, tags=["algorithm", name.lower().replace(" ", "-"), backend, style], difficulty=random.choice(["easy","medium","hard"]))

# Component/block lookup examples with <=10 qubits
for i in range(3500):
    n = random.randint(2, 10)
    qs = sorted(random.sample(range(n), k=min(n, random.randint(1, min(4, n)))))
    g1, g2 = random.choice(single_gates), random.choice(single_gates)
    body = [f"{g1}(q[{qs[0]}])"]
    if len(qs) >= 2:
        body.append(f"CNOT(q[{qs[0]}], q[{qs[1]}])")
    if len(qs) >= 3:
        body.append(f"{g2}(q[{qs[2]}])")
    code = f"simulate({n}, engine=\"sparse\", use_lookup=true) {{\n    q = quantum_register({n})\n    " + "\n    ".join(body) + "\n    print(lookup_profile())\n}"
    add("lookup_code_generation", f"Generate a <=10-qubit Sansqrit circuit that benefits from embedded precomputed lookup tables. Use {n} qubits.", code, tags=["lookup", "<=10q", f"{n}q"], difficulty="medium")

# Large-qubit safe/unsafe examples
for i in range(3000):
    n = random.choice([120, 121, 128, 132, 140, 144, 150, 160, 192, 256, 512, 1000])
    domain_title, body, domain = random.choice(real_domains)
    engine = random.choice(["auto", "sharded", "hierarchical", "stabilizer", "mps"])
    code = f"# Safe large-register Sansqrit pattern: {domain_title}\nsimulate({n}, engine=\"{engine}\", n_shards=16, workers=4, use_lookup=true) {{\n    q = quantum_register({n})\n    {body}\n    print(estimate_qubits({n}))\n    print(engine_nnz())\n}}"
    add("large_qubit_safe_code", f"Write a safe structured Sansqrit program for {n} logical qubits in the {domain} domain.", code, tags=["large-qubit", f"{n}q", domain, engine], difficulty="hard")

# Evaluation held-out prompts
for i, (instr, out) in enumerate(architecture_answers):
    rec_instr = instr.replace("Explain", "In one paragraph, explain")
    add("eval_explanation", rec_instr, out, tags=["eval", "architecture"], difficulty="hard", split="eval")
for provider in providers:
    add("eval_code_generation", f"Generate a three-qubit Bell-like Sansqrit circuit and export it to {provider}.", f"simulate(3, engine=\"sparse\") {{\n    q = quantum_register(3)\n    H(q[0])\n    CNOT(q[0], q[1])\n    CNOT(q[1], q[2])\n    print(export_hardware(\"{provider}\"))\n}}", tags=["eval", "hardware", provider], difficulty="medium", split="eval")
for code_name in qec_codes:
    add("eval_qec", f"Write a concise Sansqrit QEC example for {code_name} with syndrome and correction.", f"simulate(24, engine=\"sparse\") {{\n    q = quantum_register(24)\n    logical = qec_logical(\"{code_name}\", base=0)\n    qec_encode(logical)\n    qec_inject_error(logical, \"X\", 1)\n    print(qec_syndrome_and_correct(logical, ancilla_base=12))\n}}", tags=["eval", "qec", code_name], difficulty="hard", split="eval")

# Preference/DPO records
preference_prompts = [
    ("Write a 120-qubit program that is honest about dense-state limitations.",
     "simulate(120, engine=\"auto\") {\n    q = quantum_register(120)\n    X(q[119])\n    H(q[0])\n    CNOT(q[0], q[1])\n    print(estimate_qubits(120))\n    print(engine_nnz())\n}",
     "simulate(120, engine=\"sparse\") {\n    q = quantum_register(120)\n    H_all(q)\n    print(\"fast dense 120 qubits\")\n}"),
    ("Write accurate Sansqrit code for a cross-block 120-qubit entangling bridge.",
     "simulate(120, engine=\"hierarchical\", block_size=10, cutoff=0.0) {\n    q = quantum_register(120)\n    H(q[9])\n    CNOT(q[9], q[10])\n    print(hierarchical_report())\n}",
     "simulate(120, engine=\"hierarchical\") {\n    q = quantum_register(120)\n    # Incorrectly assume q[9] and q[10] remain independent after CNOT.\n    H(q[9])\n    CNOT(q[9], q[10])\n}"),
    ("Write a QEC workflow with syndrome extraction.",
     "simulate(12, engine=\"sparse\") {\n    q = quantum_register(12)\n    l = qec_logical(\"bit_flip\", base=0)\n    qec_encode(l)\n    qec_inject_error(l, \"X\", 1)\n    print(qec_syndrome_and_correct(l, ancilla_base=6))\n}",
     "simulate(12, engine=\"sparse\") {\n    q = quantum_register(12)\n    X(q[1])\n    print(\"corrected\")\n}"),
]
for i in range(2000):
    prompt, chosen, rejected = random.choice(preference_prompts)
    rec = {
        "id": rid("sqp", prompt + chosen + rejected + str(i)),
        "dataset": VERSION,
        "schema": "preference-v1",
        "language": "sansqrit",
        "prompt": prompt,
        "chosen": chosen,
        "rejected": rejected,
        "tags": ["preference", "dpo", "quality"],
        "split": "train" if i < 1800 else "eval",
        "source": "synthetic-preference-template",
        "author": AUTHOR,
        "license": LICENSE,
        "quality_notes": "Chosen answer follows Sansqrit architecture and safety/accuracy constraints; rejected answer contains overclaiming or incomplete logic.",
    }
    preferences.append(rec)

# Sort/stable truncate maybe ensure not enormous
records = records[:20000]
eval_records = eval_records[:1000]
preferences = preferences[:2000]

# Write files

def write_jsonl_gz(path, rows):
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=9) as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

write_jsonl_gz(OUT / "sansqrit_sft_train_v1.jsonl.gz", records)
write_jsonl_gz(OUT / "sansqrit_sft_eval_v1.jsonl.gz", eval_records)
write_jsonl_gz(OUT / "sansqrit_preference_v1.jsonl.gz", preferences)

manifest = {
    "dataset": VERSION,
    "author": AUTHOR,
    "license": LICENSE,
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "description": "Synthetic instruction, code, explanation, troubleshooting, QEC, hardware-export and preference dataset for training AI models to understand and generate Sansqrit quantum DSL programs.",
    "files": [
        {"name": "sansqrit_sft_train_v1.jsonl.gz", "schema": "instruction-input-output-v1", "records": len(records)},
        {"name": "sansqrit_sft_eval_v1.jsonl.gz", "schema": "instruction-input-output-v1", "records": len(eval_records)},
        {"name": "sansqrit_preference_v1.jsonl.gz", "schema": "preference-v1", "records": len(preferences)},
    ],
    "total_records": len(records) + len(eval_records) + len(preferences),
    "topics": [
        "DSL syntax", "gates", "circuits", "algorithms", "large qubit sparse/sharded execution", "hierarchical tensor shards", "precomputed lookups", "distributed computing", "QEC", "surface codes", "hardware exports", "QASM", "troubleshooting", "backend selection", "bug fixing", "preference training"
    ],
    "intended_use": "Fine-tuning, retrieval-augmented generation, evaluation, prompt engineering and documentation-aware AI model training for Sansqrit DSL.",
    "limitations": "Synthetic data is generated from templates and package examples. It should be supplemented with human-reviewed traces and verified circuit outputs before safety-critical use.",
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

# Human-friendly samples
sample_md = ["# Sansqrit Synthetic Training Dataset Samples\n"]
for r in records[:20]:
    sample_md.append(f"## {r['id']}\n\n**Task:** {r['task_type']}\n\n**Instruction:** {r['instruction']}\n\n**Output:**\n```sansqrit\n{r['output'][:2000]}\n```\n")
(OUT / "README.md").write_text("\n".join(sample_md), encoding="utf-8")
print(json.dumps(manifest, indent=2))
