#!/usr/bin/env bash
# Render the OG cards and icons with a locally installed Chrome/Chromium.
# Outputs: site/public/og*.png (1200x630), apple-touch-icon.png (180x180),
# and favicon-32.png (32x32). Source templates remain editable; do not hand-edit PNGs.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE="$REPO/site"
CHROME_PATH="${OG_CHROME:-}"

usage() {
  cat <<'EOF'
Usage: bash scripts/build-og.sh [--chrome PATH]

Render site/og.html, site/og-en.html, and the SVG icons into site/public/.
Set OG_CHROME=/path/to/chrome or pass --chrome PATH to choose a browser.
Without an explicit path, the script searches PATH and standard Chrome/Chromium
application locations. Google Fonts are used when reachable; system fonts are
used as fallbacks when offline. Node 22.12+ reads the shared bilingual copy from
site/src/i18n/ui.ts before rendering the temporary HTML templates.
EOF
}

while (($#)); do
  case "$1" in
    --chrome|--chrome-bin)
      if (($# < 2)); then
        echo "缺少 --chrome 的路径参数。" >&2
        usage >&2
        exit 2
      fi
      CHROME_PATH="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "未知参数：$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

resolve_chrome() {
  if [[ -n "$CHROME_PATH" ]]; then
    if [[ "$CHROME_PATH" == */* ]]; then
      [[ -x "$CHROME_PATH" ]] && return 0
    else
      CHROME_PATH="$(command -v "$CHROME_PATH" || true)"
      [[ -n "$CHROME_PATH" && -x "$CHROME_PATH" ]] && return 0
    fi
    echo "指定的 Chrome/Chromium 不存在或不可执行：$CHROME_PATH" >&2
    return 1
  fi

  local candidate
  for candidate in google-chrome google-chrome-stable chromium chromium-browser chrome; do
    CHROME_PATH="$(command -v "$candidate" || true)"
    if [[ -n "$CHROME_PATH" && -x "$CHROME_PATH" ]]; then
      return 0
    fi
  done
  for candidate in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "$HOME/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "$HOME/Applications/Chromium.app/Contents/MacOS/Chromium"; do
    if [[ -x "$candidate" ]]; then
      CHROME_PATH="$candidate"
      return 0
    fi
  done
  return 1
}

if ! resolve_chrome; then
  cat >&2 <<'EOF'
找不到可运行的 Chrome/Chromium。请安装 Google Chrome 或 Chromium，或显式指定路径：
  OG_CHROME=/path/to/chrome bash scripts/build-og.sh
  bash scripts/build-og.sh --chrome /path/to/chrome
EOF
  exit 1
fi

CHROME_VERSION="$("$CHROME_PATH" --version 2>&1 | head -n 1)"
if [[ -z "$CHROME_VERSION" ]]; then
  echo "无法读取浏览器版本：$CHROME_PATH --version" >&2
  exit 1
fi

TEMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/adhd-md-og.XXXXXX")"
trap 'rm -rf "$TEMP_ROOT"' EXIT
mkdir -p "$SITE/public"

node --experimental-strip-types --input-type=module - "$SITE" "$TEMP_ROOT" <<'JS'
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const [site, output] = process.argv.slice(2);
const { ui } = await import(pathToFileURL(resolve(site, "src/i18n/ui.ts")).href);
const escape = (value) => value.replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[char]);
for (const [language, filename] of [["zh", "og.html"], ["en", "og-en.html"]]) {
  const copy = ui[language].og;
  const values = { ...copy, tag1: copy.tags[0], tag2: copy.tags[1], tag3: copy.tags[2] };
  const source = readFileSync(resolve(site, filename), "utf8");
  const rendered = source.replace(/\{\{(\w+)\}\}/g, (_, key) => {
    if (typeof values[key] !== "string") throw new Error(`Missing ${language} OG text: ${key}`);
    return escape(values[key]);
  });
  writeFileSync(resolve(output, filename), rendered);
}
JS

echo "浏览器：$CHROME_VERSION"
echo "运行时：$(uname -s) / Bash $BASH_VERSION / Python $(python3 --version 2>&1)"
echo "字体：模板请求 Manrope、Noto Sans SC 与 IBM Plex Mono；离线时回退到系统字体。"
echo "渲染："

render_count=0
render() {
  local width="$1" height="$2" output="$3" source="$4"
  local source_url wrapper log profile
  local -a chrome_args
  render_count=$((render_count + 1))

  case "$source" in
    *.svg)
      wrapper="$TEMP_ROOT/icon-$render_count.html"
      source_url="$(python3 - "$source" "$wrapper" "$width" "$height" <<'PY'
from html import escape
from pathlib import Path
import sys

source = Path(sys.argv[1]).resolve().as_uri()
wrapper = Path(sys.argv[2])
width, height = sys.argv[3:5]
wrapper.write_text(
    '<!doctype html><html><head><meta charset="utf-8">'
    f'<style>html,body{{margin:0;width:{width}px;height:{height}px;overflow:hidden}}'
    'img{display:block;width:100%;height:100%}</style></head>'
    f'<body><img src="{escape(source, quote=True)}"></body></html>',
    encoding="utf-8",
)
print(wrapper.as_uri())
PY
      )"
      ;;
    *)
      source_url="$(python3 - "$source" <<'PY'
from pathlib import Path
import sys
print(Path(sys.argv[1]).resolve().as_uri())
PY
      )"
      ;;
  esac

  profile="$TEMP_ROOT/profile-$render_count"
  log="$TEMP_ROOT/chrome-$render_count.log"
  chrome_args=(
    --headless=new
    --disable-gpu
    --hide-scrollbars
    --allow-file-access-from-files
    --no-first-run
    --no-default-browser-check
    --force-device-scale-factor=1
    --run-all-compositor-stages-before-draw
    --virtual-time-budget=2500
    "--user-data-dir=$profile"
    "--window-size=$width,$height"
    "--screenshot=$output"
  )
  if [[ "$(uname -s)" == Linux && "$(id -u)" == 0 ]]; then
    chrome_args+=(--no-sandbox)
  fi
  if ! "$CHROME_PATH" "${chrome_args[@]}" "$source_url" >"$log" 2>&1; then
    cat "$log" >&2
    echo "渲染失败：$(basename "$output")" >&2
    return 1
  fi

  python3 - "$output" "$width" "$height" <<'PY'
from pathlib import Path
import struct
import sys

path = Path(sys.argv[1])
expected = tuple(map(int, sys.argv[2:4]))
data = path.read_bytes()
if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
    raise SystemExit(f"无效 PNG：{path}")
actual = struct.unpack(">II", data[16:24])
if actual != expected:
    raise SystemExit(f"PNG 尺寸错误：{path}，预期 {expected[0]}x{expected[1]}，实际 {actual[0]}x{actual[1]}")
print(f"  {path.name}  {actual[0]}x{actual[1]}")
PY
}

render 1200 630 "$SITE/public/og.png" "$TEMP_ROOT/og.html"
render 1200 630 "$SITE/public/og-en.png" "$TEMP_ROOT/og-en.html"
render 180 180 "$SITE/public/apple-touch-icon.png" "$SITE/icon-square.svg"
render 32 32 "$SITE/public/favicon-32.png" "$SITE/public/favicon.svg"
echo "完成。产物在 site/public/。"
