# Upload Sansqrit 0.3.6 to PyPI

This package uses version `0.3.6` because PyPI will reject reusing an already-uploaded version filename.

```bash
python -m pip install --upgrade twine
python -m twine check dist/*
python -m twine upload dist/*
```

When prompted:

```text
username: __token__
password: <your PyPI API token>
```

For TestPyPI:

```bash
python -m twine upload --repository testpypi dist/*
```

The `dist/` folder contains the wheel. A wheel-only upload is accepted by PyPI. If you need a traditional source distribution, rebuild in your local Python packaging environment with:

```bash
python -m pip install --upgrade build
python -m build --sdist --wheel
```
