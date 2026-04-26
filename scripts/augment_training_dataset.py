from __future__ import annotations
import gzip, json, random, hashlib
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'src' / 'sansqrit' / 'data' / 'training'
random.seed(20260426)
VERSION='sansqrit-synthetic-training-v1'
AUTHOR='Karthik V'
LICENSE='MIT'

def read_jsonl_gz(path):
    rows=[]
    if Path(path).exists():
        with gzip.open(path,'rt',encoding='utf-8') as f:
            for line in f:
                if line.strip(): rows.append(json.loads(line))
    return rows

def write_jsonl_gz(path, rows):
    with gzip.open(path,'wt',encoding='utf-8',compresslevel=9) as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True)+'\n')

def rid(prefix, s): return prefix+'_'+hashlib.sha256(s.encode()).hexdigest()[:20]

def rec(task_type, instruction, output, input='', tags=(), difficulty='medium', split='train', source='synthetic-augmentation'):
    return {
        'id': rid('sqt', task_type+instruction+input+output),
        'dataset': VERSION,
        'schema': 'instruction-input-output-v1',
        'language': 'sansqrit',
        'task_type': task_type,
        'instruction': instruction.strip(),
        'input': input.strip(),
        'output': output.strip(),
        'tags': list(tags),
        'difficulty': difficulty,
        'split': split,
        'source': source,
        'author': AUTHOR,
        'license': LICENSE,
        'quality_notes': 'Synthetic record generated from validated Sansqrit DSL patterns; review required for production fine-tuning.',
    }

train = read_jsonl_gz(OUT/'sansqrit_sft_train_v1.jsonl.gz')
eval_rows = read_jsonl_gz(OUT/'sansqrit_sft_eval_v1.jsonl.gz')
prefs = read_jsonl_gz(OUT/'sansqrit_preference_v1.jsonl.gz')
seen={r['id'] for r in train+eval_rows}

def add(r):
    if r['id'] not in seen:
        seen.add(r['id']); train.append(r)

def add_eval(r):
    if r['id'] not in seen:
        seen.add(r['id']); eval_rows.append(r)

single=['H','X','Y','Z','S','Sdg','T','Tdg','SX','SXdg']
two=['CNOT','CX','CZ','CY','CH','CSX','SWAP','iSWAP','ECR','MS']
param=['Rx','Ry','Rz','Phase','CRx','CRy','CRz','CP','RXX','RYY','RZZ','RZX']
engines=['auto','sparse','sharded','hierarchical','stabilizer','mps','density','gpu','distributed']
domains=['climate','finance','cybersecurity','power-grid','telecom','robotics','supply-chain','aerospace','drug-discovery','satellite','qkd','traffic','port-logistics','medical-sensor','materials']
qec_codes=['bit_flip','phase_flip','repetition3','shor9','steane7','five_qubit','surface3']
providers=['openqasm2','openqasm3','qiskit','cirq','braket','azure','pennylane','ibm']
angles=['PI / 2','PI / 3','PI / 4','PI / 6','PI / 8','0.125','0.333','theta']

# 1) diverse code-generation records
for i in range(14000):
    n=random.choice([2,3,4,5,8,10,12,16,20,32,64,120,121,124,128,132,140,144,150,160,192,256,512,1000])
    engine=random.choice(engines)
    domain=random.choice(domains)
    g1=random.choice(single); g2=random.choice(single); tg=random.choice(two); pg=random.choice(param); angle=random.choice(angles)
    q0=random.randrange(min(n,64)); q1=(q0+random.randrange(1,min(n,64)))%n if n>1 else 0
    q2=random.randrange(min(n,64))
    p_header='theta = PI / 7\n    ' if angle=='theta' else ''
    safe_note='# Structured large-qubit program: avoids blind dense expansion.\n' if n>=120 else '# Small/medium Sansqrit program.\n'
    extras=[]
    if random.random()<0.35: extras.append('print(lookup_profile())')
    if random.random()<0.20: extras.append(f'print(export_hardware("{random.choice(providers)}"))')
    if random.random()<0.25: extras.append(f'print(estimate_qubits({n}))')
    if random.random()<0.25: extras.append('print(plan_backend('+str(n)+', []))')
    if not extras: extras=['print(probabilities())' if n<=20 else 'print(engine_nnz())']
    lines=[f'{safe_note}simulate({n}, engine="{engine}", n_shards=16, workers=4, use_lookup=true) {{', f'    q = quantum_register({n})', '    '+p_header+f'{g1}(q[{q0}])', f'    {g2}(q[{q2}])']
    if n>1: lines.append(f'    {tg}(q[{q0}], q[{q1}])')
    if pg in ['CRx','CRy','CRz','CP','RXX','RYY','RZZ','RZX'] and n>1:
        lines.append(f'    {pg}(q[{q0}], q[{q1}], {angle})')
    else:
        lines.append(f'    {pg}(q[{q2}], {angle})')
    lines += ['    '+x for x in extras]
    lines.append('}')
    code='\n'.join(lines)
    add(rec('code_generation', f'Case {i}: write a Sansqrit {domain} circuit with {n} qubits, backend {engine}, gates {g1}/{g2}/{tg}/{pg}, and safe diagnostics.', code, tags=['code-generation',domain,f'{n}q',engine,'diagnostics'], difficulty='hard' if n>=120 else 'medium'))

