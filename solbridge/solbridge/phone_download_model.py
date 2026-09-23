"""Download and verify the free local model; safe to rerun after interruption."""
import hashlib
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q4_K_M.gguf"
SHA256 = "72c5c3cb38fa32d5256e2fe30d03e7a64c6c79e668ad84057e3bd66e250b24fb"
SIZE = 1282439584
dst = Path.home() / "solbridge-workspace" / "models" / "qwen3-1.7b-q4_k_m.gguf"
dst.parent.mkdir(parents=True, exist_ok=True)
tmp = dst.with_suffix(".part")
if dst.exists() and dst.stat().st_size == SIZE:
    h = hashlib.file_digest(dst.open("rb"), "sha256").hexdigest()
    if h == SHA256:
        print(json.dumps({"verified": True, "bytes": SIZE, "sha256": h, "path": str(dst)}))
        raise SystemExit(0)
if tmp.exists() and tmp.stat().st_size > SIZE:
    tmp.unlink()
offset = tmp.stat().st_size if tmp.exists() else 0
headers = {"User-Agent": "OutcomeGate/1.0"}
if offset:
    headers["Range"] = f"bytes={offset}-"
with urlopen(Request(URL, headers=headers), timeout=120) as response:
    if offset and response.status != 206:
        offset = 0
    with tmp.open("ab" if offset else "wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)
if tmp.stat().st_size != SIZE:
    raise RuntimeError(f"incomplete model: {tmp.stat().st_size} of {SIZE} bytes")
with tmp.open("rb") as file:
    h = hashlib.file_digest(file, "sha256").hexdigest()
if h != SHA256:
    raise RuntimeError("model SHA-256 mismatch")
os.replace(tmp, dst)
print(json.dumps({"verified": True, "bytes": SIZE, "sha256": h, "path": str(dst)}))
