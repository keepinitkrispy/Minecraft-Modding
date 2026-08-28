from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path.home() / "solbridge-workspace"
BASE = ROOT / "autoloop"
INBOX = BASE / "inbox"
PROOFS = BASE / "proofs"
ARM = BASE / "reboot-arm.json"
CONSUMED = BASE / "reboot-arm-consumed.json"


def boot_id() -> str:
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()


def main() -> None:
    if not ARM.exists():
        return
    try:
        arm = json.loads(ARM.read_text())
    except Exception:
        return
    old = str(arm.get("old_boot_id") or "")
    new = boot_id()
    if not old or new == old:
        return

    BASE.mkdir(parents=True, exist_ok=True)
    INBOX.mkdir(parents=True, exist_ok=True)
    PROOFS.mkdir(parents=True, exist_ok=True)
    mid = str(arm.get("mission_id") or "reboot-survival-proof")
    goal = str(arm.get("goal") or "Inspect the live Android state after reboot and execute exactly one safe launch action that changes the foreground app, then verify it.")
    detected = {
        "verified_reboot": True,
        "old_boot_id": old,
        "new_boot_id": new,
        "armed_at": arm.get("armed_at"),
        "detected_at": time.time(),
        "mission_id": mid,
    }
    (PROOFS / "reboot-detected.json").write_text(json.dumps(detected, indent=2))
    mission = {
        "id": mid,
        "created_at": time.time(),
        "goal": goal,
        "attempts": 0,
    }
    (INBOX / f"{mid}.json").write_text(json.dumps(mission, indent=2))
    CONSUMED.write_text(json.dumps({**arm, **detected}, indent=2))
    ARM.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
