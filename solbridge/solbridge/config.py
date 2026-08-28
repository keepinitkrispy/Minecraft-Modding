from __future__ import annotations
import json, os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG = Path.home() / ".config" / "solbridge" / "config.json"

@dataclass
class Config:
    repo: str
    token: str
    device_id: str = "pixel"
    poll_seconds: int = 15
    workspace: Path = field(default_factory=lambda: Path.home() / "solbridge-workspace")
    allow_shell: bool = False
    shell_timeout: int = 120
    allowed_shell_prefixes: list[str] = field(default_factory=lambda: ["git ", "python ", "python3 ", "pytest", "ls", "pwd", "find ", "du ", "df ", "zip ", "unzip "])

    @classmethod
    def load(cls, path: str | os.PathLike | None = None) -> "Config":
        path = Path(path or os.getenv("SOLBRIDGE_CONFIG", DEFAULT_CONFIG))
        data = json.loads(path.read_text())
        token = os.getenv("SOLBRIDGE_GITHUB_TOKEN") or data.get("token", "")
        repo = os.getenv("SOLBRIDGE_REPO") or data.get("repo", "")
        if not token or not repo:
            raise RuntimeError("Missing GitHub token or repository")
        return cls(
            repo=repo,
            token=token,
            device_id=data.get("device_id", "pixel"),
            poll_seconds=int(data.get("poll_seconds", 15)),
            workspace=Path(data.get("workspace", str(Path.home() / "solbridge-workspace"))).expanduser(),
            allow_shell=bool(data.get("allow_shell", False)),
            shell_timeout=int(data.get("shell_timeout", 120)),
            allowed_shell_prefixes=list(data.get("allowed_shell_prefixes", cls.__dataclass_fields__["allowed_shell_prefixes"].default_factory())),
        )
