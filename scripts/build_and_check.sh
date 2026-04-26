#!/usr/bin/env bash
set -euo pipefail
python -m pytest
python -m build
python -m twine check dist/*
