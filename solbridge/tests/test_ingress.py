from types import SimpleNamespace

from solbridge.agent import _authorized_actor


class FakeBus:
    def __init__(self, verified=True):
        self.verified = verified
        self.calls = []

    def verify_owner_command_file(self, **kwargs):
        self.calls.append(kwargs)
        return self.verified


def cfg():
    return SimpleNamespace(repo="keepinitkrispy/solbridge-bus")


def test_owner_issue_is_authorized_without_fallback():
    bus = FakeBus(False)
    issue = {"user": {"login": "keepinitkrispy"}}
    assert _authorized_actor(issue, cfg(), bus, {"tool": "health"}) is True
    assert bus.calls == []


def test_actions_issue_requires_verified_owner_command_file():
    bus = FakeBus(True)
    issue = {"user": {"login": "github-actions[bot]"}}
    cmd = {
        "id": "proof",
        "tool": "health",
        "args": {},
        "_ingress": {
            "type": "owner-command-file",
            "path": "commands/proof.json",
            "commit": "a" * 40,
        },
    }
    assert _authorized_actor(issue, cfg(), bus, cmd) is True
    assert bus.calls == [{
        "path": "commands/proof.json",
        "commit_sha": "a" * 40,
        "expected": {"id": "proof", "tool": "health", "args": {}},
    }]


def test_actions_issue_rejected_when_provenance_fails():
    bus = FakeBus(False)
    issue = {"user": {"login": "github-actions[bot]"}}
    cmd = {
        "id": "proof",
        "tool": "health",
        "args": {},
        "_ingress": {
            "type": "owner-command-file",
            "path": "commands/proof.json",
            "commit": "b" * 40,
        },
    }
    assert _authorized_actor(issue, cfg(), bus, cmd) is False


def test_other_actor_is_rejected():
    bus = FakeBus(True)
    issue = {"user": {"login": "someone-else"}}
    assert _authorized_actor(issue, cfg(), bus, {"tool": "health"}) is False
