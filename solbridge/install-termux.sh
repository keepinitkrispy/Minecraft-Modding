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
python -m pip install --upgrade pip

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
cd "$DEST/solbridge"
python -m pip install .
mkdir -p "$CFG_DIR" "$WORK"

cat > "$CFG_DIR/config.json" <<JSON
{
  "repo": "$BUS_REPO",
  "token": "",
  "device_id": "ryan-pixel",
  "poll_seconds": 15,
  "workspace": "~/solbridge-workspace",
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
sv-enable solbridge || true
sv up solbridge || true

echo
echo "SOLBRIDGE_INSTALLED=1"
echo "BUS_REPO=$BUS_REPO"
echo "CONFIG=$CFG_DIR/config.json"
echo "WORKSPACE=$WORK"
echo "Run: sv status solbridge"