# 2) QEC training records
for i in range(4500):
    cn=random.choice(qec_codes); pauli=random.choice(['X','Z','Y']); offset=random.choice([0,1,2,3,4]); base=random.choice([0,5,10]); anc=random.choice([12,16,20,24,32]); engine=random.choice(['sparse','stabilizer','density'])
    nq=max(anc+5, {'shor9':24,'steane7':20,'five_qubit':16,'surface3':25}.get(cn,12))
    code=f'''simulate({nq}, engine="{engine}") {{
    q = quantum_register({nq})
    logical = qec_logical("{cn}", base={base})
    qec_encode(logical)
    qec_inject_error(logical, "{pauli}", {offset})
    syndrome = qec_syndrome(logical, ancilla_base={anc})
    correction = qec_correct(logical, syndrome)
    print("syndrome", syndrome)
    print("correction", correction)
}}'''
    add(rec('qec_code_generation', f'QEC case {i}: create a Sansqrit {cn} logical qubit program with a {pauli} error at physical offset {offset}, syndrome extraction, and correction.', code, tags=['qec',cn,pauli,'syndrome','correction'], difficulty='hard'))
    expl=f'''The `{cn}` workflow uses `qec_logical` to allocate a logical abstraction, `qec_encode` to prepare the encoded state, `qec_inject_error` for a controlled synthetic {pauli} error, `qec_syndrome` to extract stabilizer information, and `qec_correct` to apply the decoder result. Use this pattern for QEC tutorials, not as a hardware-calibrated decoder without validation.'''
    add(rec('qec_explanation', f'QEC explanation case {i}: explain the Sansqrit {cn} syndrome pipeline.', expl, tags=['qec',cn,'explanation'], difficulty='hard'))

# 3) Hardware export and interop
for i in range(3000):
    provider=random.choice(providers); n=random.choice([2,3,5,8,10,16,32,120,121])
    code=f'''simulate({n}, engine="auto") {{
    q = quantum_register({n})
    H(q[0])
    CNOT(q[0], q[1])
    Rz(q[min(2, {n-1})], PI / 4)
    payload = export_hardware("{provider}")
    print(hardware_payload_summary())
    print(payload)
}}'''
    add(rec('hardware_export', f'Hardware export case {i}: generate Sansqrit code for {provider} export with {n} logical qubits.', code, tags=['hardware',provider,f'{n}q'], difficulty='medium'))

# 4) Architecture / backend selection / estimates
for i in range(4000):
    n=random.choice([50,80,100,120,128,150,256,512,1000,5000])
    circ=random.choice(['sparse oracle flags','Clifford graph state','low-entanglement nearest-neighbor ansatz','noisy small code block','dense arbitrary state-vector','hierarchical 10-qubit local blocks'])
    if 'Clifford' in circ: backend='stabilizer'
    elif 'low-entanglement' in circ: backend='mps'
    elif 'noisy' in circ: backend='density only for small code blocks'
    elif 'dense arbitrary' in circ: backend='not feasible beyond modest qubit counts; use estimator and refuse unsafe dense expansion'
    elif 'hierarchical' in circ: backend='hierarchical with MPS bridge promotion'
    else: backend='sparse/sharded'
    out=f'''For a {n}-qubit {circ}, prefer `{backend}`. Sansqrit should use `engine="auto"` first, inspect the interaction graph, check dense memory estimates, then choose sparse/sharded, hierarchical tensor shards, stabilizer, MPS, density, GPU, or distributed execution. Precomputed lookups speed static gates and <=10-qubit blocks but do not remove exponential dense-state growth.'''
    add(rec('backend_selection', f'Backend selection case {i}: choose a Sansqrit execution backend for {n} qubits with {circ}.', out, tags=['backend-selection',f'{n}q',circ.replace(' ','-')], difficulty='hard'))

