from __future__ import annotations
import gzip, hashlib, json, random, re
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'src'/'sansqrit'/'data'/'training'
EXAMPLES=ROOT/'examples'
OUT.mkdir(parents=True, exist_ok=True)
random.seed(2026042601)
VERSION='sansqrit-synthetic-training-v1'
AUTHOR='Karthik V'
LICENSE='MIT'

def rid(prefix, s): return prefix+'_'+hashlib.sha256(s.encode()).hexdigest()[:20]
def jdump(row): return json.dumps(row, ensure_ascii=False, sort_keys=True)+'\n'
def base(task_type, instruction, output, input='', tags=(), difficulty='medium', split='train', source='synthetic-v1'):
    return {'id':rid('sqt', task_type+instruction+input+output),'dataset':VERSION,'schema':'instruction-input-output-v1','language':'sansqrit','task_type':task_type,'instruction':instruction.strip(),'input':input.strip(),'output':output.strip(),'tags':list(tags),'difficulty':difficulty,'split':split,'source':source,'author':AUTHOR,'license':LICENSE,'quality_notes':'Synthetic record generated from validated Sansqrit DSL patterns; review required for production fine-tuning.'}

def pref(prompt, chosen, rejected, idx):
    return {'id':rid('sqp', prompt+chosen+rejected+str(idx)),'dataset':VERSION,'schema':'preference-v1','language':'sansqrit','prompt':prompt.strip(),'chosen':chosen.strip(),'rejected':rejected.strip(),'tags':['preference','dpo','quality'],'split':'train' if idx<4500 else 'eval','source':'synthetic-preference-v1','author':AUTHOR,'license':LICENSE,'quality_notes':'Chosen answer follows Sansqrit architecture and safety/accuracy constraints; rejected answer contains overclaiming, invalid DSL, or incomplete execution logic.'}

single=['H','X','Y','Z','S','Sdg','T','Tdg','SX','SXdg']
two=['CNOT','CX','CZ','CY','CH','CSX','SWAP','iSWAP','ECR','MS']
param=['Rx','Ry','Rz','Phase','CRx','CRy','CRz','CP','RXX','RYY','RZZ','RZX']
engines=['auto','sparse','sharded','hierarchical','stabilizer','mps','density','gpu','distributed']
domains=['climate','finance','cybersecurity','power-grid','telecom','robotics','supply-chain','aerospace','drug-discovery','satellite','qkd','traffic','port-logistics','medical-sensor','materials','pharma','banking','smart-city','ocean-sensor','earthquake-grid']
qec_codes=['bit_flip','phase_flip','repetition3','shor9','steane7','five_qubit','surface3']
providers=['openqasm2','openqasm3','qiskit','cirq','braket','azure','pennylane','ibm']
angles=['PI / 2','PI / 3','PI / 4','PI / 6','PI / 8','0.125','0.333','theta']
real_bodies=[
 ('climate','X(q[3])\n    X(q[41])\n    X(q[90])'),('power-grid','X(q[12])\n    X(q[73])\n    X(q[149])'),('finance','X(q[5])\n    X(q[66])\n    X(q[127])'),('cybersecurity','H(q[0])\n    CNOT(q[0], q[32])\n    CNOT(q[32], q[96])'),('logistics','X(q[10])\n    X(q[88])\n    H(q[0])\n    CNOT(q[0], q[119])'),('robotics','X(q[22])\n    X(q[88])\n    Rz(q[22], PI / 8)\n    H(q[0])\n    CNOT(q[0], q[88])'),('telecom','block_a = shard("block_a", 0, 9)\n    block_b = shard("block_b", 10, 19)\n    apply_block("H", block_a)\n    X(q[17])\n    CNOT(q[9], q[10])')]
algorithms=[('Bell state','q = quantum_register(2)\n    H(q[0])\n    CNOT(q[0], q[1])\n    print(measure_all())',2),('GHZ state','q = quantum_register(3)\n    H(q[0])\n    CNOT(q[0], q[1])\n    CNOT(q[1], q[2])\n    print(probabilities())',3),('QFT','q = quantum_register(5)\n    X(q[0])\n    qft(q)\n    print(probabilities())',5),('Grover search','print(grover_search(oracle_target=5, n_qubits=3))',3),('QAOA MaxCut','print(qaoa_maxcut(edges=[(0,1),(1,2),(2,3)], p=2))',4),('VQE H2','print(vqe_h2(theta=0.2))',4),('teleportation','print(teleport(alpha=1.0, beta=0.0))',3),('BB84 QKD','print(bb84_qkd(bits=[1,0,1,1], bases=[0,1,0,1]))',8)]

