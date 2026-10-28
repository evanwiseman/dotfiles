import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

WT = Path(__file__).resolve().parent.parent / "bin" / "wt"

HERDR_STUB = """#!/bin/sh
printf '%s\\n' "$*" >>"$HERDR_LOG"
"""

# Records the candidates it was given, then prints $FZF_OUTPUT and exits $FZF_RC,
# mimicking `fzf --print-query` (query line, then the selected line).
FZF_STUB = """#!/bin/sh
cat >"$FZF_INPUT"
printf '%s' "$FZF_OUTPUT"
exit "${FZF_RC:-0}"
"""


@dataclass
class Sandbox:
    """A throwaway origin plus stubbed herdr and fzf, isolated from the user's git config."""

    root: Path
    env: dict[str, str]
    origin: Path

    def git(self, *args: str, cwd: Path) -> str:
        result = subprocess.run(
            ["git", *args], cwd=cwd, env=self.env, check=True, capture_output=True, text=True
        )
        return result.stdout.strip()

    def wt(
        self, cwd: Path, *args: str, fzf_output: str = "", fzf_rc: int = 0
    ) -> subprocess.CompletedProcess[str]:
        """Run wt with arguments (e.g. a branch), or through the (stubbed) fzf picker if none."""
        env = {**self.env, "FZF_OUTPUT": fzf_output, "FZF_RC": str(fzf_rc)}
        # stdin is closed so fail()'s "press enter" prompt returns immediately
        return subprocess.run(
            [str(WT), *args],
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
        )

    def herdr_calls(self) -> list[list[str]]:
        log = Path(self.env["HERDR_LOG"])
        if not log.exists():
            return []
        return [shlex.split(line) for line in log.read_text().splitlines()]

    def fzf_candidates(self) -> list[str]:
        return Path(self.env["FZF_INPUT"]).read_text().splitlines()

    def clone_normal(self, name: str = "normal") -> Path:
        repo = self.root / name
        self.git("clone", "-q", str(self.origin), str(repo), cwd=self.root)
        return repo

    def clone_bare(self, name: str = "bare") -> Path:
        repo = self.root / name
        repo.mkdir()
        self.git("clone", "-q", "--bare", str(self.origin), ".bare", cwd=repo)
        (repo / ".git").write_text("gitdir: ./.bare\n")
        self.git("config", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*", cwd=repo)
        self.git("fetch", "-q", "origin", cwd=repo)
        self.git("worktree", "add", "-q", "main", "main", cwd=repo)
        return repo


@pytest.fixture
def sandbox(tmp_path: Path) -> Sandbox:
    stub = tmp_path / "stub"
    stub.mkdir()
    for name, script in [("herdr", HERDR_STUB), ("fzf", FZF_STUB)]:
        path = stub / name
        path.write_text(script)
        path.chmod(0o755)

    env = {
        "PATH": f"{stub}{os.pathsep}{os.environ['PATH']}",
        "HOME": str(tmp_path),
        "HERDR_LOG": str(tmp_path / "herdr.log"),
        "FZF_INPUT": str(tmp_path / "fzf.in"),
        "GIT_CEILING_DIRECTORIES": str(tmp_path.parent),
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }

    src = tmp_path / "src"
    origin = tmp_path / "origin.git"
    box = Sandbox(root=tmp_path, env=env, origin=origin)
    box.git("init", "-q", "-b", "main", str(src), cwd=tmp_path)
    box.git("commit", "-q", "--allow-empty", "-m", "init", cwd=src)
    box.git("switch", "-q", "-c", "remote-only", cwd=src)
    box.git("commit", "-q", "--allow-empty", "-m", "remote work", cwd=src)
    box.git("switch", "-q", "main", cwd=src)
    box.git("clone", "-q", "--bare", str(src), str(origin), cwd=tmp_path)
    return box
