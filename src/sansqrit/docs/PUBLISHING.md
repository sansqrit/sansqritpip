# Publishing Sansqrit to PyPI

This project uses a modern `pyproject.toml` source layout.

## Before publishing

- Replace placeholder URLs in `pyproject.toml` with your repository and documentation URLs.
- Confirm the package name on TestPyPI and PyPI.
- Keep `README.md` as valid Markdown because PyPI uses it as the long description.
- Ensure examples and docs are included in both the source distribution and wheel.

## Commands

```bash
python -m pip install --upgrade build twine
rm -rf build dist *.egg-info src/*.egg-info
python -m build --sdist --wheel
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*
# after testing:
python -m twine upload dist/*
```

## Test install

```bash
python -m venv /tmp/sansqrit-test
source /tmp/sansqrit-test/bin/activate
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ sansqrit
python -c "import sansqrit; print(sansqrit.__version__)"
```
