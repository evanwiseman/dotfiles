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

The repo uses the bare layout that `wt` expects (see [`wt`](#wt)), so clone it bare and add a `main` worktree:

```sh
mkdir -p ~/dev/github.com/evanwiseman/dotfiles
cd ~/dev/github.com/evanwiseman/dotfiles
git clone --bare https://github.com/evanwiseman/dotfiles.git .bare
echo "gitdir: ./.bare" > .git
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
git fetch origin
git worktree add main main
./main/install.sh
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
- `prefix` + `shift+g` opens `wt` in an 80% popup (the built-in `new_worktree` key is disabled)

## `wt`

Creates a worktree for a branch and opens it as a herdr workspace. Run it from anywhere inside a **bare-layout** repo:

```
myrepo/
├── .bare/        # bare git dir (any name works)
├── .git          # file containing "gitdir: ./.bare", so git works from the root
├── main/         # worktree
└── feature-x/    # worktree created by wt
```

```sh
wt              # pick a branch with fzf, or type a new name to create one
wt feature-x    # skip the picker
```

What it does:

1. Fetches `origin` and finds its default branch.
2. Adds a worktree at `<repo>/<branch>`:
   - existing local branch → checks it out
   - remote-only branch → creates a tracking branch
   - new name → branches off the origin default branch
3. Copies `.env` from the default-branch worktree (or any sibling that has one).
4. Installs dependencies if it finds `composer.json`, `pnpm-lock.yaml` / `package-lock.json` / `yarn.lock`, or `uv.lock`.
5. Opens the worktree in herdr and focuses it.
