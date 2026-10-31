#!/usr/bin/env bash
# 把 ~/.local/bin/jb 链接到本仓库里的 jb; 之后 git pull 即可更新.
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$HOME/.local/bin"
chmod +x "$SRC/jb"
ln -sf "$SRC/jb" "$HOME/.local/bin/jb"
echo "已安装: $HOME/.local/bin/jb -> $SRC/jb"
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) echo "提示: ~/.local/bin 不在 PATH 中, 在 ~/.bashrc 里加一行: export PATH=\"\$HOME/.local/bin:\$PATH\"" ;;
esac
