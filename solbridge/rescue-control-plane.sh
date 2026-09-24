#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
HOME="${HOME:-/data/data/com.termux/files/home}"
SRC="$HOME/.local/share/solbridge-src"
SERVICE="$PREFIX/var/service/solbridge"
ENSURE="$HOME/.local/bin/solbridge-ensure"
PROPS="$HOME/.termux/termux.properties"
BOOT="$HOME/.termux/boot/solbridge-start.sh"
CFG="$HOME/.config/solbridge/config.json"

mkdir -p "$HOME/.termux" "$HOME/.local/bin" "$HOME/.config/solbridge" "$HOME/.termux/boot"
touch "$PROPS"

if grep -qE '^[[:space:]]*allow-external-apps[[:space:]]*=' "$PROPS"; then
  sed -i -E 's/^[[:space:]]*allow-external-apps[[:space:]]*=.*/allow-external-apps=true/' "$PROPS"
else
  printf '\nallow-external-apps=true\n' >> "$PROPS"
fi
termux-reload-settings >/dev/null 2>&1 || true

if [ ! -f "$SRC/solbridge/solbridge/agent.py" ]; then
  if ! command -v git >/dev/null 2>&1; then
    pkg install -y git
  fi
  TMP="$HOME/.local/share/solbridge-src.rescue.$$"
  rm -rf "$TMP"
  git clone --depth 1 --branch solbridge-v1 https://github.com/keepinitkrispy/Minecraft-Modding.git "$TMP"
  rm -rf "$SRC"
  mv "$TMP" "$SRC"
fi

cat > "$PREFIX/bin/solbridge" <<'RUN'
#!/data/data/com.termux/files/usr/bin/sh
export PYTHONPATH="$HOME/.local/share/solbridge-src/solbridge${PYTHONPATH:+:$PYTHONPATH}"
exec python -m solbridge.agent
RUN
chmod 700 "$PREFIX/bin/solbridge"

if [ ! -f "$CFG" ]; then
  cat > "$CFG" <<'JSON'
{
  "repo": "keepinitkrispy/solbridge-bus",
  "token": "",
  "device_id": "ryan-pixel",
  "poll_seconds": 15,
  "workspace": "~/solbridge-workspace",
  "source_dir": "~/.local/share/solbridge-src",
  "allow_shell": false,
  "shell_timeout": 120
}
JSON
  chmod 600 "$CFG"
fi

mkdir -p "$SERVICE/log" "$PREFIX/var/log/sv/solbridge"
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

cat > "$ENSURE" <<'RUN'
#!/data/data/com.termux/files/usr/bin/sh
set -u
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export SVDIR="$PREFIX/var/service"
export LOGDIR="$PREFIX/var/log"
PROP="$HOME/.termux/termux.properties"
mkdir -p "$HOME/.termux"
touch "$PROP"
if grep -qE '^[[:space:]]*allow-external-apps[[:space:]]*=' "$PROP"; then
  sed -i -E 's/^[[:space:]]*allow-external-apps[[:space:]]*=.*/allow-external-apps=true/' "$PROP"
else
  printf '\nallow-external-apps=true\n' >> "$PROP"
fi
termux-reload-settings >/dev/null 2>&1 || true
PIDFILE="$PREFIX/var/run/service-daemon.pid"
if command -v service-daemon >/dev/null 2>&1; then
  service-daemon start >/dev/null 2>&1 || true
else
  mkdir -p "$PREFIX/var/log"
  runsvdir -P "$PREFIX/var/service" >>"$PREFIX/var/log/runsvdir.log" 2>&1 &
fi
for _ in $(seq 1 40); do
  [ -e "$PREFIX/var/service/solbridge/supervise/ok" ] && break
  sleep 0.25
done
rm -f "$PREFIX/var/service/solbridge/down"
sv up solbridge >/dev/null 2>&1 || exit 1
sv status solbridge
RUN
chmod 700 "$ENSURE"

cat > "$BOOT" <<'RUN'
#!/data/data/com.termux/files/usr/bin/sh
exec "$HOME/.local/bin/solbridge-ensure" >/dev/null 2>&1
RUN
chmod 700 "$BOOT"

rm -f "$SERVICE/down"
export SVDIR="$PREFIX/var/service"
export LOGDIR="$PREFIX/var/log"
if command -v service-daemon >/dev/null 2>&1; then
  service-daemon start >/dev/null 2>&1 || true
else
  runsvdir -P "$PREFIX/var/service" >>"$PREFIX/var/log/runsvdir.log" 2>&1 &
fi

for _ in $(seq 1 40); do
  [ -e "$SERVICE/supervise/ok" ] && break
  sleep 0.25
done

if [ ! -e "$SERVICE/supervise/ok" ]; then
  echo "RESCUE_FAILED=service-not-supervised"
  exit 21
fi

sv up solbridge >/dev/null 2>&1 || true
sleep 2

echo "ALLOW_EXTERNAL_APPS=$(grep -E '^[[:space:]]*allow-external-apps[[:space:]]*=' "$PROPS" | tail -1)"
echo "ENSURE=$ENSURE"
echo "SERVICE_DIR=$SERVICE"
sv status solbridge
echo "SOLBRIDGE_RESCUE_COMPLETE=1"
