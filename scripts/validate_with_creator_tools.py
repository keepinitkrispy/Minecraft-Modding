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

    # MCT 0.17.7's JSON payload does not echo the selected suite. Verify instead
    # that it is an actual validate result with one or more project result sets,
    # aggregate counters, and concrete generated test items. A plain version
    # response or unrelated JSON therefore cannot pass this gate.
    projects = payload.get("projects")
    if not isinstance(projects, list) or not projects:
        print("VALIDATION HARNESS FAILURE: no project validation results present", file=sys.stderr)
        return 2
    generated_items = 0
    for project in projects:
        if not isinstance(project, dict):
            continue
        items = project.get("items")
        if isinstance(items, list):
            generated_items += sum(
                1 for item in items
                if isinstance(item, dict) and item.get("generatorId")
            )
    if generated_items == 0:
        print("VALIDATION HARNESS FAILURE: payload contains no generated validation items", file=sys.stderr)
        return 2

    for key in ("errors", "warnings", "recommendations"):
        if key not in payload:
            print(f"VALIDATION HARNESS FAILURE: aggregate field {key!r} missing", file=sys.stderr)
            return 2

    errors = int(payload["errors"])
    warnings = int(payload["warnings"])
    recommendations = int(payload["recommendations"])
    print(
        f"MCT VERIFIED PAYLOAD: requested_suite={args.suite} "
        f"projects={len(projects)} test_items={generated_items} "
        f"errors={errors} warnings={warnings} recommendations={recommendations}"
    )

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
