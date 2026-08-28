#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO_URL="${SOLBRIDGE_SOURCE_REPO:-https://github.com/keepinitkrispy/Minecraft-Modding.git}"
BRANCH="${SOLBRIDGE_SOURCE_BRANCH:-solbridge-v1}"
BUS_NAME="${SOLBRIDGE_BUS_NAME:-solbridge-bus}"
DEST="$HOME/.local/share/solbridge-src"
CFG_DIR="$HOME/.config/solbridge"
WORK="$HOME/solbridge-workspace"

pkg update -y
pkg install -y python git gh termux-api termux-services

if ! gh auth status --hostname github.com >/dev/null 2>&1; then
  echo
  echo "GitHub authorization is the one required account approval."
  export BROWSER=termux-open-url
  gh auth login --hostname github.com --git-protocol https --web
fi

OWNER="$(gh api user --jq .login)"
BUS_REPO="$OWNER/$BUS_NAME"
if ! gh repo view "$BUS_REPO" >/dev/null 2>&1; then
  gh repo create "$BUS_REPO" --private --description "Private SolBridge command/result bus"
fi

rm -rf "$DEST"
git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$DEST"
mkdir -p "$CFG_DIR" "$WORK"

cat > "$PREFIX/bin/solbridge" <<'RUN'
#!/data/data/com.termux/files/usr/bin/sh
export PYTHONPATH="$HOME/.local/share/solbridge-src/solbridge${PYTHONPATH:+:$PYTHONPATH}"
exec python -m solbridge.agent
RUN
chmod +x "$PREFIX/bin/solbridge"

cat > "$CFG_DIR/config.json" <<JSON
{
  "repo": "$BUS_REPO",
  "token": "",
  "device_id": "ryan-pixel",
  "poll_seconds": 15,
  "workspace": "~/solbridge-workspace",
  "source_dir": "~/.local/share/solbridge-src",
  "allow_shell": false,
  "shell_timeout": 120
}
JSON
chmod 600 "$CFG_DIR/config.json"

SERVICE="$PREFIX/var/service/solbridge"
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
chmod +x "$SERVICE/run" "$SERVICE/log/run"

export SVDIR="$PREFIX/var/service"
export LOGDIR="$PREFIX/var/log"
PIDFILE="$PREFIX/var/run/service-daemon.pid"
if [ ! -s "$PIDFILE" ] || ! kill -0 "$(cat "$PIDFILE" 2>/dev/null)" 2>/dev/null; then
  service-daemon start >/dev/null 2>&1 || true
fi

# runsvdir scans asynchronously. Wait until this service is actually supervised.
for _ in $(seq 1 20); do
  [ -e "$SERVICE/supervise/ok" ] && break
  sleep 0.5
done
if [ ! -e "$SERVICE/supervise/ok" ]; then
  echo "ERROR: runit did not begin supervising SolBridge" >&2
  exit 1
fi

rm -f "$SERVICE/down"
sv up solbridge
sv status solbridge

# Termux:Boot will run this after Android reboots, if the companion app is installed/opened once.
mkdir -p "$HOME/.termux/boot"
cat > "$HOME/.termux/boot/solbridge-start.sh" <<'RUN'
#!/data/data/com.termux/files/usr/bin/sh
export SVDIR="$PREFIX/var/service"
export LOGDIR="$PREFIX/var/log"
PIDFILE="$PREFIX/var/run/service-daemon.pid"
if [ ! -s "$PIDFILE" ] || ! kill -0 "$(cat "$PIDFILE" 2>/dev/null)" 2>/dev/null; then
  service-daemon start >/dev/null 2>&1 || true
fi
for _ in $(seq 1 20); do
  [ -e "$PREFIX/var/service/solbridge/supervise/ok" ] && break
  sleep 0.5
done
sv up solbridge >/dev/null 2>&1 || true
RUN
chmod +x "$HOME/.termux/boot/solbridge-start.sh"

echo
echo "SOLBRIDGE_INSTALLED=1"
echo "BUS_REPO=$BUS_REPO"
echo "CONFIG=$CFG_DIR/config.json"
echo "WORKSPACE=$WORK"
echo "SERVICE=running"
