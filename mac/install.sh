#!/usr/bin/env bash
# 在 Mac 上安装常驻的隧道 + 通知 (launchd, 登录自启, 断线重连).
#   mac/install.sh user@host [-p 22] [--token xxx]
#   mac/install.sh --uninstall
set -euo pipefail
LABEL=com.jb.mac
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DEST="$HOME/.local/share/jbmac"
DOMAIN="gui/$(id -u)"

if [ "${1:-}" = "--uninstall" ]; then
  launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"
  echo "已卸载 $LABEL"
  exit 0
fi
if [ $# -lt 1 ]; then
  echo "用法: $0 user@host [-p SSH端口] [--token TOKEN]"
  exit 1
fi

mkdir -p "$DEST" "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
cp "$(cd "$(dirname "$0")" && pwd)/jbmac.py" "$DEST/jbmac.py"

xml() { printf '%s' "$1" | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g'; }
ARGS=""
for a in "$@"; do ARGS+="    <string>$(xml "$a")</string>"$'\n'; done

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>$DEST/jbmac.py</string>
$ARGS  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>20</integer>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/jbmac.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/jbmac.log</string>
</dict>
</plist>
EOF

launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$PLIST"
echo "已启动 $LABEL, 日志: ~/Library/Logs/jbmac.log"
echo "打开 http://127.0.0.1:18765/ 查看面板"
