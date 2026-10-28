# dotfiles

Personal config for Neovim, [herdr](https://github.com/ogulcancelik/herdr), and a few helper scripts.

| Path                | Linked to                     | What it is                                      |
| ------------------- | ----------------------------- | ----------------------------------------------- |
| `nvim/`             | `~/.config/nvim`              | [LazyVim](https://lazyvim.github.io) config     |
| `herdr/config.toml` | `~/.config/herdr/config.toml` | herdr config (catppuccin theme, `wt` popup key) |
| `bin/wt`            | `~/.local/bin/wt`             | Create a git worktree and open it in herdr      |

## Getting started

### Requirements

- `git`, `bash`
- [Neovim](https://neovim.io) 0.11+ (for LazyVim)
- [herdr](https://github.com/ogulcancelik/herdr)
- [fzf](https://github.com/junegunn/fzf) (used by `wt` for branch picking)
- `~/.local/bin` on your `PATH`

Optional, used by language extras and `wt` when the project needs them: `node`/`pnpm`/`npm`/`yarn`, `uv`, `composer`, `clang-format`.

### Install

```sh
git clone https://github.com/evanwiseman/dotfiles.git ~/dev/github.com/evanwiseman/dotfiles
cd ~/dev/github.com/evanwiseman/dotfiles
./install.sh
```

`install.sh` symlinks each entry in the table above into place. It is safe to re-run:

- already-correct symlinks are left alone (`ok`)
- an existing file or directory at the target is moved to `<target>.bak` first (`backup`)

Then open `nvim` once and let lazy.nvim install plugins.

### Uninstall

Remove the symlinks and restore any `.bak` copies:

```sh
rm ~/.config/nvim ~/.config/herdr/config.toml ~/.local/bin/wt
# e.g. mv ~/.config/nvim.bak ~/.config/nvim
```

## Neovim

LazyVim starter with these customizations:

- Extras enabled in `nvim/lazyvim.json` (clangd, go, python, typescript, docker, sql, dap, test, prettier, eslint, and more)
- Python LSP set to `basedpyright` with `ruff` (`nvim/lua/config/options.lua`, `nvim/lua/plugins/python.lua`)
- `clang-format` for C/C++ via conform.nvim (`nvim/lua/plugins/clang_format.lua`)

Add plugins as new files under `nvim/lua/plugins/`.

## herdr

- Prefix key: `ctrl+\`
- `prefix` + `shift+1..9` switches to workspace 1-9
- `prefix` + `shift+g` opens `wt` in an 80% popup (the built-in `new_worktree` key is disabled)

## `wt`

Creates a worktree for a branch and opens it as a herdr workspace. Run it from anywhere inside a repo (or any of its worktrees). Where the worktree goes depends on the layout.

**Normal repo:** worktrees go under `.worktrees/`. `wt` adds `/.worktrees/` to `.git/info/exclude`, so they never show up as untracked.

```
myrepo/
├── .git/
├── .worktrees/
│   └── feature-x/    # worktree created by wt
└── ...               # main checkout
```

**Bare-layout repo:** worktrees sit next to each other.

```
myrepo/
├── .bare/        # bare git dir (any name works)
├── .git          # file containing "gitdir: ./.bare", so git works from the root
├── main/         # worktree
└── feature-x/    # worktree created by wt
```

To set up a repo in the bare layout:

```sh
mkdir myrepo && cd myrepo
git clone --bare <url> .bare
echo "gitdir: ./.bare" > .git
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
git fetch origin
git worktree add main main
```

Then:

```sh
wt              # pick a branch with fzf, or type a new name to create one
wt feature-x    # skip the picker
```

The picker lists all branches by default. `ctrl-l` shows only local branches, `ctrl-o` only branches on origin (online), and `ctrl-a` goes back to all. Branches deleted on origin are pruned on fetch, and local branches whose upstream was deleted are left out (typing the exact name still opens one).

What it does:

1. Fetches `origin` and finds its default branch.
2. Adds a worktree at `<repo>/.worktrees/<branch>` (normal) or `<repo>/<branch>` (bare):
   - existing local branch → checks it out
   - remote-only branch → creates a tracking branch
   - new name → branches off the origin default branch
3. Copies `.env` from the main checkout (normal) or the default-branch worktree (bare), else from any other worktree that has one.
4. Installs dependencies if it finds `composer.json`, `pnpm-lock.yaml` / `package-lock.json` / `yarn.lock`, or `uv.lock`.
5. Opens the worktree in herdr and focuses it.

## Tests

`tests/` covers `wt` with pytest. Each test runs the real script against throwaway git repos, with stubbed `herdr` and `fzf` and your git config isolated. Needs [uv](https://docs.astral.sh/uv/):

```sh
uv run pytest                 # tests
uv run ruff check tests       # lint
uv run ruff format tests      # format
uv run basedpyright           # type check
```
