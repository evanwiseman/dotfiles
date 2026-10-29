#!/usr/bin/env bash
# Remove symlinks made by install.sh and restore any <target>.bak it moved aside.
# Targets that aren't our symlinks are left alone.
#   ./uninstall.sh            uninstall everything
#   ./uninstall.sh nvim wt    uninstall only the named parts (nvim, herdr, wt)
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)

remove() {
  local src=$1 dst=$2
  if [[ ! -L $dst || $(readlink "$dst") != "$src" ]]; then
    if [[ -e $dst || -L $dst ]]; then
      echo "skip    $dst (not linked to $src)"
    else
      echo "skip    $dst (not installed)"
    fi
    return
  fi
  rm "$dst"
  echo "remove  $dst"
  if [[ -e $dst.bak || -L $dst.bak ]]; then
    mv "$dst.bak" "$dst"
    echo "restore $dst.bak -> $dst"
  fi
}

usage() {
  echo "usage: $0 [nvim] [herdr] [wt]   (no arguments uninstalls all)"
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
    nvim) remove "$here/nvim" "$HOME/.config/nvim" ;;
    herdr)
      remove "$here/herdr/config.toml" "$HOME/.config/herdr/config.toml"
      remove "$here/bin/herdr-tabs" "$HOME/.local/bin/herdr-tabs"
      ;;
    wt) remove "$here/bin/wt" "$HOME/.local/bin/wt" ;;
  esac
done
