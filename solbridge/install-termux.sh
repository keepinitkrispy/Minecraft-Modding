#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO_URL="${SOLBRIDGE_SOURCE_REPO:-https://github.com/keepinitkrispy/Minecraft-Modding.git}"
BRANCH="${SOLBRIDGE_SOURCE_BRANCH:-solbridge-v1}"
DEST="$HOME/.local/share/solbridge-src"
CFG_DIR="$HOME/.config/solbridge"
WORK="$HOME/solbridge-workspace"

pkg update -y
pkg install -y python git termux-api termux-services
python -m pip install --upgrade pip

rm -rf "$DEST"
git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$DEST"
cd "$DEST/solbridge"
python -m pip install .
mkdir -p "$CFG_DIR" "$WORK"

if [ ! -f "$CFG_DIR/config.json" ]; then
  cat > "$CFG_DIR/config.json" <<'JSON'
{
  "repo": "REPLACE_WITH_PRIVATE_OWNER_REPO",
  "token": "",
  "device_id": "ryan-pixel",
  "poll_seconds": 15,
  "workspace": "~/solbridge-workspace",
  "allow_shell": false,
  "shell_timeout": 120
}
JSON
fi
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
sv-enable solbridge || true

echo
printf '%s\n' 'SOLBRIDGE_INSTALLED=1' "CONFIG=$CFG_DIR/config.json" "WORKSPACE=$WORK"
printf '%s\n' 'Next required values: private GitHub repo + fine-grained token with Issues read/write.'
