#!/usr/bin/env bash
set -euo pipefail
for f in examples/*.sq; do
  echo "Running $f"
  sansqrit run "$f" >/dev/null
done
