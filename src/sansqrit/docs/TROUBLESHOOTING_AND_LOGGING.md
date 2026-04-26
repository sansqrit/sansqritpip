# Troubleshooting and logging

## CLI

```bash
sansqrit doctor
sansqrit backends
sansqrit estimate 120
sansqrit troubleshoot lookup
sansqrit hardware
```

## DSL logging

```sansqrit
enable_logging("INFO", "sansqrit.log")
log_sansqrit_event("program_start", {"name": "sparse_150"})
```

## Common issues

- Slow 120-qubit run: use `estimate_qubits`, `plan_backend`, `stabilizer`, `mps`, or `hierarchical`.
- Missing lookup files: verify `sansqrit/data/` exists in the installed package.
- Cloud export fails: install the provider extra or use OpenQASM fallback.
- Density backend memory issue: density matrices scale as `4^n`.
- GPU missing: install CuPy matching your CUDA runtime.
