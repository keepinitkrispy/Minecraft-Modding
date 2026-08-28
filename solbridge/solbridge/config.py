from __future__ import annotations
import json, os, shutil, subprocess
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG = Path.home() / ".config" / "solbridge" / "config.json"

def _gh_token() -> str:
    if not shutil.which("gh"):
        return ""
    p = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=15)
    return p.stdout.strip() if p.returncode == 0 else ""

@dataclass
class Config:
    repo: str
    token: str
    device_id: str = "pixel"
    poll_seconds: int = 15
    workspace: Path = field(default_factory=lambda: Path.home() / "solbridge-workspace")
    source_dir: Path = field(default_factory=lambda: Path.home() / ".local" / "share" / "solbridge-src")
    allow_shell: bool = False
    shell_timeout: int = 120
    allowed_shell_prefixes: list[str] = field(default_factory=lambda: ["git ", "python ", "python3 ", "pytest", "ls", "pwd", "find ", "du ", "df ", "zip ", "unzip "])

    @classmethod
    def load(cls, path: str | os.PathLike | None = None) -> "Config":
        path = Path(path or os.getenv("SOLBRIDGE_CONFIG", DEFAULT_CONFIG))
        data = json.loads(path.read_text())
        token = os.getenv("SOLBRIDGE_GITHUB_TOKEN") or data.get("token", "") or _gh_token()
        repo = os.getenv("SOLBRIDGE_REPO") or data.get("repo", "")
        if not token or not repo:
            raise RuntimeError("Missing GitHub authentication or repository")
        return cls(
            repo=repo,
            token=token,
            device_id=data.get("device_id", "pixel"),
            poll_seconds=int(data.get("poll_seconds", 15)),
            workspace=Path(data.get("workspace", str(Path.home() / "solbridge-workspace"))).expanduser(),
            source_dir=Path(data.get("source_dir", str(Path.home() / ".local" / "share" / "solbridge-src"))).expanduser(),
            allow_shell=bool(data.get("allow_shell", False)),
            shell_timeout=int(data.get("shell_timeout", 120)),
            allowed_shell_prefixes=list(data.get("allowed_shell_prefixes", cls.__dataclass_fields__["allowed_shell_prefixes"].default_factory())),
        )
