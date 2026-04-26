import importlib.util, pathlib, traceback, sys
base = pathlib.Path('tests')
failed = 0
for file in base.glob('test_*.py'):
    spec = importlib.util.spec_from_file_location(file.stem, file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for name in dir(mod):
        if name.startswith('test_'):
            try:
                getattr(mod, name)()
                print('PASS', file.name, name)
            except Exception:
                failed += 1
                print('FAIL', file.name, name)
                traceback.print_exc()
print('failed', failed)
sys.exit(failed)
