#!/usr/bin/env bash
# Symlink dotfiles into their real locations. Existing non-symlink targets are
# moved aside to <target>.bak.
#   ./install.sh              install everything
#   ./install.sh nvim wt      install only the named parts (nvim, herdr, wt, hammerspoon)
#   ./install.sh --linux      install everything except the macOS-only parts (hammerspoon)
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
  echo "usage: $0 [--linux] [nvim] [herdr] [wt] [hammerspoon]   (no parts installs all)"
  echo "  --linux  skip macOS-only parts (hammerspoon)"
}

linux=false
parts=()
for arg in "$@"; do
  case $arg in
    nvim | herdr | wt | hammerspoon) parts+=("$arg") ;;
    --linux) linux=true ;;
    -h | --help) usage; exit 0 ;;
    *) echo "unknown part: $arg"; usage; exit 1 ;;
  esac
done

if [[ ${#parts[@]} -eq 0 ]]; then
  parts=(nvim herdr wt)
  $linux || parts+=(hammerspoon)
elif $linux; then
  for part in "${parts[@]}"; do
    if [[ $part == hammerspoon ]]; then
      echo "hammerspoon is macOS-only; drop it or --linux"; exit 1
    fi
  done
fi

for part in "${parts[@]}"; do
  case $part in
    nvim) link "$here/nvim" "$HOME/.config/nvim" ;;
    herdr)
      link "$here/herdr/config.toml" "$HOME/.config/herdr/config.toml"
      link "$here/bin/herdr-tabs" "$HOME/.local/bin/herdr-tabs"
      link "$here/bin/hp" "$HOME/.local/bin/hp"
      ;;
    wt) link "$here/bin/wt" "$HOME/.local/bin/wt" ;;
    hammerspoon) link "$here/hammerspoon/init.lua" "$HOME/.hammerspoon/init.lua" ;;
  esac
done