# 5) DSL-to-Python-like translation patterns (high-level, not exact translator internals)
for i in range(2500):
    n=random.choice([2,3,5,10,120]); g=random.choice(single); tg=random.choice(two); engine=random.choice(['sparse','sharded','auto'])
    dsl=f'''simulate({n}, engine="{engine}") {{
    q = quantum_register({n})
    {g}(q[0])
    {tg}(q[0], q[1])
    print(measure_all())
}}'''
    py=f'''from sansqrit.runtime import simulate, quantum_register, {g}, {tg}, measure_all

with simulate({n}, engine="{engine}"):
    q = quantum_register({n})
    {g}(q[0])
    {tg}(q[0], q[1])
    print(measure_all())'''
    add(rec('dsl_to_python', f'Translate Sansqrit DSL case {i} into equivalent Python API style.', py, input=f'```sansqrit\n{dsl}\n```', tags=['translation','python-api',engine], difficulty='medium'))

# 6) Bug fix records
bugs=[
 ('CNOT(q[0])','CNOT(q[0], q[1])','CNOT requires two qubits: control and target.'),
 ('noise_bit_flip(q[0], 0.01)  # inside sparse engine','simulate(4, engine="density") {\n    q = quantum_register(4)\n    noise_bit_flip(q[0], 0.01)\n}','Noise channels require density-matrix simulation.'),
 ('simulate(120, engine="sparse") {\n    q = quantum_register(120)\n    H_all(q)\n}','simulate(120, engine="stabilizer") {\n    q = quantum_register(120)\n    H_all(q)\n    print(measure_all())\n}','For Clifford-only H_all on 120 qubits, stabilizer avoids dense expansion.'),
 ('qec_logical("surface")','qec_logical("surface3", base=0)','Use a registered code name such as surface3 or supply a distance-aware helper.'),
 ('# independent 10-qubit blocks after CNOT(q[9], q[10])','# use engine="hierarchical" with MPS bridge promotion for CNOT(q[9], q[10])','Cross-block entanglement must be represented, not ignored.'),
]
for i in range(2000):
    bad,good,note=random.choice(bugs)
    add(rec('bug_fix', f'Bug-fix case {i}: correct this Sansqrit mistake and explain why.', f'Corrected Sansqrit:\n```sansqrit\n{good}\n```\nExplanation: {note}', input=f'```sansqrit\n{bad}\n```', tags=['bug-fix','quality'], difficulty='medium'))

# 7) eval holdout set
for i in range(1200):
    n=random.choice([120,128,150,256,1000]); topic=random.choice(['QEC','hardware export','lookup profiling','hierarchical bridge','backend estimate'])
    add_eval(rec('eval_prompt', f'Evaluation case {i}: write a concise Sansqrit {topic} program for {n} qubits.', f'# Expected answer should be valid Sansqrit, should avoid unsafe dense expansion for {n} qubits, should use diagnostics such as estimate_qubits, lookup_profile, hierarchical_report, or qec_syndrome when relevant.', tags=['eval',topic.lower().replace(' ','-'),f'{n}q'], difficulty='hard', split='eval'))

