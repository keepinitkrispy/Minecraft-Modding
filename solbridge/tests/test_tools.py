from pathlib import Path
from solbridge.config import Config
from solbridge.tools import execute, ToolError


def cfg(tmp_path):
    return Config(repo="x/y", token="t", workspace=tmp_path)


def test_write_read(tmp_path):
    c = cfg(tmp_path)
    execute(c, "write_text", {"path": "a/b.txt", "text": "hello"})
    out = execute(c, "read_text", {"path": "a/b.txt"})
    assert out["text"] == "hello"


def test_path_jail(tmp_path):
    c = cfg(tmp_path)
    try:
        execute(c, "read_text", {"path": "../escape"})
        assert False
    except ToolError:
        pass


def test_shell_disabled(tmp_path):
    c = cfg(tmp_path)
    try:
        execute(c, "shell", {"command": "ls"})
        assert False
    except ToolError:
        pass
