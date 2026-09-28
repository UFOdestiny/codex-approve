# Codex Auto Approve

This plugin handles Codex `PermissionRequest` events using a JSON policy. It has three ordered levels:

| Level | Hook behavior |
| --- | --- |
| `codex` | Return no decision; Codex handles the request normally. |
| `retry_without_sandbox` | Approve when `tool_input.description` contains `沙盒` or `sandbox` (case insensitive for English). |
| `all` | Approve every `PermissionRequest`, including requests with no description. |

The default level is `all`. The `retry_without_sandbox` keyword rule also approves descriptions that mention a sandbox without saying “retry”; the level name is retained for existing configurations. The bundled read-only default is [`config.json`](config.json). To customize it, create `PLUGIN_DATA/config.json` in the writable data directory Codex provides to this plugin. You can also point `CODEX_AUTO_APPROVE_CONFIG` at an explicit JSON file.

```json
{
  "default_level": "codex",
  "projects": {
    "/absolute/path/to/project": "retry_without_sandbox",
    "/absolute/path/to/project/trusted-subproject": "all"
  }
}
```

Project rules cover the listed directory and its descendants. The most specific matching path wins. Paths must be absolute; other projects use `default_level`. Use a trusted `PLUGIN_DATA` directory for this file, since a project checkout does not supply its own policy.

Configuration order is:

1. `CODEX_AUTO_APPROVE_LEVEL` overrides the selected level for every project.
2. `CODEX_AUTO_APPROVE_CONFIG` selects a JSON config file explicitly.
3. `PLUGIN_DATA/config.json` is used when present.
4. `PLUGIN_ROOT/config.json` supplies the bundled default.

The environment level accepts `codex`, `retry_without_sandbox`, or `all`. For example, start Codex with `CODEX_AUTO_APPROVE_LEVEL=codex codex` to leave all requests to Codex. An invalid or unreadable config, an invalid level, or malformed hook input causes the hook to return no decision. The hook writes each automatic approval to `PLUGIN_DATA/approvals.jsonl` when that directory is available.

For a config file outside the plugin data directory, start Codex with `CODEX_AUTO_APPROVE_CONFIG=/absolute/path/to/config.json codex`. This is also a convenient way to select a policy before the first hook run.

`all` removes the manual approval step for every request that reaches this hook. Choose it only where that behavior is intended. Organization-managed Codex policy may still disable or ignore plugin hooks.

The hook is bundled with the plugin. In a new Codex session, review and trust it, then use `/hooks` to verify it is active. Disabling `codex-auto-approve` in `/plugins` disables its hook in new sessions.
