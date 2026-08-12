#!/usr/bin/env bash
# 把 adhd-md 安装到本机所有支持 SKILL.md 的 agent 宿主。
#
# 做法：canonical skill 放 ~/.agents/skills/adhd-md（这是本机各宿主已有的共享约定），
# 再往每个宿主的 skills 目录放一条软链。改一处，所有宿主同时生效。
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO/skill"
CANON="$HOME/.agents/skills/adhd-md"

MODE=link      # link | copy
SCOPE=user     # user | project
DRY=0
UNINSTALL=0

usage() {
  cat <<'EOF'
用法：install.sh [选项]

  --copy         复制而非软链 canonical skill（默认软链到本仓库，git pull 即更新）
  --project      装到当前仓库而非用户目录（.claude/ .grok/ .cursor/ .codex/）
  --uninstall    卸载
  --dry-run      只打印会做什么
  -h, --help     本帮助
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --copy) MODE=copy ;;
    --project) SCOPE=project ;;
    --uninstall) UNINSTALL=1 ;;
    --dry-run) DRY=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知选项：$1" >&2; usage; exit 2 ;;
  esac
  shift
done

run() {
  if [ "$DRY" = 1 ]; then echo "  + $*"; else "$@"; fi
}

# ── 宿主表：CLI 名 → 用户级 skills 目录（P0 实证，见 docs/host-matrix.md）
hosts_user() {
  cat <<EOF
claude|$HOME/.claude/skills
codex|$HOME/.codex/skills
grok|$HOME/.grok/skills
gemini|$HOME/.gemini/skills
cursor-agent|$HOME/.cursor/skills
opencode|$HOME/.config/opencode/skills
EOF
}

# 项目级。Grok 也读 .claude/skills，所以两者都装能覆盖四个宿主。
hosts_project() {
  root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
  cat <<EOF
claude|$root/.claude/skills
grok|$root/.grok/skills
cursor|$root/.cursor/skills
codex|$root/.codex/skills
EOF
}

if [ "$SCOPE" = project ]; then HOSTS="$(hosts_project)"; else HOSTS="$(hosts_user)"; fi

# ── 卸载
if [ "$UNINSTALL" = 1 ]; then
  echo "卸载 adhd-md"
  echo "$HOSTS" | while IFS='|' read -r cli dir; do
    [ -e "$dir/adhd-md" ] || [ -L "$dir/adhd-md" ] || continue
    echo "  - $dir/adhd-md"
    run rm -rf "$dir/adhd-md"
  done
  if [ -e "$HOME/.codex/prompts/adhd-md.md" ]; then
    echo "  - $HOME/.codex/prompts/adhd-md.md"
    run rm -f "$HOME/.codex/prompts/adhd-md.md"
  fi
  if [ "$SCOPE" = user ] && { [ -e "$CANON" ] || [ -L "$CANON" ]; }; then
    echo "  - $CANON"
    run rm -rf "$CANON"
  fi
  echo "完成。"
  exit 0
fi

# ── 自检：装之前先确认工具层是好的
echo "自检 adhd_md.py"
if ! python3 "$SRC/scripts/adhd_md.py" selftest >/dev/null 2>&1; then
  echo "✗ 自检失败，中止安装。手动跑一遍看原因：" >&2
  echo "  python3 $SRC/scripts/adhd_md.py selftest" >&2
  exit 1
fi
echo "  ✓ 30 项通过"

# ── canonical 位置
if [ "$SCOPE" = user ]; then
  echo "canonical skill → $CANON"
  run mkdir -p "$(dirname "$CANON")"
  run rm -rf "$CANON"
  if [ "$MODE" = copy ]; then
    run cp -R "$SRC" "$CANON"
  else
    run ln -sfn "$SRC" "$CANON"
  fi
  TARGET="$CANON"
else
  TARGET="$SRC"
fi

# ── 往各宿主放链接
echo "安装到宿主："
n=0
echo "$HOSTS" | while IFS='|' read -r cli dir; do
  # CLI 装了，或目录已存在 → 装
  if ! command -v "$cli" >/dev/null 2>&1 && [ ! -d "$dir" ]; then
    printf "  %-14s 跳过（未安装）\n" "$cli"
    continue
  fi
  run mkdir -p "$dir"
  run rm -rf "$dir/adhd-md"
  if [ "$MODE" = copy ] && [ "$SCOPE" = project ]; then
    run cp -R "$SRC" "$dir/adhd-md"
  else
    run ln -sfn "$TARGET" "$dir/adhd-md"
  fi
  printf "  %-14s ✓ %s\n" "$cli" "$dir/adhd-md"
done

# ── Codex 额外的斜杠命令入口（skill 之外的显式调用通道）
if [ "$SCOPE" = user ] && { command -v codex >/dev/null 2>&1 || [ -d "$HOME/.codex" ]; }; then
  echo "Codex 斜杠命令："
  run mkdir -p "$HOME/.codex/prompts"
  if [ "$DRY" = 1 ]; then
    echo "  + 生成 $HOME/.codex/prompts/adhd-md.md"
  else
    sed "s|__CANON__|$TARGET|g" "$REPO/adapters/codex/adhd-md.prompt.md" \
      > "$HOME/.codex/prompts/adhd-md.md"
  fi
  echo "  ✓ /adhd-md"
fi

cat <<EOF

装好了。试试：

  python3 $TARGET/scripts/adhd_md.py audit 你的文档.md

或者在任一 agent 里直接说：
  「把 README.md 改成 ADHD 友好的，只改格式」

没有命令执行能力的环境（网页版 LLM）用自包含单文件：
  $REPO/dist/adhd-md.standalone.md
EOF
