from __future__ import annotations
import base64, csv, hashlib, os, tarfile, zipfile, io, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NAME='sansqrit'; VERSION='0.3.6'
DIST=ROOT/'dist'; DIST.mkdir(exist_ok=True)
for p in DIST.glob('*'): p.unlink()
DISTINFO=f'{NAME}-{VERSION}.dist-info'
WHEEL_NAME=f'{NAME}-{VERSION}-py3-none-any.whl'; SDIST_NAME=f'{NAME}-{VERSION}.tar.gz'

def hash_file(data: bytes):
    digest=base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b'=').decode('ascii')
    return f'sha256={digest}', str(len(data))
readme=(ROOT/'README.md').read_text(encoding='utf-8')
metadata=f'''Metadata-Version: 2.3
Name: {NAME}
Version: {VERSION}
Summary: Sansqrit quantum DSL by Karthik V with adaptive planning, distributed clusters, QEC, GPU/cuQuantum adapters, QASM3, verification, and AI datasets.
Author: Karthik V
Maintainer: Karthik V
License: MIT
Requires-Python: >=3.10
Requires-Dist: numpy>=1.26
Description-Content-Type: text/markdown
Provides-Extra: dev
Provides-Extra: qec
Provides-Extra: tensor
Provides-Extra: gpu
Provides-Extra: qiskit
Provides-Extra: cirq
Provides-Extra: braket
Provides-Extra: pennylane
Provides-Extra: interop
Provides-Extra: ray
Provides-Extra: dask
Provides-Extra: mpi
Provides-Extra: cuquantum
Provides-Extra: all
Requires-Dist: pytest>=8; extra == "dev"
Requires-Dist: build>=1; extra == "dev"
Requires-Dist: twine>=5; extra == "dev"
Requires-Dist: stim>=1.13; extra == "qec"
Requires-Dist: pymatching>=2.1; extra == "qec"
Requires-Dist: cupy-cuda12x>=13; extra == "gpu"
Requires-Dist: qiskit>=1; extra == "qiskit"
Requires-Dist: cirq-core>=1.4; extra == "cirq"
Requires-Dist: amazon-braket-sdk>=1.80; extra == "braket"
Requires-Dist: pennylane>=0.40; extra == "pennylane"
Requires-Dist: ray>=2; extra == "ray"
Requires-Dist: dask[distributed]>=2024; extra == "dask"
Requires-Dist: mpi4py>=4; extra == "mpi"
Requires-Dist: cuquantum-python-cu12>=24; extra == "cuquantum"
Keywords: quantum,dsl,sparse,sharding,lookup,stabilizer,qec,surface-code,mps,gpu,cuquantum,qasm,qiskit,azure,aws,braket,cirq,pennylane,ai-training
Classifier: Development Status :: 3 - Alpha
Classifier: Intended Audience :: Developers
Classifier: Intended Audience :: Education
Classifier: Intended Audience :: Science/Research
Classifier: Programming Language :: Python :: 3
Classifier: Topic :: Scientific/Engineering :: Physics

'''+readme
wheel_meta='''Wheel-Version: 1.0
Generator: sansqrit-manual-build-fast
Root-Is-Purelib: true
Tag: py3-none-any
'''
entry_points='''[console_scripts]
sansqrit = sansqrit.cli:main
'''
records=[]
wheel_path=DIST/WHEEL_NAME
with zipfile.ZipFile(wheel_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
    def add_bytes(arc, data: bytes):
        z.writestr(arc, data)
        h,l=hash_file(data); records.append((arc,h,l))
    def add_file(path: Path, arc: str):
        data=path.read_bytes(); z.writestr(arc, data)
        h,l=hash_file(data); records.append((arc,h,l))
    files=[p for p in sorted((ROOT/'src'/'sansqrit').rglob('*')) if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.pyc')]
    for i,path in enumerate(files,1):
        add_file(path, str(path.relative_to(ROOT/'src')).replace(os.sep,'/'))
    add_bytes(f'{DISTINFO}/METADATA', metadata.encode())
    add_bytes(f'{DISTINFO}/WHEEL', wheel_meta.encode())
    add_bytes(f'{DISTINFO}/entry_points.txt', entry_points.encode())
    add_bytes(f'{DISTINFO}/top_level.txt', b'sansqrit\n')
    rows=[[arc,h,l] for arc,h,l in records]+[[f'{DISTINFO}/RECORD','','']]
    s=io.StringIO(); csv.writer(s, lineterminator='\n').writerows(rows)
    z.writestr(f'{DISTINFO}/RECORD', s.getvalue().encode())
# sdist
sdist_path=DIST/SDIST_NAME
with tarfile.open(sdist_path,'w:gz',compresslevel=1) as tar:
    root=f'{NAME}-{VERSION}'
    for item in ['pyproject.toml','README.md','LICENSE','MANIFEST.in']:
        p=ROOT/item
        if p.exists(): tar.add(p, arcname=f'{root}/{item}', recursive=False)
    for base in ['src','docs','examples','tests','scripts']:
        b=ROOT/base
        if b.exists():
            for p in sorted(b.rglob('*')):
                if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.pyc'):
                    tar.add(p, arcname=f'{root}/{p.relative_to(ROOT)}', recursive=False)
print(wheel_path)
print(sdist_path)
os._exit(0)