counts={'train':0,'eval':0,'pref':0}
train_path=OUT/'sansqrit_sft_train_v1.jsonl.gz'
eval_path=OUT/'sansqrit_sft_eval_v1.jsonl.gz'
pref_path=OUT/'sansqrit_preference_v1.jsonl.gz'
with gzip.open(train_path,'wt',encoding='utf-8',compresslevel=6) as train:
    # package examples as seeds
    for p in sorted(EXAMPLES.glob('*.sq')):
        code=p.read_text(encoding='utf-8').strip()
        title=re.sub(r'^\d+_','',p.stem).replace('_',' ')
        for task, instr, out in [
            ('code_generation',f'Write a Sansqrit program for: {title}.',code),
            ('code_explanation',f'Explain and reproduce the Sansqrit example {p.name}.',f'This example demonstrates {title}.\n\n```sansqrit\n{code}\n```')]:
            train.write(jdump(base(task,instr,out,tags=['canonical-example']+title.split()[:5],difficulty='hard' if any(x in p.stem for x in ['120','128','150','qec','hierarchical']) else 'medium',source='package-example'))); counts['train']+=1
    # general code generation 12k
    for i in range(12000):
        n=random.choice([2,3,4,5,8,10,12,16,20,32,64,120,121,124,128,132,140,144,150,160,192,256,512,1000])
        engine=random.choice(engines); domain=random.choice(domains); g1=random.choice(single); g2=random.choice(single); tg=random.choice(two); pg=random.choice(param); angle=random.choice(angles)
        q0=random.randrange(min(n,80)); q1=(q0+random.randrange(1,min(n,80)))%n if n>1 else 0; q2=random.randrange(min(n,80))
        p_header='theta = PI / 7\n    ' if angle=='theta' else ''
        extras=[]
        if random.random()<.35: extras.append('print(lookup_profile())')
        if random.random()<.20: extras.append(f'print(export_hardware("{random.choice(providers)}"))')
        if random.random()<.25: extras.append(f'print(estimate_qubits({n}))')
        if random.random()<.25: extras.append(f'print(plan_backend({n}, []))')
        if not extras: extras=[('print(probabilities())' if n<=20 else 'print(engine_nnz())')]
        lines=[f'# Synthetic training case {i}: {domain} structured circuit.',f'simulate({n}, engine="{engine}", n_shards=16, workers=4, use_lookup=true) {{',f'    q = quantum_register({n})',f'    {p_header}{g1}(q[{q0}])',f'    {g2}(q[{q2}])']
        if n>1: lines.append(f'    {tg}(q[{q0}], q[{q1}])')
        if pg in ['CRx','CRy','CRz','CP','RXX','RYY','RZZ','RZX'] and n>1: lines.append(f'    {pg}(q[{q0}], q[{q1}], {angle})')
        else: lines.append(f'    {pg}(q[{q2}], {angle})')
        lines += ['    '+x for x in extras]; lines.append('}')
        code='\n'.join(lines)
        train.write(jdump(base('code_generation',f'Case {i}: write a Sansqrit {domain} circuit with {n} qubits, backend {engine}, and gates {g1}/{g2}/{tg}/{pg}.',code,tags=['code-generation',domain,f'{n}q',engine],difficulty='hard' if n>=120 else 'medium'))); counts['train']+=1
    # large qubit real-world 4k
    for i in range(4000):
        n=random.choice([120,121,124,128,132,140,144,150,160,192,256,512,1000]); domain,body=random.choice(real_bodies)
        engine='stabilizer' if n>=1000 or domain=='cybersecurity' else random.choice(['auto','sharded','hierarchical','mps'])
        code=f'''# Real-world {n}-qubit {domain} Sansqrit template.
simulate({n}, engine="{engine}", n_shards=16, workers=4, use_lookup=true) {{
    q = quantum_register({n})
    {body}
    print("domain", "{domain}")
    print(estimate_qubits({n}))
    print(engine_nnz())
    print(lookup_profile())
}}'''
        train.write(jdump(base('real_world_large_qubit_program',f'Large-qubit case {i}: write a structured {n}-qubit Sansqrit program for {domain}.',code,tags=['real-world',domain,f'{n}q',engine],difficulty='hard'))); counts['train']+=1
    # QEC 4k
    for i in range(4000):
        cn=random.choice(qec_codes); pauli=random.choice(['X','Z','Y']); offset=random.choice([0,1,2,3,4]); baseq=random.choice([0,5,10]); anc=random.choice([12,16,20,24,32]); engine=random.choice(['sparse','stabilizer','density'])
        nq=max(anc+5, {'shor9':24,'steane7':20,'five_qubit':16,'surface3':25}.get(cn,12))
        code=f'''simulate({nq}, engine="{engine}") {{
    q = quantum_register({nq})
    logical = qec_logical("{cn}", base={baseq})
    qec_encode(logical)
    qec_inject_error(logical, "{pauli}", {offset})
    syndrome = qec_syndrome(logical, ancilla_base={anc})
    correction = qec_correct(logical, syndrome)
    print("syndrome", syndrome)
    print("correction", correction)
}}'''
        train.write(jdump(base('qec_code_generation',f'QEC case {i}: create a Sansqrit {cn} program with {pauli} error, syndrome extraction, and correction.',code,tags=['qec',cn,pauli,'syndrome'],difficulty='hard'))); counts['train']+=1
    # hardware 2k
    for i in range(2000):
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
        train.write(jdump(base('hardware_export',f'Hardware export case {i}: generate Sansqrit code for {provider} export using {n} logical qubits.',code,tags=['hardware',provider,f'{n}q'],difficulty='medium'))); counts['train']+=1
    # explanations/backend 3k
    for i in range(3000):
        n=random.choice([50,80,100,120,128,150,256,512,1000,5000]); circ=random.choice(['sparse oracle flags','Clifford graph state','low-entanglement nearest-neighbor ansatz','noisy small code block','dense arbitrary state-vector','hierarchical 10-qubit local blocks'])
        backend='stabilizer' if 'Clifford' in circ else 'mps' if 'low-entanglement' in circ else 'density only for small code blocks' if 'noisy' in circ else 'not feasible beyond modest qubit counts' if 'dense' in circ else 'hierarchical with MPS bridge promotion' if 'hierarchical' in circ else 'sparse/sharded'
        out=f'For a {n}-qubit {circ}, prefer `{backend}`. Use `engine="auto"` so Sansqrit can inspect the interaction graph, estimate memory, choose sparse/sharded, hierarchical tensor shards, stabilizer, MPS, density, GPU, or distributed execution, and use precomputed lookups only where they are mathematically safe.'
        train.write(jdump(base('backend_selection',f'Backend selection case {i}: choose a Sansqrit execution backend for {n} qubits with {circ}.',out,tags=['backend-selection',f'{n}q',circ.replace(' ','-')],difficulty='hard'))); counts['train']+=1
    # algorithms 2k
    for i in range(2000):
        name,body,nq=random.choice(algorithms); engine=random.choice(['auto','sparse','sharded','stabilizer','mps']); style=random.choice(['minimal','commented','lookup-profiled','hardware-exportable','diagnostic'])
        extra='\n    print(lookup_profile())' if style=='lookup-profiled' else ('\n    print(export_qasm3())' if style=='hardware-exportable' else ('\n    print(sansqrit_doctor())' if style=='diagnostic' else ''))
        code=f'''# {style} {name} example
simulate({nq}, engine="{engine}") {{
    {body}{extra}
}}'''
        train.write(jdump(base('algorithm_code_generation',f'Algorithm case {i}: create a {style} Sansqrit program for {name} using {engine}.',code,tags=['algorithm',name.lower().replace(' ','-'),engine,style],difficulty='medium'))); counts['train']+=1
    # bug fix + translation 2k
    for i in range(2000):
        if i%2==0:
            bad='simulate(120, engine="sparse") {\n    q = quantum_register(120)\n    H_all(q)\n}'
            good='simulate(120, engine="stabilizer") {\n    q = quantum_register(120)\n    H_all(q)\n    print(measure_all())\n}'
            out=f'Corrected Sansqrit:\n```sansqrit\n{good}\n```\nExplanation: for Clifford-only all-Hadamard circuits at 120 qubits, use stabilizer to avoid unsafe dense sparse expansion.'
            train.write(jdump(base('bug_fix',f'Bug-fix case {i}: correct an unsafe dense-expansion Sansqrit program.',out,input=f'```sansqrit\n{bad}\n```',tags=['bug-fix','large-qubit'],difficulty='medium'))); counts['train']+=1
        else:
            n=random.choice([2,3,5,10,120]); g=random.choice(single); tg=random.choice(['CNOT','CZ']); engine=random.choice(['sparse','sharded','auto'])
            dsl=f'simulate({n}, engine="{engine}") {{\n    q = quantum_register({n})\n    {g}(q[0])\n    {tg}(q[0], q[1])\n    print(measure_all())\n}}'
            py=f'from sansqrit.runtime import simulate, quantum_register, {g}, {tg}, measure_all\n\nwith simulate({n}, engine="{engine}"):\n    q = quantum_register({n})\n    {g}(q[0])\n    {tg}(q[0], q[1])\n    print(measure_all())'
            train.write(jdump(base('dsl_to_python',f'Translate Sansqrit DSL case {i} into Python API style.',py,input=f'```sansqrit\n{dsl}\n```',tags=['translation','python-api'],difficulty='medium'))); counts['train']+=1

