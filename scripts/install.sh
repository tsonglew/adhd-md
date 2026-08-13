#!/usr/bin/env bash
# 把 adhd-md 安装到本机所有支持 SKILL.md 的 agent 宿主。
#
# 三种来源都能跑：
#   本地克隆      bash scripts/install.sh            软链到仓库，git pull 即更新
#   npx           npx adhd-md                        强制复制（npx 缓存会被清理）
#   curl | bash   curl -fsSL <url>/install.sh | bash 自己下 tarball
#
# 做法：canonical skill 放 ~/.agents/skills/adhd-md（本机各宿主已有的共享约定），
# 再往每个宿主的 skills 目录放一条软链。改一处，所有宿主同时生效。
set -euo pipefail

GH="https://github.com/tsonglew/adhd-md"
TARBALL="https://codeload.github.com/tsonglew/adhd-md/tar.gz/refs/heads/main"
CANON="$HOME/.agents/skills/adhd-md"

MODE=link      # link | copy
SCOPE=user     # user | project
DRY=0
UNINSTALL=0
REMOTE=0

usage() {
  cat <<'EOF'
用法：install.sh [选项]

  --copy         复制而非软链 canonical skill
  --link         强制软链（本地克隆时的默认，方便开发）
  --project      装到当前仓库而非用户目录（.claude/ .grok/ .cursor/ .codex/）
  --uninstall    卸载
  --dry-run      只打印会做什么
  -h, --help     本帮助
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --copy) MODE=copy ;;
    --link) MODE=link ;;
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

# ── 卸载。不需要源码，提前处理
if [ "$UNINSTALL" = 1 ]; then
  echo "卸载 adhd-md"
  echo "$HOSTS" | while IFS='|' read -r cli dir; do
    if [ -e "$dir/adhd-md" ] || [ -L "$dir/adhd-md" ]; then
      echo "  - $dir/adhd-md"
      run rm -rf "$dir/adhd-md"
    fi
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

# ── 定位源码
REPO=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
  REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

if [ -n "$REPO" ] && [ -r "$REPO/skill/SKILL.md" ]; then
  case "$REPO" in
    */_npx/*|*/node_modules/*)
      # npx 把包解到临时缓存，缓存会被清理 —— 软链过去早晚变死链
      if [ "$MODE" = link ]; then
        echo "从 npx 缓存运行，改用复制（缓存会被清理，软链会变死链）"
        MODE=copy
      fi
      ;;
  esac
else
  # curl | bash：脚本从标准输入来的，本地没有源码，去下一份
  REMOTE=1
  MODE=copy
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  echo "下载源码"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$TARBALL" | tar -xzf - -C "$TMP" --strip-components=1
  elif command -v wget >/dev/null 2>&1; then
    wget -qO- "$TARBALL" | tar -xzf - -C "$TMP" --strip-components=1
  else
    echo "✗ 需要 curl 或 wget" >&2
    exit 1
  fi
  REPO="$TMP"
  [ -r "$REPO/skill/SKILL.md" ] || { echo "✗ 下载的包里没有 skill/SKILL.md" >&2; exit 1; }
fi

SRC="$REPO/skill"

# ── 自检：装之前先确认工具层是好的
if command -v python3 >/dev/null 2>&1; then
  echo "自检 adhd_md.py"
  if ! python3 "$SRC/scripts/adhd_md.py" selftest >/dev/null 2>&1; then
    echo "✗ 自检失败，中止安装。手动跑一遍看原因：" >&2
    echo "  python3 $SRC/scripts/adhd_md.py selftest" >&2
    exit 1
  fi
  echo "  ✓ 36 项通过"
else
  echo "! 没找到 python3，跳过自检"
  echo "  规则与工作流照样可用，但审计、格式修复、无损校验都需要 python3"
fi

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
echo "$HOSTS" | while IFS='|' read -r cli dir; do
  # CLI 装了，或目录已存在 → 装
  if ! command -v "$cli" >/dev/null 2>&1 && [ ! -d "$dir" ]; then
    printf "  %-14s 跳过（未安装）\n" "$cli"
    continue
  fi
  run mkdir -p "$dir"
  run rm -rf "$dir/adhd-md"
  if [ "$SCOPE" = project ]; then
    # 项目级不能软链到临时目录或用户目录，直接放实体
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
  elif [ -r "$REPO/adapters/codex/adhd-md.prompt.md" ]; then
    sed "s|__CANON__|$TARGET|g" "$REPO/adapters/codex/adhd-md.prompt.md" \
      > "$HOME/.codex/prompts/adhd-md.md"
  else
    # npm 包里不带 adapters/，直接生成一份最小壳
    cat > "$HOME/.codex/prompts/adhd-md.md" <<EOF
---
description: 把 Markdown 改造成 ADHD 友好（可只改格式 / 只改内容 / 兼改）
argument-hint: <文件.md> [--scope=format|content|both] [--level=light|standard|deep]
---

读取并严格执行 \`$TARGET/SKILL.md\` 里定义的工作流。参数在 \`\$ARGUMENTS\` 里。

铁律：只重排信息，绝不删信息。\`scope=format\` 时 \`verify\` 是硬门禁，不通过必须回退。
EOF
  fi
  echo "  ✓ /adhd-md"
fi

if [ "$REMOTE" = 1 ]; then
  STANDALONE="$GH/blob/main/dist/adhd-md.standalone.md"
else
  STANDALONE="$REPO/dist/adhd-md.standalone.md"
fi

cat <<EOF

装好了。试试：

  python3 $TARGET/scripts/adhd_md.py audit 你的文档.md

或者在任一 agent 里直接说：
  「把 README.md 改成 ADHD 友好的，只改格式」

没有命令执行能力的环境（网页版 LLM）用自包含单文件：
  $STANDALONE

卸载：
  bash <(curl -fsSL https://tsonglew.github.io/adhd-md/install.sh) --uninstall
EOF