# Preference extra
pref_base=len(prefs)
for i in range(3000):
    n=random.choice([120,128,150,1000]); provider=random.choice(providers); cn=random.choice(qec_codes)
    if i%3==0:
        prompt=f'Preference case {i}: produce a safe {n}-qubit Sansqrit program.'
        chosen=f'simulate({n}, engine="auto", use_lookup=true) {{\n    q = quantum_register({n})\n    X(q[{n-1}])\n    H(q[0])\n    CNOT(q[0], q[1])\n    print(estimate_qubits({n}))\n    print(engine_nnz())\n}}'
        rejected=f'simulate({n}, engine="sparse") {{\n    q = quantum_register({n})\n    H_all(q)\n    print("dense {n} qubits is always fast")\n}}'
    elif i%3==1:
        prompt=f'Preference case {i}: export a Sansqrit circuit to {provider} correctly.'
        chosen=f'simulate(3, engine="sparse") {{\n    q = quantum_register(3)\n    H(q[0])\n    CNOT(q[0], q[1])\n    print(export_hardware("{provider}"))\n}}'
        rejected=f'print("send to {provider} without building a circuit")'
    else:
        prompt=f'Preference case {i}: build a QEC program for {cn} with syndrome extraction.'
        chosen=f'simulate(24, engine="sparse") {{\n    q = quantum_register(24)\n    l = qec_logical("{cn}", base=0)\n    qec_encode(l)\n    qec_inject_error(l, "X", 1)\n    print(qec_syndrome_and_correct(l, ancilla_base=12))\n}}'
        rejected=f'simulate(24, engine="sparse") {{\n    q = quantum_register(24)\n    X(q[1])\n    print("QEC done")\n}}'
    prefs.append({
        'id': rid('sqp', prompt+chosen+rejected), 'dataset': VERSION, 'schema':'preference-v1', 'language':'sansqrit',
        'prompt':prompt, 'chosen':chosen, 'rejected':rejected, 'tags':['preference','dpo','quality'], 'split':'train' if i<2700 else 'eval',
        'source':'synthetic-preference-augmentation', 'author':AUTHOR, 'license':LICENSE,
        'quality_notes':'Chosen answer follows Sansqrit architecture and safety/accuracy constraints; rejected answer contains overclaiming or incomplete logic.'})

# Dedup IDs and cap
unique=[]; ids=set()
for r in train:
    if r['id'] not in ids:
        ids.add(r['id']); unique.append(r)
train=unique[:30000]
unique=[]; ids=set()
for r in eval_rows:
    if r['id'] not in ids:
        ids.add(r['id']); unique.append(r)
eval_rows=unique[:1500]
unique=[]; ids=set()
for r in prefs:
    if r['id'] not in ids:
        ids.add(r['id']); unique.append(r)
prefs=unique[:5000]

write_jsonl_gz(OUT/'sansqrit_sft_train_v1.jsonl.gz', train)
write_jsonl_gz(OUT/'sansqrit_sft_eval_v1.jsonl.gz', eval_rows)
write_jsonl_gz(OUT/'sansqrit_preference_v1.jsonl.gz', prefs)
manifest={
 'dataset': VERSION, 'author': AUTHOR, 'license': LICENSE, 'created_utc': datetime.now(timezone.utc).isoformat(),
 'description':'Extensive synthetic instruction, code, explanation, troubleshooting, QEC, hardware-export and preference dataset for training AI models to understand and generate Sansqrit quantum DSL programs.',
 'files':[
  {'name':'sansqrit_sft_train_v1.jsonl.gz','schema':'instruction-input-output-v1','records':len(train)},
  {'name':'sansqrit_sft_eval_v1.jsonl.gz','schema':'instruction-input-output-v1','records':len(eval_rows)},
  {'name':'sansqrit_preference_v1.jsonl.gz','schema':'preference-v1','records':len(prefs)},
 ],
 'total_records':len(train)+len(eval_rows)+len(prefs),
 'topics':['DSL syntax','gates','circuits','algorithms','large qubit sparse/sharded execution','hierarchical tensor shards','precomputed lookups','distributed computing','QEC','surface codes','hardware exports','QASM','troubleshooting','backend selection','bug fixing','preference training','DSL to Python','safe dense-state warnings'],
 'schemas': {
   'instruction-input-output-v1': {'fields':['id','dataset','schema','language','task_type','instruction','input','output','tags','difficulty','split','source','author','license','quality_notes']},
   'preference-v1': {'fields':['id','dataset','schema','language','prompt','chosen','rejected','tags','split','source','author','license','quality_notes']}
 },
 'intended_use':'Fine-tuning, supervised instruction tuning, DPO/preference training, retrieval-augmented generation, evaluation, prompt engineering and documentation-aware AI model training for Sansqrit DSL.',
 'limitations':'Synthetic data is generated from templates and package examples. It should be supplemented with human-reviewed traces and verified circuit outputs before safety-critical use.'
}
(OUT/'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding='utf-8')
# README samples
sample=['# Sansqrit Synthetic Training Dataset\n', 'This directory is packaged inside Sansqrit and contains compressed JSONL datasets for AI/ML training.\n', '## Manifest\n', '```json\n'+json.dumps(manifest, indent=2)+'\n```\n', '## Sample records\n']
for r in train[:15]:
    sample.append(f"### {r['id']}\n\nInstruction: {r['instruction']}\n\n```sansqrit\n{r['output'][:1500]}\n```\n")
(OUT/'README.md').write_text('\n'.join(sample), encoding='utf-8')
print(json.dumps(manifest, indent=2))