with gzip.open(eval_path,'wt',encoding='utf-8',compresslevel=6) as ev:
    for i in range(1500):
        n=random.choice([120,128,150,256,1000]); topic=random.choice(['QEC','hardware export','lookup profiling','hierarchical bridge','backend estimate','distributed sparse execution'])
        out=f'# Evaluation target: produce valid Sansqrit for {topic} on {n} qubits. The answer should avoid unsafe dense expansion, include diagnostics, and use the correct backend or export/QEC helper.'
        ev.write(jdump(base('eval_prompt',f'Evaluation case {i}: write a concise Sansqrit {topic} program for {n} qubits.',out,tags=['eval',topic.lower().replace(' ','-'),f'{n}q'],difficulty='hard',split='eval',source='synthetic-eval-v1'))); counts['eval']+=1

with gzip.open(pref_path,'wt',encoding='utf-8',compresslevel=6) as pf:
    for i in range(5000):
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
        pf.write(jdump(pref(prompt,chosen,rejected,i))); counts['pref']+=1

manifest={'dataset':VERSION,'author':AUTHOR,'license':LICENSE,'created_utc':datetime.now(timezone.utc).isoformat(),'description':'Extensive synthetic instruction, code, explanation, troubleshooting, QEC, hardware-export and preference dataset for training AI models to understand and generate Sansqrit quantum DSL programs.','files':[{'name':'sansqrit_sft_train_v1.jsonl.gz','schema':'instruction-input-output-v1','records':counts['train']},{'name':'sansqrit_sft_eval_v1.jsonl.gz','schema':'instruction-input-output-v1','records':counts['eval']},{'name':'sansqrit_preference_v1.jsonl.gz','schema':'preference-v1','records':counts['pref']}],'total_records':counts['train']+counts['eval']+counts['pref'],'topics':['DSL syntax','gates','circuits','algorithms','large qubit sparse/sharded execution','hierarchical tensor shards','precomputed lookups','distributed computing','QEC','surface codes','hardware exports','QASM','troubleshooting','backend selection','bug fixing','preference training','DSL to Python','safe dense-state warnings'],'schemas':{'instruction-input-output-v1':{'fields':['id','dataset','schema','language','task_type','instruction','input','output','tags','difficulty','split','source','author','license','quality_notes']},'preference-v1':{'fields':['id','dataset','schema','language','prompt','chosen','rejected','tags','split','source','author','license','quality_notes']}},'intended_use':'Fine-tuning, supervised instruction tuning, DPO/preference training, retrieval-augmented generation, evaluation, prompt engineering and documentation-aware AI model training for Sansqrit DSL.','limitations':'Synthetic data is generated from templates and package examples. It should be supplemented with human-reviewed traces and verified circuit outputs before safety-critical use.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True),encoding='utf-8')
readme=['# Sansqrit Synthetic Training Dataset','', 'Packaged compressed JSONL datasets for AI/ML training on Sansqrit DSL.', '', '## Manifest', '```json', json.dumps(manifest, indent=2), '```', '', '## Usage', '```python', 'from sansqrit.dataset import dataset_info, load_training_records', 'print(dataset_info())', 'for row in load_training_records("sft_train", limit=3):', '    print(row["instruction"])', '```']
(OUT/'README.md').write_text('\n'.join(readme),encoding='utf-8')
print(json.dumps(manifest, indent=2))
