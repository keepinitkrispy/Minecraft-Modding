# SolBridge v0.1

SolBridge turns an Android/Termux device into a controlled execution endpoint using a private GitHub repository's Issues API as the command/result bus.

## What is already built

The current ChatGPT environment can create and read GitHub issues. The phone can call GitHub's HTTPS API. SolBridge joins those two existing capabilities so ChatGPT can issue a structured command, the Pixel executes it, and the result comes back through the same private repo.

No inbound phone port, public IP, custom ChatGPT connector, or manually maintained token is required.

## Install

Install **Termux** and **Termux:API** from the same signing source. Upstream Termux requires the API app and main app to share a signing key.

Then in Termux run:

```bash
pkg install -y curl && curl -fsSL https://raw.githubusercontent.com/keepinitkrispy/Minecraft-Modding/solbridge-v1/solbridge/install-termux.sh | bash
```

The installer:

1. installs Python, git, the official GitHub CLI (`gh`), Termux API helpers, and termux-services;
2. opens GitHub's browser/device authorization if the phone is not already logged in;
3. automatically creates `OWNER/solbridge-bus` as a **private** repository;
4. clones and installs SolBridge;
5. writes its config without copying the GitHub token into the config file (the agent asks `gh auth token` locally);
6. registers and starts SolBridge as a runit service.

That GitHub authorization is the only account-level approval the installer cannot perform on the user's behalf.

## Command protocol

A command is an issue labeled `solbridge-command` whose body is JSON:

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
- `self_update` — pulls this branch, reinstalls SolBridge, returns the result, then restarts the running agent into the new code
- `shell` — disabled by default; when enabled it is still restricted to configured command prefixes and the workspace

All ordinary file operations are jailed to `~/solbridge-workspace`.

## Why `self_update` matters

Once the first round trip works, new capabilities can be added to this branch, covered by CI, and then installed on the phone through a `self_update` command. That is the bootstrap for the larger capability-factory idea: add a tool once, then it becomes part of the device agent's permanent callable surface.

## Current config

`~/.config/solbridge/config.json`

```json
{
  "repo": "OWNER/solbridge-bus",
  "token": "",
  "device_id": "ryan-pixel",
  "poll_seconds": 15,
  "workspace": "~/solbridge-workspace",
  "allow_shell": false,
  "shell_timeout": 120
}
```

## Next capability layers

- persistent SQLite state/event journal
- Android notification ingestion
- Shizuku/rish adapter for approved higher-privilege operations
- Minecraft Bedrock validators/builders as the first specialized tool suite
- local document/media indexing
- purpose-built relay/MCP transport if the ChatGPT environment later supports calling it directly
