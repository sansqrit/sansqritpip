# Sansqrit v0.3.0 Validation Notes

Validated in this environment:

```bash
python -m py_compile src/sansqrit/*.py
PYTHONPATH=src python scripts/custom_test_runner.py
PYTHONPATH=src python scripts/compile_all_examples.py
PYTHONPATH=src python scripts/run_all_examples.py
python -m build --sdist --wheel --outdir dist
python -m venv /mnt/data/sansqrit_v03_wheel_test
/mnt/data/sansqrit_v03_wheel_test/bin/python -m pip install dist/sansqrit-0.3.0-py3-none-any.whl
/mnt/data/sansqrit_v03_wheel_test/bin/python -c "import sansqrit; print(sansqrit.__version__)"
```

Results:

- Python source compiled successfully.
- Custom tests: 14 passed, 0 failed.
- Example translation: 250 examples, 0 bad.
- Example execution: 250 examples, 0 bad.
- Built artifacts: `sansqrit-0.3.0.tar.gz` and `sansqrit-0.3.0-py3-none-any.whl`.
- Wheel install check: imported `sansqrit` version `0.3.0`.
- Wheel package-data check: 250 `.sq` examples included under `sansqrit/examples`; docs included under `sansqrit/docs`.

Not performed here:

- `twine check dist/*`, because `twine` is not installed in this environment. Run `python -m pip install twine` and then `python -m twine check dist/*` before uploading.
- Real GPU execution, because CUDA/CuPy hardware availability is environment-dependent.
- External SDK formal verification unless optional SDK dependencies are installed.
