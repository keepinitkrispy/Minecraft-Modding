# SolBridge v0.1

SolBridge turns an Android/Termux device into a controlled execution endpoint using a GitHub repository's Issues API as the command/result bus.

## Why this transport

The current ChatGPT environment can already create/read GitHub issues. The phone can already call GitHub's HTTPS API. That gives both sides a shared, authenticated transport without requiring inbound ports, a public phone IP, or a custom ChatGPT connector.

## Command protocol

Create an issue with label `solbridge-command` and a JSON body:

```json
{
  "id": "example-001",
  "device_id": "ryan-pixel",
  "tool": "health",
  "args": {}
}
```

The phone claims it, executes the named tool, posts a JSON result comment, labels it done/error, and closes it.

## Built-in tools

- `health`
- `device_snapshot`
- `list_files`
- `read_text`
- `write_text`
- `git` (`status`, `diff`, `log`, `pull`)
- `termux_api` (`battery`, `wifi`, `location`, `clipboard_get`, `volume`)
- `shell` (disabled by default; prefix allowlist when enabled)

All file access is jailed to the configured workspace. The general shell is opt-in.

## Android side

Install Termux and Termux:API from the same signing source. The upstream Termux project notes that the API app must share the main Termux app's signing key. Then run `install-termux.sh` from this branch. The installer adds Python, git, the Termux API package, and termux-services; upstream termux-services uses runit and supports `sv-enable` for autostart.

## Required private bus repository

Use a **private** GitHub repository for actual commands/results. Do not use the public Minecraft repository as the live bus for personal data. The current ChatGPT GitHub connector can write into repositories it has access to, but it does not expose repository creation, so creating the private repo is the one account-level action that must be done outside the bridge.

Create a fine-grained GitHub token scoped only to that bus repo with Issues read/write. Put the token in the phone's environment (`SOLBRIDGE_GITHUB_TOKEN`) or config. Prefer environment storage over committing it anywhere.

## Config

`~/.config/solbridge/config.json`

```json
{
  "repo": "OWNER/PRIVATE_BUS_REPO",
  "token": "",
  "device_id": "ryan-pixel",
  "poll_seconds": 15,
  "workspace": "~/solbridge-workspace",
  "allow_shell": false,
  "shell_timeout": 120
}
```

## Next layers

1. First successful `health` round trip.
2. Add a persistent state database and event journal.
3. Add Android notification ingestion.
4. Add Shizuku/rish adapter for approved higher-privilege operations.
5. Add Minecraft-specific validators/builders as first self-added tools.
6. Move from GitHub polling to a purpose-built relay/MCP endpoint if/when the ChatGPT environment can call it directly.
