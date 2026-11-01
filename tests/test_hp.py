import json
import os
import shlex
import socket
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path

import pytest

HP = Path(__file__).resolve().parent.parent / "bin" / "hp"

# Logs every call, and answers the list/get queries hp makes from canned JSON.
HERDR_STUB = """#!/bin/sh
printf '%s\\n' "$*" >>"$HERDR_LOG"
case "$1 $2" in
  "workspace list") cat "$STATE/workspaces.json" ;;
  "tab list") cat "$STATE/tabs.json" ;;
  "pane list") cat "$STATE/panes.json" ;;
  "pane get") jq --arg id "$3" '{result: {pane: (.result.panes[] | select(.pane_id == $id))}}' "$STATE/panes.json" ;;
  "pane read") echo "output of $3" ;;
esac
"""

FZF_STUB = """#!/bin/sh
cat >"$FZF_INPUT"
printf '%s\\n' "$@" >"$FZF_ARGS"
"""

WORKSPACES = [{"workspace_id": "w1", "label": "pr3"}, {"workspace_id": "w2", "label": "dots"}]
TABS = [
    {"tab_id": "w1:t1", "label": "claude", "workspace_id": "w1"},
    {"tab_id": "w1:t2", "label": "nvim", "workspace_id": "w1"},
    {"tab_id": "w2:t3", "label": "shell", "workspace_id": "w2"},
]
PANES = [
    {"pane_id": "w1:p1", "tab_id": "w1:t1", "workspace_id": "w1", "terminal_title_stripped": "claude chat"},
    {"pane_id": "w1:p2", "tab_id": "w1:t2", "workspace_id": "w1", "terminal_title_stripped": "nvim ."},
    {"pane_id": "w2:p3", "tab_id": "w2:t3", "workspace_id": "w2", "terminal_title_stripped": "zsh"},
]


@dataclass
class Herdr:
    root: Path
    env: dict[str, str]

    def hp(self, *args: str, anchor: str | None = "w1:p2") -> subprocess.CompletedProcess[str]:
        env = dict(self.env)
        if anchor is not None:
            env["HERDR_ACTIVE_PANE_ID"] = anchor
        # stdin is closed so fail()'s "press enter" prompt returns immediately
        return subprocess.run(
            [str(HP), *args], env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True
        )

    def calls(self, *prefix: str) -> list[list[str]]:
        """herdr calls that change state (queries are left out), filtered by a prefix."""
        log = Path(self.env["HERDR_LOG"])
        lines = [shlex.split(line) for line in log.read_text().splitlines()] if log.exists() else []
        queries = (["workspace", "list"], ["tab", "list"], ["pane", "list"], ["pane", "get"], ["pane", "read"])
        lines = [c for c in lines if not any(c[: len(q)] == list(q) for q in queries)]
        return [c for c in lines if c[: len(prefix)] == list(prefix)]


@pytest.fixture
def herdr(tmp_path: Path) -> Herdr:
    stub = tmp_path / "stub"
    stub.mkdir()
    for name, script in [("herdr", HERDR_STUB), ("fzf", FZF_STUB)]:
        (stub / name).write_text(script)
        (stub / name).chmod(0o755)
    state = tmp_path / "state"
    state.mkdir()
    (state / "workspaces.json").write_text(json.dumps({"result": {"workspaces": WORKSPACES}}))
    (state / "tabs.json").write_text(json.dumps({"result": {"tabs": TABS}}))
    (state / "panes.json").write_text(json.dumps({"result": {"panes": PANES}}))
    env = {
        "PATH": f"{stub}{os.pathsep}{os.environ['PATH']}",
        "HOME": str(tmp_path),
        "STATE": str(state),
        "HERDR_LOG": str(tmp_path / "herdr.log"),
        "FZF_INPUT": str(tmp_path / "fzf.in"),
        "FZF_ARGS": str(tmp_path / "fzf.args"),
    }
    return Herdr(root=tmp_path, env=env)


def test_list_shows_every_pane_and_marks_the_anchor(herdr: Herdr) -> None:
    result = herdr.hp("--list", "w1:p2")

    assert result.returncode == 0, result.stdout
    rows = [line.split("\t") for line in result.stdout.splitlines()]
    assert rows == [
        ["w1:p1", " ", "pr3", "claude", "claude chat"],
        ["w1:p2", "*", "pr3", "nvim", "nvim ."],
        ["w2:p3", " ", "dots", "shell", "zsh"],
    ]


