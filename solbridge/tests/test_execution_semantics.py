from types import SimpleNamespace

from solbridge import agent


def test_top_level_nonzero_is_failure():
    assert agent._execution_failure("python_job", {"returncode": 3}) == "python_job returned nonzero exit status 3"


def test_top_level_zero_is_success():
    assert agent._execution_failure("python_job", {"returncode": 0}) is None


def test_workflow_explicit_error_is_failure():
    output = {
        "steps": [
            {"index": 0, "tool": "http_download", "status": "ok", "result": {"bytes": 10}},
            {"index": 1, "tool": "python_job", "status": "error", "error": "boom"},
        ]
    }
    failure = agent._execution_failure("workflow", output)
    assert failure is not None
    assert "workflow step 1" in failure
    assert "boom" in failure


def test_workflow_nested_nonzero_is_failure():
    output = {
        "steps": [
            {"index": 0, "tool": "http_download", "status": "ok", "result": {"bytes": 10}},
            {"index": 1, "tool": "python_job", "status": "ok", "result": {"returncode": 2, "stdout": "", "stderr": "failed"}},
        ]
    }
    failure = agent._execution_failure("workflow", output)
    assert failure == "workflow step 1 (python_job) returned nonzero exit status 2"


def test_workflow_success_is_success():
    output = {
        "steps": [
            {"index": 0, "tool": "http_download", "status": "ok", "result": {"bytes": 10}},
            {"index": 1, "tool": "python_job", "status": "ok", "result": {"returncode": 0}},
        ]
    }
    assert agent._execution_failure("workflow", output) is None


def test_companion_direct_ok_false_is_failure():
    failure = agent._execution_failure("companion", {"ok": False, "error": "target not found"})
    assert failure == "companion action failed: target not found"


def test_companion_nested_ok_false_is_failure():
    failure = agent._execution_failure("companion", {"launch": {"ok": False, "error": "no launcher"}})
    assert failure == "companion launch failed: no launcher"


def test_companion_verified_false_is_failure():
    failure = agent._execution_failure("companion", {"verified": False, "failure": "accessibility disconnected"})
    assert failure == "companion verification failed: accessibility disconnected"


def test_companion_success_is_success():
    assert agent._execution_failure("companion", {"health": {"ok": True}}) is None


def test_processed_issue_is_not_rewritten_done(monkeypatch, tmp_path):
    calls = []

    class Bus:
        def labels(self, number, labels):
            calls.append(("labels", number, labels))

        def close(self, number):
            calls.append(("close", number))

    cfg = SimpleNamespace(workspace=tmp_path)
    monkeypatch.setattr(agent, "_processed", lambda _cfg: {42})

    restarted = agent.process(Bus(), cfg, {"number": 42})

    assert restarted is False
    assert calls == [("close", 42)]



def _valid_gate_state():
    return {
        "schemaVersion": 1,
        "runtime": {"name": "shadow", "version": "4.2"},
        "objectives": [{"id": "goal-1"}],
        "activeId": "goal-1",
    }


def _write_command(state_text):
    return {"tool": "write_text", "args": {"path": "objectives/active.json", "text": state_text}}


def test_active_objective_write_requires_exact_valid_phone_readback(monkeypatch):
    import json

    text = json.dumps(_valid_gate_state()) + "\n"
    output = {"path": "objectives/active.json", "bytes": len(text.encode())}
    monkeypatch.setattr(agent, "execute", lambda cfg, tool, args: {"path": args["path"], "text": text, "truncated": False})

    state = agent._verify_active_objective_write(SimpleNamespace(), _write_command(text), output)

    assert state["activeId"] == "goal-1"
    assert output["readback_verified"] is True


def test_active_objective_write_rejects_mismatch_or_truncated_readback(monkeypatch):
    import pytest

    command = _write_command('{"schemaVersion":1}')

    monkeypatch.setattr(agent, "execute", lambda cfg, tool, args: {"text": "different", "truncated": False})
    with pytest.raises(RuntimeError, match="did not match"):
        agent._verify_active_objective_write(SimpleNamespace(), command, {})

    monkeypatch.setattr(agent, "execute", lambda cfg, tool, args: {"text": command["args"]["text"], "truncated": True})
    with pytest.raises(RuntimeError, match="did not match"):
        agent._verify_active_objective_write(SimpleNamespace(), command, {})


def test_return_link_contains_decodable_verified_receipt():
    import base64
    import json

    state = _valid_gate_state()
    command = _write_command(json.dumps(state))
    result = {
        "status": "ok",
        "command_id": "sync-7",
        "result": {"readback_verified": True, "bytes": 91},
    }

    link = agent._outcome_gate_return_link(77, command, "ryan-pixel", state, result)

    assert link.startswith(agent.OUTCOME_GATE_URL + "#bridge-state=")
    encoded = link.split("#bridge-state=", 1)[1]
    receipt = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
    assert receipt["schema"] == "outcome-gate-phone-receipt/v1"
    assert receipt["state"] == state
    assert receipt["issue_number"] == 77
    assert receipt["readback_verified"] is True


def test_return_link_is_not_created_without_phone_readback():
    import json

    state = _valid_gate_state()
    command = _write_command(json.dumps(state))
    result = {"status": "ok", "result": {"bytes": 10}}

    assert agent._outcome_gate_return_link(77, command, "ryan-pixel", state, result) is None
    other = {"tool": "read_text", "args": {"path": "objectives/active.json"}}
    assert agent._outcome_gate_return_link(77, other, "ryan-pixel", state, result) is None
