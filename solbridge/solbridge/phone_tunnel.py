"""Keep the free HTTPS tunnel alive and put the private entry link in GitHub."""
import os
import re
import subprocess
import threading
from pathlib import Path

ROOT = Path.home() / "solbridge-workspace"
URL_PATH = ROOT / "agent" / "tunnel_url"
SECRET = ROOT / "agent" / "session_secret"
ISSUE = "370"
REPO = "keepinitkrispy/solbridge-bus"
TUNNEL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def notify(url: str):
    if not SECRET.exists():
        raise RuntimeError("Pixel app has not generated the private pairing link yet")
    link = url + "/invite/" + SECRET.read_text().strip()
    URL_PATH.parent.mkdir(parents=True, exist_ok=True)
    old = URL_PATH.read_text().strip() if URL_PATH.exists() else ""
    URL_PATH.write_text(url + "\n")
    if old != url:
        result = subprocess.run(
            ["gh", "issue", "comment", ISSUE, "-R", REPO, "--body",
             f"Pixel app is online: {link}\n\nOpen this private link on your phone or Mac. The Pixel keeps working while browsers are closed."],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode:
            raise RuntimeError("Could not post private tunnel link: " + result.stderr[-300:])
    print("Tunnel is live: " + url, flush=True)


def main():
    cloudflared = "/data/data/com.termux/files/usr/bin/cloudflared"
    command = [cloudflared, "tunnel", "--no-autoupdate", "--url", "http://127.0.0.1:8765"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    lines = []

    def read_stream(stream):
        for line in stream:
            lines.append(line[-500:])
            found = TUNNEL.search(line)
            if found and not getattr(read_stream, "published", False):
                read_stream.published = True
                try:
                    notify(found.group(0))
                except Exception as exc:
                    print("Tunnel publish failed: " + str(exc), flush=True)

    threads = [threading.Thread(target=read_stream, args=(stream,), daemon=True)
               for stream in (process.stdout, process.stderr)]
    for thread in threads:
        thread.start()
    code = process.wait()
    for thread in threads:
        thread.join(timeout=2)
    URL_PATH.unlink(missing_ok=True)
    raise RuntimeError(f"cloudflared exited {code}: {''.join(lines[-4:])[-800:]}")


if __name__ == "__main__":
    main()
