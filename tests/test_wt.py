from pathlib import Path

import pytest

from conftest import Sandbox


def upstream(box: Sandbox, worktree: Path) -> str:
    ref = box.git("symbolic-ref", "HEAD", cwd=worktree)
    return box.git("for-each-ref", "--format=%(upstream:short)", ref, cwd=worktree)


def branch_of(box: Sandbox, worktree: Path) -> str:
    return box.git("branch", "--show-current", cwd=worktree)


class TestNormalRepo:
    def test_new_branch_goes_under_dot_worktrees(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_normal()

        result = sandbox.wt(repo, "feature")

        assert result.returncode == 0, result.stdout
        worktree = repo / ".worktrees" / "feature"
        assert branch_of(sandbox, worktree) == "feature"
        assert upstream(sandbox, worktree) == ""
        assert sandbox.git("rev-parse", "HEAD", cwd=worktree) == sandbox.git(
            "rev-parse", "origin/main", cwd=repo
        )

    def test_slashed_branch_nests(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_normal()

        assert sandbox.wt(repo, "feat/x").returncode == 0

        assert branch_of(sandbox, repo / ".worktrees" / "feat" / "x") == "feat/x"

    def test_remote_only_branch_tracks_origin(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_normal()

        assert sandbox.wt(repo, "remote-only").returncode == 0

        worktree = repo / ".worktrees" / "remote-only"
        assert upstream(sandbox, worktree) == "origin/remote-only"
        assert sandbox.git("log", "-1", "--format=%s", cwd=worktree) == "remote work"

    def test_existing_local_branch_is_checked_out(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_normal()
        sandbox.git("branch", "local", cwd=repo)

        assert sandbox.wt(repo, "local").returncode == 0

        assert branch_of(sandbox, repo / ".worktrees" / "local") == "local"

    def test_worktrees_are_excluded_once(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_normal()

        assert sandbox.wt(repo, "one").returncode == 0
        assert sandbox.wt(repo, "two").returncode == 0

        exclude = (repo / ".git" / "info" / "exclude").read_text().splitlines()
        assert exclude.count("/.worktrees/") == 1
        assert sandbox.git("status", "--porcelain", cwd=repo) == ""

    def test_nothing_excluded_when_cancelled(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_normal()

        assert sandbox.wt(repo, fzf_rc=130).returncode == 0

        assert "/.worktrees/" not in (repo / ".git" / "info" / "exclude").read_text()

    def test_run_from_inside_a_worktree_uses_repo_root(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_normal()
        assert sandbox.wt(repo, "first").returncode == 0

        assert sandbox.wt(repo / ".worktrees" / "first", "second").returncode == 0

        assert (repo / ".worktrees" / "second").is_dir()
        assert not (repo / ".worktrees" / "first" / ".worktrees").exists()

    def test_env_copied_from_main_checkout(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_normal()
        (repo / ".env").write_text("FROM=main\n")

        assert sandbox.wt(repo, "feature").returncode == 0

        assert (repo / ".worktrees" / "feature" / ".env").read_text() == "FROM=main\n"

    def test_env_falls_back_to_another_worktree(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_normal()
        assert sandbox.wt(repo, "first").returncode == 0
        (repo / ".worktrees" / "first" / ".env").write_text("FROM=first\n")

        assert sandbox.wt(repo, "second").returncode == 0

        assert (repo / ".worktrees" / "second" / ".env").read_text() == "FROM=first\n"

    def test_opens_worktree_in_herdr(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_normal()

        assert sandbox.wt(repo, "feature").returncode == 0

        assert sandbox.herdr_calls() == [
            [
                "worktree", "open",
                "--cwd", str(repo),
                "--path", str(repo / ".worktrees" / "feature"),
                "--label", "feature",
                "--focus",
            ]
        ]  # fmt: skip


class TestBareRepo:
    def test_new_branch_goes_next_to_main(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_bare()

        assert sandbox.wt(repo / "main", "feature").returncode == 0

        assert branch_of(sandbox, repo / "feature") == "feature"
        assert not (repo / ".worktrees").exists()

    def test_runs_from_repo_root(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_bare()

        assert sandbox.wt(repo, "feature").returncode == 0

        assert branch_of(sandbox, repo / "feature") == "feature"

    def test_nothing_excluded(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_bare()

        assert sandbox.wt(repo / "main", "feature").returncode == 0

        exclude = repo / ".bare" / "info" / "exclude"
        assert not exclude.exists() or "/.worktrees/" not in exclude.read_text()

    def test_env_copied_from_default_branch_worktree(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_bare()
        (repo / "main" / ".env").write_text("FROM=main\n")

        assert sandbox.wt(repo / "main", "feature").returncode == 0

        assert (repo / "feature" / ".env").read_text() == "FROM=main\n"

    def test_opens_worktree_in_herdr(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_bare()

        assert sandbox.wt(repo / "main", "feature").returncode == 0

        assert sandbox.herdr_calls() == [
            [
                "worktree", "open",
                "--cwd", str(repo),
                "--path", str(repo / "feature"),
                "--label", "feature",
                "--focus",
            ]
        ]  # fmt: skip


class TestPicker:
    def test_offers_local_and_remote_branches_once(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_normal()
        sandbox.git("branch", "local", cwd=repo)

        sandbox.wt(repo, fzf_rc=130)

        assert sandbox.fzf_candidates() == ["local", "main", "remote-only"]

    def test_picking_a_branch(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_normal()

        result = sandbox.wt(repo, fzf_output="rem\nremote-only\n")

        assert result.returncode == 0, result.stdout
        assert upstream(sandbox, repo / ".worktrees" / "remote-only") == "origin/remote-only"

    def test_typing_a_new_name(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_normal()

        # no match: fzf exits 1 and prints only the query
        result = sandbox.wt(repo, fzf_output="brand-new\n", fzf_rc=1)

        assert result.returncode == 0, result.stdout
        assert branch_of(sandbox, repo / ".worktrees" / "brand-new") == "brand-new"

    def test_cancel_does_nothing(self, sandbox: Sandbox) -> None:
        repo = sandbox.clone_normal()

        result = sandbox.wt(repo, fzf_output="typed\n", fzf_rc=130)

        assert result.returncode == 0
        assert not (repo / ".worktrees").exists()
        assert sandbox.herdr_calls() == []


@pytest.mark.parametrize("layout", ["normal", "bare"])
def test_existing_path_fails(sandbox: Sandbox, layout: str) -> None:
    repo = sandbox.clone_normal() if layout == "normal" else sandbox.clone_bare()
    assert sandbox.wt(repo, "feature").returncode == 0

    result = sandbox.wt(repo, "feature")

    assert result.returncode == 1
    assert "already exists" in result.stdout
    assert len(sandbox.herdr_calls()) == 1


def test_outside_a_repo_fails(sandbox: Sandbox, tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()

    result = sandbox.wt(empty, "feature")

    assert result.returncode == 1
    assert "not inside a git repo" in result.stdout
    assert sandbox.herdr_calls() == []
