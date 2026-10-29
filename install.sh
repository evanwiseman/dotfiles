#!/usr/bin/env bash
# Symlink dotfiles into their real locations. Existing non-symlink targets are
# moved aside to <target>.bak.
#   ./install.sh              install everything
#   ./install.sh nvim wt      install only the named parts (nvim, herdr, wt)
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)

link() {
  local src=$1 dst=$2
  mkdir -p "$(dirname "$dst")"
  if [[ -L $dst && $(readlink "$dst") == "$src" ]]; then
    echo "ok      $dst"
    return
  fi
  if [[ -e $dst || -L $dst ]]; then
    mv "$dst" "$dst.bak"
    echo "backup  $dst -> $dst.bak"
  fi
  ln -s "$src" "$dst"
  echo "link    $dst -> $src"
}

usage() {
  echo "usage: $0 [nvim] [herdr] [wt]   (no arguments installs all)"
}

parts=("$@")
[[ ${#parts[@]} -gt 0 ]] || parts=(nvim herdr wt)

for part in "${parts[@]}"; do
  case $part in
    nvim | herdr | wt) ;;
    -h | --help) usage; exit 0 ;;
    *) echo "unknown part: $part"; usage; exit 1 ;;
  esac
done

for part in "${parts[@]}"; do
  case $part in
    nvim) link "$here/nvim" "$HOME/.config/nvim" ;;
    herdr)
      link "$here/herdr/config.toml" "$HOME/.config/herdr/config.toml"
      link "$here/bin/herdr-tabs" "$HOME/.local/bin/herdr-tabs"
      ;;
    wt) link "$here/bin/wt" "$HOME/.local/bin/wt" ;;
  esac
done
