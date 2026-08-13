#!/usr/bin/env bash
# 从 site/og.html 与 site/favicon.svg 渲染位图产物。
#
# 需要 gstack browse（无头 Chromium）。产物已提交进仓库，只在改了源模板时才需要重跑。
#   site/og.png                1200x630  OG / Twitter 预览图
#   site/apple-touch-icon.png  180x180   iOS 主屏图标
#   site/favicon-32.png        32x32     旧浏览器兜底
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE="$REPO/site"

B="$HOME/.claude/skills/gstack/browse/dist/browse"
[ -x "$B" ] || { echo "找不到 browse：$B" >&2; exit 1; }

PORT=8812
python3 -m http.server "$PORT" --directory "$SITE" >/dev/null 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null || true' EXIT
sleep 1

shot() { # 视口 输出 [url]
  "$B" viewport "$1" >/dev/null
  "$B" goto "http://localhost:$PORT/${3:-og.html}" >/dev/null
  sleep 2   # 等 Google Fonts
  "$B" screenshot "$2" --viewport >/dev/null
  echo "  $(basename "$2")  $1"
}

echo "渲染："
shot 1200x630 "$SITE/og.png"                og.html
shot 180x180  "$SITE/apple-touch-icon.png"  icon-square.svg
shot 32x32    "$SITE/favicon-32.png"        favicon.svg

"$B" viewport 1440x900 >/dev/null
echo "完成。产物在 site/。"
