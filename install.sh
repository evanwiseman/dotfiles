#!/usr/bin/env bash
# Symlink dotfiles into their real locations. Existing non-symlink targets are
# moved aside to <target>.bak.
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

link "$here/nvim"              "$HOME/.config/nvim"
link "$here/herdr/config.toml" "$HOME/.config/herdr/config.toml"
link "$here/bin/wt"            "$HOME/.local/bin/wt"
