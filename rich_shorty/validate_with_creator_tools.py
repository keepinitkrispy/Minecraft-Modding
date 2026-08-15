#!/usr/bin/env python3
"""Fail-closed wrapper around Mojang Minecraft Creator Tools validation."""
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
        raise RuntimeError("MCT produced no machine-readable validate payload. This is NOT a validation pass.")
    return payloads[-1]


def _project_declares_server_beta(project: Path) -> bool:
    manifest = project / "BP" / "manifest.json"
    try:
        obj = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:
        return False
    for dep in obj.get("dependencies", []):
        if isinstance(dep, dict) and dep.get("module_name") == "@minecraft/server":
            return dep.get("version") == "beta"
    return False


def _validation_items(payload: dict) -> list[dict]:
    result: list[dict] = []
    for project in payload.get("projects", []):
        if not isinstance(project, dict):
            continue
        for item in project.get("items", []):
            if isinstance(item, dict):
                result.append(item)
    return result


def _is_exact_beta_parser_bug(item: dict) -> bool:
    """Creator Tools 0.17.7 CHKMANIF rejects Microsoft's documented literal 'beta'."""
    return (
        item.get("type") == "error"
        and item.get("generatorId") == "CHKMANIF"
        and item.get("message") == "Unable To Parse Version"
        and item.get("data") == "beta"
        and item.get("path") == "/BP/manifest.json"
    )


def _is_beta_parser_testfail(item: dict) -> bool:
    return (
        item.get("type") == "testFail"
        and item.get("generatorId") == "CHKMANIF"
        and item.get("message") == "Found 1 error in Manifest Validation check"
    )


def exact_beta_parser_bug_only(payload: dict, project: Path) -> bool:
    """Return true only when MCT failed solely on its numeric parser for 'beta'."""
    if not _project_declares_server_beta(project):
        return False
    items = _validation_items(payload)
    errors = [i for i in items if i.get("type") == "error"]
    testfails = [i for i in items if i.get("type") == "testFail"]
    warnings = [i for i in items if i.get("type") == "warning"]
    if warnings:
        return False
    if int(payload.get("errors", -1)) != 2:
        return False
    if len(errors) != 1 or not _is_exact_beta_parser_bug(errors[0]):
        return False
    if len(testfails) != 1 or not _is_beta_parser_testfail(testfails[0]):
        return False

    # SCRIPTMODULE must independently recognize the beta dependency. This keeps
    # the allowlist tied to the exact contradictory Creator Tools behavior, not
    # merely to the string "beta" appearing somewhere in the manifest.
    recognized = any(
        i.get("generatorId") == "SCRIPTMODULE"
        and i.get("type") == "info"
        and i.get("message") == "Behavior pack dependency on beta at @minecraft/server"
        and i.get("data") == "beta"
        and i.get("path") == "/BP/manifest.json"
        for i in items
    )
    return recognized


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    parser.add_argument("--suite", choices=("all", "addon", "main", "currentplatform"), default="all")
    parser.add_argument("--fail-on-warnings", action="store_true")
    parser.add_argument("--allow-beta-version-parser-bug", action="store_true")
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()

    command = ["mct", "validate", args.suite, "-i", str(args.project.resolve()), "--single", "--json"]
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
            generated_items += sum(1 for item in items if isinstance(item, dict) and item.get("generatorId"))
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
    print(f"MCT VERIFIED PAYLOAD: requested_suite={args.suite} projects={len(projects)} test_items={generated_items} errors={errors} warnings={warnings} recommendations={recommendations}")

    allowed_beta_bug = (
        args.allow_beta_version_parser_bug
        and exact_beta_parser_bug_only(payload, args.project)
    )
    if allowed_beta_bug:
        print(
            "MCT KNOWN-BUG ALLOWLIST: accepted only CHKMANIF Unable To Parse Version(beta); "
            "SCRIPTMODULE independently recognized @minecraft/server beta; no other MCT failures or warnings were present."
        )
        return 0

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
