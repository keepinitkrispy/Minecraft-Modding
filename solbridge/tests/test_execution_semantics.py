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
