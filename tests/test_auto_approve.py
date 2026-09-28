import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "plugins/codex-auto-approve/hooks/auto_approve.py"
PLUGIN = HOOK.parent.parent


def request(description="retry without sandbox", cwd="/tmp/project"):
    return {
        "hook_event_name": "PermissionRequest",
        "tool_name": "Bash",
        "cwd": cwd,
        "tool_input": {"description": description},
    }


class ApprovalPolicyTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name)
        self.env = os.environ.copy()
        self.env.pop("CODEX_AUTO_APPROVE_LEVEL", None)
        self.env.pop("CODEX_AUTO_APPROVE_CONFIG", None)
        self.env.update(PLUGIN_ROOT=str(PLUGIN), PLUGIN_DATA=str(self.data))

    def run_hook(self, payload):
        result = subprocess.run(
            ["python3", str(HOOK)],
            input=json.dumps(payload), text=True, capture_output=True, env=self.env, check=True,
        )
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout) if result.stdout else None

    def write_config(self, config):
        (self.data / "config.json").write_text(json.dumps(config), encoding="utf-8")

    def test_default_approves_every_permission_request(self):
        self.assertEqual(self.run_hook(request())["hookSpecificOutput"]["decision"]["behavior"], "allow")
        self.assertEqual(self.run_hook(request("run privileged command"))["hookSpecificOutput"]["decision"]["behavior"], "allow")

    def test_sandbox_keywords(self):
        self.env["CODEX_AUTO_APPROVE_LEVEL"] = "retry_without_sandbox"
        for description in ("请在沙盒外重试该命令", "沙盒执行失败", "Sandbox blocked the command"):
            with self.subTest(description=description):
                self.assertIsNotNone(self.run_hook(request(description)))
        for description in ("执行失败，请重试", "run privileged command"):
            with self.subTest(description=description):
                self.assertIsNone(self.run_hook(request(description)))

    def test_all_and_codex_levels(self):
        self.env["CODEX_AUTO_APPROVE_LEVEL"] = "all"
        payload = request("")
        payload.pop("tool_input")
        self.assertIsNotNone(self.run_hook(payload))
        self.env["CODEX_AUTO_APPROVE_LEVEL"] = "codex"
        self.assertIsNone(self.run_hook(request()))

    def test_project_rules_and_environment_override(self):
        self.write_config({
            "default_level": "codex",
            "projects": {
                "/tmp/project": "retry_without_sandbox",
                "/tmp/project/trusted": "all",
            },
        })
        self.assertIsNone(self.run_hook(request(cwd="/tmp/elsewhere")))
        self.assertIsNotNone(self.run_hook(request(cwd="/tmp/project/child")))
        self.assertIsNone(self.run_hook(request(cwd="/tmp/project-neighbor")))
        self.assertIsNotNone(self.run_hook(request("anything", "/tmp/project/trusted/child")))
        self.env["CODEX_AUTO_APPROVE_LEVEL"] = "codex"
        self.assertIsNone(self.run_hook(request("anything", "/tmp/project/trusted")))

    def test_invalid_config_returns_no_decision(self):
        self.write_config({"default_level": "all", "projects": {"relative/path": "all"}})
        self.assertIsNone(self.run_hook(request()))
        self.env["CODEX_AUTO_APPROVE_LEVEL"] = "all"
        self.assertIsNone(self.run_hook(request()))

    def test_explicit_config_path(self):
        config = self.data / "alternate.json"
        config.write_text('{"default_level":"all"}', encoding="utf-8")
        self.env["CODEX_AUTO_APPROVE_CONFIG"] = str(config)
        self.assertIsNotNone(self.run_hook(request("anything")))

    def test_non_permission_event(self):
        payload = request()
        payload["hook_event_name"] = "Other"
        self.env["CODEX_AUTO_APPROVE_LEVEL"] = "all"
        self.assertIsNone(self.run_hook(payload))

if __name__ == "__main__":
    unittest.main()
