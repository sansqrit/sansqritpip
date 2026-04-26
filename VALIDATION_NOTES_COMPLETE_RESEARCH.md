# Validation notes for Sansqrit v0.3.3 complete research package

Performed in this container:

```bash
/usr/bin/python3 -m py_compile src/sansqrit/*.py
PYTHONPATH=src /usr/bin/python3 scripts/compile_all_examples.py
```

Results:

```text
Python source compiled successfully.
examples 300 bad 0
```

New examples 278-300 were executed individually with timeouts and passed. CLI smoke checks passed:

```bash
PYTHONPATH=src /usr/bin/python3 -m sansqrit.cli doctor
PYTHONPATH=src /usr/bin/python3 -m sansqrit.cli estimate 120
PYTHONPATH=src /usr/bin/python3 -m sansqrit.cli hardware
```

Wheel inspection/import smoke check:

```bash
unzip sansqrit-0.3.3-py3-none-any.whl
PYTHONPATH=/tmp/sqwheel /usr/bin/python3 -c "import sansqrit; print(sansqrit.__version__)"
```

Result:

```text
version 0.3.3
examples 300
docs 16
targets 9
```

Caveat: `python -m build` and `twine check` were not used because build/twine were not reliably installed in this container. The wheel and sdist were created manually with standard wheel metadata, METADATA, WHEEL, entry_points.txt and RECORD.
