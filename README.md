# Codex Auto Approve

A Codex plugin marketplace containing `codex-auto-approve`. The plugin handles `PermissionRequest` hooks with three policy levels: `codex` (return no decision), `retry_without_sandbox` (approve descriptions containing `沙盒` or `sandbox`), and `all` (approve every request). **The default is `all`.**

## Install from GitHub

After this repository layout is pushed to GitHub:

```bash
codex plugin marketplace add UFOdestiny/codex-approve
codex plugin add codex-auto-approve@codex-auto-approve-local
```

For a local checkout, replace the first command with `codex plugin marketplace add .` from the repository root.

Start a new Codex session and review and trust the plugin hook when prompted. `/hooks` should show one active `PermissionRequest` hook. Disabling `codex-auto-approve` in `/plugins` removes that hook from new sessions.

To change the approval policy, see the [plugin configuration guide](plugins/codex-auto-approve/README.md). You can start Codex with `CODEX_AUTO_APPROVE_LEVEL=codex codex` to leave every decision to Codex.

## Uninstall

```bash
codex plugin remove codex-auto-approve@codex-auto-approve-local
codex plugin marketplace remove codex-auto-approve-local
```

Start a new Codex session to apply the change.

## Test

```bash
python3 -m unittest discover -s tests -v
```

The marketplace catalog is at [`.agents/plugins/marketplace.json`](.agents/plugins/marketplace.json), and the plugin is at [`plugins/codex-auto-approve`](plugins/codex-auto-approve).
