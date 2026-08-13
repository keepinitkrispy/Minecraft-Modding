#!/usr/bin/env python3
"""Fail-closed wrapper around Mojang Minecraft Creator Tools validation.

Why this exists: a previous CI command accidentally passed `-v`, which means
`--version` in MCT, not verbose. It printed a version number, exited 0, and was
mistaken for a validation pass. This wrapper owns the exact command invocation
and refuses to return PASS unless it can parse an actual validation payload.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def extract_payload(text: str) -> dict:
    payloads = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("command") == "validate":
            payloads.append(value)
    if not payloads:
        raise RuntimeError(
            "MCT produced no machine-readable validate payload. "
            "This is NOT a validation pass."
        )
    return payloads[-1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    parser.add_argument("--suite", choices=("all", "addon", "main", "currentplatform"), default="all")
    parser.add_argument("--fail-on-warnings", action="store_true")
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()

    command = [
        "mct",
        "validate",
        args.suite,
        "-i",
        str(args.project.resolve()),
        "--single",
        "--json",
    ]
    proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout or ""
    print(text, end="" if text.endswith("\n") else "\n")
    if args.log:
        args.log.parent.mkdir(parents=True, exist_ok=True)
        args.log.write_text(text, encoding="utf-8")

    try:
        payload = extract_payload(text)
    except RuntimeError as exc:
        print(f"VALIDATION HARNESS FAILURE: {exc}", file=sys.stderr)
        return 2

    if payload.get("suite") != args.suite:
        print(
            f"VALIDATION HARNESS FAILURE: requested suite {args.suite!r} but payload reports {payload.get('suite')!r}",
            file=sys.stderr,
        )
        return 2
    if int(payload.get("projects", 0)) < 1:
        print("VALIDATION HARNESS FAILURE: no project was actually validated", file=sys.stderr)
        return 2

    summary = payload.get("validationSummary")
    if not isinstance(summary, dict):
        print("VALIDATION HARNESS FAILURE: validationSummary missing", file=sys.stderr)
        return 2

    errors = int(summary.get("errors", 0))
    warnings = int(summary.get("warnings", 0))
    info = int(summary.get("info", 0))
    print(f"MCT VERIFIED PAYLOAD: suite={args.suite} errors={errors} warnings={warnings} info={info}")

    if proc.returncode != 0:
        print(f"MCT process exited {proc.returncode}", file=sys.stderr)
        return proc.returncode or 1
    if errors:
        return 1
    if args.fail_on_warnings and warnings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