def test_preview_reads_the_pane(herdr: Herdr) -> None:
    result = herdr.hp("--preview", "w1:p1")

    assert result.stdout.strip() == "output of w1:p1"


@pytest.mark.parametrize("direction, split", [("right", "right"), ("down", "down")])
def test_move_right_or_down_splits_the_anchor(herdr: Herdr, direction: str, split: str) -> None:
    assert herdr.hp("--move", direction, "w1:p2", "w2:p3").returncode == 0

    assert herdr.calls("pane") == [
        ["pane", "move", "w2:p3", "--tab", "w1:t2", "--target-pane", "w1:p2", "--split", split, "--no-focus"],
    ]


@pytest.mark.parametrize("direction, split", [("left", "right"), ("up", "down")])
def test_move_left_or_up_splits_then_swaps(herdr: Herdr, direction: str, split: str) -> None:
    assert herdr.hp("--move", direction, "w1:p2", "w2:p3").returncode == 0

    assert herdr.calls("pane") == [
        ["pane", "move", "w2:p3", "--tab", "w1:t2", "--target-pane", "w1:p2", "--split", split, "--no-focus"],
        ["pane", "swap", "--source-pane", "w2:p3", "--target-pane", "w1:p2"],
    ]


def test_move_several_skips_the_anchor(herdr: Herdr) -> None:
    assert herdr.hp("--move", "right", "w1:p2", "w1:p1", "w1:p2", "w2:p3").returncode == 0

    moved = [c[2] for c in herdr.calls("pane", "move")]
    assert moved == ["w1:p1", "w2:p3"]


def test_move_rejects_unknown_direction(herdr: Herdr) -> None:
    result = herdr.hp("--move", "sideways", "w1:p2", "w2:p3")

    assert result.returncode != 0
    assert herdr.calls("pane") == []


def test_close_closes_each_but_not_the_anchor(herdr: Herdr) -> None:
    assert herdr.hp("--close", "w1:p2", "w1:p1", "w1:p2", "w2:p3").returncode == 0

    assert herdr.calls("pane") == [["pane", "close", "w1:p1"], ["pane", "close", "w2:p3"]]


def test_swap_with_the_anchor(herdr: Herdr) -> None:
    assert herdr.hp("--swap", "w1:p2", "w2:p3").returncode == 0

    assert herdr.calls("pane") == [["pane", "swap", "--source-pane", "w2:p3", "--target-pane", "w1:p2"]]


def test_jump_focuses_the_pane_through_the_socket(herdr: Herdr) -> None:
    path = herdr.root / "herdr.sock"
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(path))
    server.listen(1)
    received: list[dict] = []

    def serve() -> None:
        conn, _ = server.accept()
        with conn:
            received.append(json.loads(conn.makefile().readline()))
            conn.sendall(b'{"id":"hp","result":{}}\n')

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    herdr.env["HERDR_SOCKET_PATH"] = str(path)

    result = herdr.hp("--jump", "w2:p3")

    thread.join(timeout=5)
    server.close()
    assert result.returncode == 0, result.stdout
    assert received == [{"id": "hp", "method": "pane.focus", "params": {"pane_id": "w2:p3"}}]


def test_picker_lists_panes_and_binds_hjkl(herdr: Herdr) -> None:
    result = herdr.hp()

    assert result.returncode == 0, result.stdout
    ids = [line.split("\t")[0] for line in Path(herdr.env["FZF_INPUT"]).read_text().splitlines()]
    assert ids == ["w1:p1", "w1:p2", "w2:p3"]
    args = Path(herdr.env["FZF_ARGS"]).read_text()
    for key in ["ctrl-h", "ctrl-j", "ctrl-k", "ctrl-l", "ctrl-s", "ctrl-x", "enter"]:
        assert f"{key}:" in args


def test_needs_an_anchor(herdr: Herdr) -> None:
    result = herdr.hp(anchor=None)

    assert result.returncode != 0
    assert "herdr key" in result.stdout
