from pathlib import Path
import os, subprocess, sys, textwrap
base = Path('tests')
passed = failed = 0
for file in sorted(base.glob('test_*.py')):
    # discover test names without importing package-heavy modules in parent
    src = file.read_text()
    names = [line.split('def ',1)[1].split('(',1)[0] for line in src.splitlines() if line.startswith('def test_')]
    for name in sorted(names):
        code = f"""
import importlib.util, pathlib, traceback, os
file = pathlib.Path({str(file)!r})
spec = importlib.util.spec_from_file_location(file.stem, file)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
try:
    getattr(mod, {name!r})()
except Exception:
    traceback.print_exc()
    os._exit(1)
os._exit(0)
"""
        env = os.environ.copy(); env['PYTHONPATH'] = 'src'
        print('RUN', file.name, name, flush=True)
        res = subprocess.run([sys.executable, '-c', code], env=env, timeout=60)
        if res.returncode == 0:
            passed += 1; print('PASS', file.name, name, flush=True)
        else:
            failed += 1; print('FAIL', file.name, name, 'returncode', res.returncode, flush=True)
print('tests:', passed, 'passed,', failed, 'failed', flush=True)
os._exit(1 if failed else 0)
