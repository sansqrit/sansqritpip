from __future__ import annotations
import base64, csv, hashlib, os, tarfile, time, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NAME='sansqrit'
VERSION='0.3.4'
DIST=ROOT/'dist'
DIST.mkdir(exist_ok=True)
for p in DIST.glob('*'): p.unlink()
WHEEL_NAME=f'{NAME}-{VERSION}-py3-none-any.whl'
SDIST_NAME=f'{NAME}-{VERSION}.tar.gz'
DISTINFO=f'{NAME}-{VERSION}.dist-info'

def hash_file(data: bytes):
    digest=base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode('ascii')
    return f'sha256={digest}', str(len(data))

metadata=f'''Metadata-Version: 2.3
Name: {NAME}
Version: {VERSION}
Summary: Sansqrit quantum DSL by Karthik V with sparse/sharded lookup execution, hierarchical tensor shards, QEC, hardware exports, diagnostics, and packaged AI/ML training datasets.
Author: Karthik V
Maintainer: Karthik V
License: MIT
Requires-Python: >=3.10
Keywords: quantum,dsl,simulator,sparse,sharding,lookup,stabilizer,qec,surface-code,tensor-network,hierarchical-tensor,mps,qasm,qiskit,braket,cirq,pennylane,education,research,ai-training
Classifier: Development Status :: 3 - Alpha
Classifier: Intended Audience :: Developers
Classifier: Intended Audience :: Education
Classifier: Intended Audience :: Science/Research
Classifier: Programming Language :: Python :: 3
Classifier: Programming Language :: Python :: 3 :: Only
Classifier: Programming Language :: Python :: 3.10
Classifier: Programming Language :: Python :: 3.11
Classifier: Programming Language :: Python :: 3.12
Classifier: Programming Language :: Python :: 3.13
Classifier: Topic :: Scientific/Engineering :: Physics
Classifier: Topic :: Software Development :: Interpreters
Provides-Extra: dev
Provides-Extra: qec
Provides-Extra: tensor
Provides-Extra: gpu
Provides-Extra: qiskit
Provides-Extra: cirq
Provides-Extra: braket
Provides-Extra: pennylane
Provides-Extra: interop
Provides-Extra: all
Description-Content-Type: text/markdown

'''+(ROOT/'README.md').read_text(encoding='utf-8')
wheel_meta='''Wheel-Version: 1.0
Generator: sansqrit-manual-build
Root-Is-Purelib: true
Tag: py3-none-any
'''
entry_points='''[console_scripts]
sansqrit = sansqrit.cli:main
'''
top_level='sansqrit\n'

wheel_path=DIST/WHEEL_NAME
records=[]
with zipfile.ZipFile(wheel_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    def add_bytes(arc, data: bytes):
        z.writestr(arc, data)
        h,l=hash_file(data); records.append((arc,h,l))
    def add_file(path: Path, arc: str):
        data=path.read_bytes()
        z.writestr(arc, data)
        h,l=hash_file(data); records.append((arc,h,l))
    for path in sorted((ROOT/'src'/'sansqrit').rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            add_file(path, str(path.relative_to(ROOT/'src')).replace(os.sep,'/'))
    add_bytes(f'{DISTINFO}/METADATA', metadata.encode('utf-8'))
    add_bytes(f'{DISTINFO}/WHEEL', wheel_meta.encode('utf-8'))
    add_bytes(f'{DISTINFO}/entry_points.txt', entry_points.encode('utf-8'))
    add_bytes(f'{DISTINFO}/top_level.txt', top_level.encode('utf-8'))
    # RECORD last
    record_arc=f'{DISTINFO}/RECORD'
    output=[]
    for arc,h,l in records:
        output.append([arc,h,l])
    output.append([record_arc,'',''])
    import io
    s=io.StringIO(); w=csv.writer(s, lineterminator='\n'); w.writerows(output)
    z.writestr(record_arc, s.getvalue().encode('utf-8'))

# sdist
sdist_root=f'{NAME}-{VERSION}'
sdist_path=DIST/SDIST_NAME
with tarfile.open(sdist_path,'w:gz') as tar:
    def add(path: Path, arc: str):
        tar.add(path, arcname=f'{sdist_root}/{arc}', recursive=False)
    for item in ['pyproject.toml','README.md']:
        add(ROOT/item, item)
    for base in ['src','docs','examples','tests','scripts']:
        b=ROOT/base
        if b.exists():
            for p in sorted(b.rglob('*')):
                if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.pyc'):
                    add(p, str(p.relative_to(ROOT)))
print(wheel_path)
print(sdist_path)
