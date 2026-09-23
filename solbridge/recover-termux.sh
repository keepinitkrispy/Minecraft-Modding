#!/data/data/com.termux/files/usr/bin/bash
# Restore the SolBridge agent on the already-paired Pixel without asking for a PAT.
set -euo pipefail

BUS_REPO="keepinitkrispy/solbridge-bus"
SOURCE_REPO="https://github.com/keepinitkrispy/Minecraft-Modding.git"
BRANCH="solbridge-v1"
DEST="$HOME/.local/share/solbridge-src"
CFG="$HOME/.config/solbridge/config.json"
SERVICE="$PREFIX/var/service/solbridge"

pkg install -y python git gh termux-api termux-services

if ! gh auth status --hostname github.com >/dev/null 2>&1; then
  echo "Opening GitHub's existing-account authorization (no PAT is requested)."
  export BROWSER=termux-open-url
  gh auth login --hostname github.com --git-protocol https --web
fi
LOGIN="$(gh api user --jq .login)"
if [ "$LOGIN" != "keepinitkrispy" ]; then
  echo "Stopped: Termux is signed in as '$LOGIN', not the account that owns $BUS_REPO."
  exit 1
fi
gh repo view "$BUS_REPO" >/dev/null

mkdir -p "$(dirname "$DEST")" "$(dirname "$CFG")" "$HOME/solbridge-workspace"
if [ -d "$DEST/.git" ]; then
  ORIGIN="$(git -C "$DEST" remote get-url origin)"
  if [ "$ORIGIN" != "$SOURCE_REPO" ]; then
    echo "Stopped: the existing checkout has a different origin; left it untouched."
    exit 1
  fi
  if [ -n "$(git -C "$DEST" status --porcelain)" ]; then
    echo "Stopped: the existing checkout has local changes; left it untouched."
    exit 1
  fi
  git -C "$DEST" fetch --depth 1 origin "$BRANCH"
  git -C "$DEST" checkout -B "$BRANCH" FETCH_HEAD
else
  if [ -e "$DEST" ]; then
    mv "$DEST" "$DEST.recovery-backup.$(date +%Y%m%d%H%M%S)"
  fi
  git clone --depth 1 --branch "$BRANCH" "$SOURCE_REPO" "$DEST"
fi
test -f "$DEST/solbridge/solbridge/agent.py"
PYTHONPATH="$DEST/solbridge" python -c 'import solbridge.agent'

python - "$CFG" "$BUS_REPO" <<'PY'
import json, pathlib, sys
p = pathlib.Path(sys.argv[1])
repo = sys.argv[2]
if p.exists():
    data = json.loads(p.read_text())
    if data.get("repo") != repo or data.get("device_id") not in (None, "ryan-pixel"):
        raise SystemExit("Stopped: saved SolBridge config points to a different bus or device; left it untouched.")
else:
    data = {
        "repo": repo, "device_id": "ryan-pixel", "poll_seconds": 15,
        "workspace": "~/solbridge-workspace", "source_dir": "~/.local/share/solbridge-src",
        "allow_shell": False, "shell_timeout": 120
    }
# Keep auth in the existing GitHub CLI login; do not store or print a token in config.
data["token"] = ""
data["device_id"] = "ryan-pixel"
data.setdefault("workspace", "~/solbridge-workspace")
data["source_dir"] = "~/.local/share/solbridge-src"
p.write_text(json.dumps(data, indent=2) + "\n")
p.chmod(0o600)
PY

cat > "$PREFIX/bin/solbridge" <<'RUN'
#!/data/data/com.termux/files/usr/bin/sh
export PYTHONPATH="$HOME/.local/share/solbridge-src/solbridge${PYTHONPATH:+:$PYTHONPATH}"
exec python -m solbridge.agent
RUN
chmod 700 "$PREFIX/bin/solbridge"

mkdir -p "$HOME/.local/bin" "$HOME/.termux"
cat > "$HOME/.local/bin/solbridge-ensure" <<'RUN'
#!/data/data/com.termux/files/usr/bin/sh
set -u
export SVDIR="$PREFIX/var/service" LOGDIR="$PREFIX/var/log"
service-daemon start >/dev/null 2>&1 || true
for _ in $(seq 1 20); do
  [ -e "$PREFIX/var/service/solbridge/supervise/ok" ] && break
  sleep 0.25
done
rm -f "$PREFIX/var/service/solbridge/down"
sv up solbridge >/dev/null 2>&1 || exit 1
sv status solbridge
RUN
chmod 700 "$HOME/.local/bin/solbridge-ensure"

PROPS="$HOME/.termux/termux.properties"
touch "$PROPS"
if grep -qE '^[[:space:]]*allow-external-apps[[:space:]]*=' "$PROPS"; then
  sed -i -E 's/^[[:space:]]*allow-external-apps[[:space:]]*=.*/allow-external-apps=true/' "$PROPS"
else
  printf '\nallow-external-apps=true\n' >> "$PROPS"
fi
termux-reload-settings >/dev/null 2>&1 || true

mkdir -p "$SERVICE/log"
cat > "$SERVICE/run" <<'RUN'
#!/data/data/com.termux/files/usr/bin/sh
exec 2>&1
exec solbridge
RUN
cat > "$SERVICE/log/run" <<'RUN'
#!/data/data/com.termux/files/usr/bin/sh
exec svlogger "$PREFIX/var/log/sv/solbridge"
RUN
chmod 700 "$SERVICE/run" "$SERVICE/log/run"

export SVDIR="$PREFIX/var/service" LOGDIR="$PREFIX/var/log"
service-daemon start >/dev/null 2>&1 || true
for _ in $(seq 1 30); do
  [ -e "$SERVICE/supervise/ok" ] && break
  sleep 0.5
done
if [ ! -e "$SERVICE/supervise/ok" ]; then
  echo "ERROR: runit did not supervise SolBridge."
  exit 1
fi
rm -f "$SERVICE/down"
sv up solbridge
mkdir -p "$HOME/.termux/boot"
cat > "$HOME/.termux/boot/solbridge-start.sh" <<'RUN'
#!/data/data/com.termux/files/usr/bin/sh
exec "$HOME/.local/bin/solbridge-ensure" >/dev/null 2>&1
RUN
chmod 700 "$HOME/.termux/boot/solbridge-start.sh"

echo "SOLBRIDGE_RESTORED=1"
echo "BUS=$BUS_REPO"
sv status solbridge
