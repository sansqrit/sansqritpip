"""Sansqrit source translator and runner.

The Python implementation intentionally uses a Python-like subset with braces so
scientists can write compact scripts while keeping the runtime easy to inspect.
The translator is not a security sandbox. Run only trusted Sansqrit programs.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .errors import SansqritSyntaxError
from .runtime import make_globals

_LAMBDA_RE = re.compile(r"fn\s*\(([^)]*)\)\s*=>\s*([^,\)\]\}\n]+(?:\([^\n]*\))?)")


def _replace_words_outside_strings(line: str) -> str:
    # Lightweight replacements for DSL literals.
    out = []
    i = 0
    in_str: str | None = None
    while i < len(line):
        ch = line[i]
        if in_str:
            out.append(ch)
            if ch == "\\" and i + 1 < len(line):
                i += 1; out.append(line[i])
            elif ch == in_str:
                in_str = None
            i += 1
            continue
        if ch in {'"', "'"}:
            in_str = ch
            out.append(ch); i += 1; continue
        if line.startswith("true", i) and (i == 0 or not line[i-1].isalnum()) and (i+4 == len(line) or not line[i+4].isalnum()):
            out.append("True"); i += 4; continue
        if line.startswith("false", i) and (i == 0 or not line[i-1].isalnum()) and (i+5 == len(line) or not line[i+5].isalnum()):
            out.append("False"); i += 5; continue
        if line.startswith("null", i) and (i == 0 or not line[i-1].isalnum()) and (i+4 == len(line) or not line[i+4].isalnum()):
            out.append("None"); i += 4; continue
        out.append(ch); i += 1
    return "".join(out)


def _strip_comment(line: str) -> str:
    in_str: str | None = None
    for i, ch in enumerate(line):
        if in_str:
            if ch == "\\":
                continue
            if ch == in_str:
                in_str = None
        else:
            if ch in {'"', "'"}:
                in_str = ch
            elif ch == "#":
                return line[:i]
    return line


def _convert_lambda(expr: str) -> str:
    # Repeatedly convert fn(x) => x*x to lambda x: x*x in expressions.
    prev = None
    while prev != expr:
        prev = expr
        expr = re.sub(r"fn\s*\(([^)]*)\)\s*=>\s*([^,\)\]\}\n]+)", r"lambda \1: \2", expr)
    return expr


def _convert_pipeline(expr: str) -> str:
    if "|>" not in expr:
        return expr
    parts = [p.strip() for p in expr.split("|>")]
    value = parts[0]
    for stage in parts[1:]:
        value = f"__pipe__({value}, {stage})"
    return value


def _convert_expr(expr: str) -> str:
    expr = _replace_words_outside_strings(expr)
    expr = _convert_lambda(expr)
    expr = _convert_pipeline(expr)
    return expr


def translate(source: str, *, filename: str = "<sansqrit>") -> str:
    """Translate Sansqrit DSL source to Python source."""
    py_lines: list[str] = [f"# Translated from {filename}"]
    indent = 0
    pending_dedent_for_else = False

    for raw_no, raw in enumerate(source.splitlines(), start=1):
        line = _strip_comment(raw).strip()
        if not line:
            continue
        while line.startswith("}"):
            indent = max(0, indent - 1)
            line = line[1:].strip()
        if not line:
            continue
        opens = line.endswith("{")
        if opens:
            line = line[:-1].rstrip()
        # Leading DSL forms.
        if line.startswith("let "):
            line = line[4:].strip()
        elif line.startswith("const "):
            line = line[6:].strip()
        elif line.startswith("fn "):
            m = re.match(r"fn\s+([A-Za-z_]\w*)\s*\((.*)\)(?:\s*->\s*[^\s{]+)?\s*$", line)
            if not m:
                raise SansqritSyntaxError(f"{filename}:{raw_no}: invalid function declaration")
            line = f"def {m.group(1)}({m.group(2)}):"
            opens = False
        elif line.startswith("simulate"):
            m = re.match(r"simulate(?:\((.*)\))?$", line)
            if not m:
                raise SansqritSyntaxError(f"{filename}:{raw_no}: invalid simulate block")
            args = _convert_expr(m.group(1) or "")
            line = f"with simulate({args}) as __engine__:"
            opens = False
        elif line.startswith("shard "):
            m = re.match(r"shard\s+([A-Za-z_]\w*)\s*\[\s*(\d+)\s*\.\.\s*(\d+)\s*\]$", line)
            if not m:
                raise SansqritSyntaxError(f"{filename}:{raw_no}: invalid shard declaration; use shard name [start..end]")
            line = f'{m.group(1)} = shard("{m.group(1)}", {m.group(2)}, {m.group(3)})'
            opens = False
        elif line.startswith("apply "):
            m = re.match(r"apply\s+([A-Za-z_]\w*)\s+on\s+(.+)$", line)
            if not m:
                raise SansqritSyntaxError(f"{filename}:{raw_no}: invalid apply statement; use apply H on block")
            gate = m.group(1)
            rest = m.group(2).strip()
            rest = re.sub(r"\s+bridge_mode\s*=\s*[A-Za-z_]\w*", "", rest).strip()
            if re.match(r"^[A-Za-z_]\w*$", rest):
                line = f'apply_block("{gate}", {rest})'
            else:
                line = f'{gate}({rest})'
            opens = False
        elif line.startswith("else if "):
            line = "elif " + line[8:].strip() + ":"
            opens = False
        elif line == "else":
            line = "else:"
            opens = False
        elif line.startswith(("if ", "for ", "while ")):
            line = _convert_expr(line) + ":"
            opens = False
        else:
            # Keep Python's def/class/try compatibility if users write it.
            line = _convert_expr(line)
            if opens:
                line = line + ":"
                opens = False
        # Convert assignment RHS and return expressions for pipelines/lambdas.
        if not line.lstrip().startswith(("if ", "for ", "while ", "elif ", "with ", "def ", "else:")):
            if line.startswith("return "):
                line = "return " + _convert_expr(line[7:].strip())
            elif "=" in line and not any(op in line for op in ["==", "!=", "<=", ">="]):
                left, right = line.split("=", 1)
                line = left.rstrip() + " = " + _convert_expr(right.strip())
        if line.endswith(":") and line.startswith(("elif ", "else:")):
            # A previous leading '}' already dedented us for else/elif.
            pass
        py_lines.append("    " * indent + line)
        if line.endswith(":"):
            indent += 1
    return "\n".join(py_lines) + "\n"


def run_code(source: str, *, filename: str = "<sansqrit>", env: dict[str, Any] | None = None) -> dict[str, Any]:
    env = make_globals() if env is None else env
    py = translate(source, filename=filename)
    env["__translated_python__"] = py
    exec(compile(py, filename, "exec"), env, env)
    return env


def run_file(path: str | Path, *, env: dict[str, Any] | None = None) -> dict[str, Any]:
    p = Path(path)
    return run_code(p.read_text(encoding="utf-8"), filename=str(p), env=env)
