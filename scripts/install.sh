#!/usr/bin/env bash
# 把 adhd-md 安装到本机所有支持 SKILL.md 的 agent 宿主。
#
# 三种来源都能跑：
#   本地克隆      bash scripts/install.sh            软链到仓库，git pull 即更新
#   npx           npx adhd-md                        强制复制（npx 缓存会被清理）
#   curl | bash   curl -fsSL <url>/install.sh | bash 自己下 tarball
#
# 做法：canonical skill 放 ~/.agents/skills/adhd-md（本机各宿主已有的共享约定）。
# 用户级宿主目录指向 canonical；项目级目录保存带归属标记的实体副本。
# 更新先在目标同级暂存并通过自检，再切换路径；失败时从同级备份回滚。
set -euo pipefail

GH="https://github.com/tsonglew/adhd-md"
TARBALL="https://codeload.github.com/tsonglew/adhd-md/tar.gz/refs/heads/main"
# ADHD_MD_HOME 供隔离测试及需要指定用户级安装根的环境使用；未设置时沿用系统用户目录。
INSTALL_HOME="${ADHD_MD_HOME:-$HOME}"
CANON="$INSTALL_HOME/.agents/skills/adhd-md"
CANON_OWNER="$INSTALL_HOME/.agents/skills/.adhd-md-managed-canonical"
OWNER_TOKEN="managed-by-adhd-md-install-v1"
PROJECT_OWNER_FILE=".adhd-md-managed"

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
  --project      装到当前仓库而非用户目录；canonical 位于 .agents/skills/adhd-md
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

marker_matches() {
  local marker_path="$1" marker_value=""
  [ -f "$marker_path" ] && [ ! -L "$marker_path" ] || return 1
  IFS= read -r marker_value < "$marker_path" || [ -n "$marker_value" ] || return 1
  [ "$marker_value" = "$OWNER_TOKEN" ]
}

# ── 单一宿主表：宿主名、CLI 别名、用户级目录、项目级目录
# Cursor 新版使用 cursor-agent，旧版仍可能提供 cursor；两种入口共用 .cursor/skills。
host_table() {
  printf '%s\n' \
    'claude|claude|.claude/skills|.claude/skills' \
    'codex|codex|.codex/skills|.codex/skills' \
    'grok|grok|.grok/skills|.grok/skills' \
    'gemini|gemini|.gemini/skills|' \
    'cursor|cursor-agent cursor|.cursor/skills|.cursor/skills' \
    'opencode|opencode|.config/opencode/skills|'
}

PROJECT_ROOT=""
PROJECT_CANON=""
PROJECT_CANON_OWNER=""
if [ "$SCOPE" = project ]; then
  PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
  PROJECT_CANON="$PROJECT_ROOT/.agents/skills/adhd-md"
  PROJECT_CANON_OWNER="$PROJECT_ROOT/.agents/skills/.adhd-md-managed-canonical"
fi

hosts_for_scope() {
  local root host cli_candidates user_relative project_relative relative cli candidate
  if [ "$SCOPE" = project ]; then root="$PROJECT_ROOT"; else root="$INSTALL_HOME"; fi
  while IFS='|' read -r host cli_candidates user_relative project_relative; do
    if [ "$SCOPE" = project ]; then relative="$project_relative"; else relative="$user_relative"; fi
    [ -n "$relative" ] || continue
    cli="$host"
    for candidate in $cli_candidates; do
      if command -v "$candidate" >/dev/null 2>&1; then cli="$candidate"; break; fi
    done
    printf '%s|%s|%s\n' "$host" "$cli" "$root/$relative"
  done < <(host_table)
}

HOSTS="$(hosts_for_scope)"
HOST_COUNT=0
while IFS='|' read -r host cli dir; do
  if command -v "$cli" >/dev/null 2>&1 || [ -d "$dir" ]; then HOST_COUNT=$((HOST_COUNT + 1)); fi
done <<< "$HOSTS"

# Install, update, and uninstall share one scope lock. All replacement payloads
# are staged beside their destination so each rename stays on the same volume.
if [ "$SCOPE" = project ]; then
  LOCK_PARENT="$PROJECT_ROOT/.agents/skills"
else
  LOCK_PARENT="$INSTALL_HOME/.agents/skills"
fi
LOCK_DIR="$LOCK_PARENT/.adhd-md-install.lock"
LOCK_HELD=0
TRANSACTION_ACTIVE=0
TRANSACTION_COMMITTED=0
ROLLBACK_FAILED=0
TMP=""
declare -a TX_TARGETS=()
declare -a TX_BACKUPS=()
declare -a TX_STAGES=()
declare -a TX_HAD_OLD=()

write_lock_owner() {
  local owner_tmp="$LOCK_DIR/owner.tmp"
  printf '%s\n%s\n' "$OWNER_TOKEN" "$$" > "$owner_tmp"
  mv -f "$owner_tmp" "$LOCK_DIR/owner"
}

rollback_entries() {
  local target="$1" backup="$2" stage="$3" had_old="$4"
  if [ -e "$backup" ] || [ -L "$backup" ]; then
    if [ -e "$target" ] || [ -L "$target" ]; then rm -rf "$target" || return 1; fi
    mv "$backup" "$target" || return 1
  elif [ "$had_old" = 0 ] && { [ -e "$target" ] || [ -L "$target" ]; } && [ ! -e "$stage" ] && [ ! -L "$stage" ]; then
    rm -rf "$target" || return 1
  fi
  rm -rf "$stage" || return 1
}

rollback_current_transaction() {
  local i
  set +e
  for ((i=${#TX_TARGETS[@]}-1; i>=0; i--)); do
    rollback_entries "${TX_TARGETS[$i]}" "${TX_BACKUPS[$i]}" "${TX_STAGES[$i]}" "${TX_HAD_OLD[$i]}" || ROLLBACK_FAILED=1
  done
  if [ "$ROLLBACK_FAILED" -eq 0 ]; then
    rm -f "$LOCK_DIR/targets" "$LOCK_DIR/state" || ROLLBACK_FAILED=1
    if [ "$ROLLBACK_FAILED" -eq 0 ]; then TRANSACTION_ACTIVE=0; fi
  fi
  set -e
  [ "$ROLLBACK_FAILED" -eq 0 ]
}

recover_stale_transaction() {
  local state target backup stage had_old i
  state=""
  if [ -f "$LOCK_DIR/state" ]; then IFS= read -r state < "$LOCK_DIR/state" || true; fi
  TX_TARGETS=()
  TX_BACKUPS=()
  TX_STAGES=()
  TX_HAD_OLD=()
  if [ -f "$LOCK_DIR/targets" ]; then
    while IFS= read -r -d '' target && IFS= read -r -d '' backup && IFS= read -r -d '' stage && IFS= read -r -d '' had_old; do
      TX_TARGETS+=("$target")
      TX_BACKUPS+=("$backup")
      TX_STAGES+=("$stage")
      TX_HAD_OLD+=("$had_old")
    done < "$LOCK_DIR/targets"
  fi
  set +e
  if [ "$state" = committed ]; then
    for ((i=0; i<${#TX_BACKUPS[@]}; i++)); do
      rm -rf "${TX_BACKUPS[$i]}" "${TX_STAGES[$i]}" || return 1
    done
  else
    for ((i=${#TX_TARGETS[@]}-1; i>=0; i--)); do
      rollback_entries "${TX_TARGETS[$i]}" "${TX_BACKUPS[$i]}" "${TX_STAGES[$i]}" "${TX_HAD_OLD[$i]}" || return 1
    done
  fi
  rm -f "$LOCK_DIR/targets" "$LOCK_DIR/state" || return 1
  set -e
}

acquire_lock() {
  local owner_file="" owner_token="" owner_pid="" tries=0
  mkdir -p "$LOCK_PARENT"
  if [ -L "$LOCK_DIR" ]; then
    echo "✗ 安装锁路径是符号链接，拒绝继续：$LOCK_DIR" >&2
    return 1
  fi
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    LOCK_HELD=1
    write_lock_owner
    return 0
  fi

  for tries in 1 2 3 4 5 6 7 8 9 10; do
    owner_file="$LOCK_DIR/owner"
    owner_token=""
    owner_pid=""
    if [ -f "$owner_file" ]; then
      { IFS= read -r owner_token; IFS= read -r owner_pid; } < "$owner_file" || true
    fi
    owner_token="${owner_token:-}"
    owner_pid="${owner_pid:-}"
    case "$owner_pid" in ''|*[!0-9]*)
      echo "✗ 安装锁缺少有效所有者信息，保留现场供恢复：$LOCK_DIR" >&2
      return 1
      ;;
    esac
    if kill -0 "$owner_pid" 2>/dev/null; then
      echo "✗ 检测到另一个安装器正在运行（PID ${owner_pid:-unknown}），本次不做并发写入。" >&2
      return 75
    fi
    if [ "$owner_token" != "$OWNER_TOKEN" ]; then
      echo "✗ 安装锁所有权标记无效，保留现场供检查：$LOCK_DIR" >&2
      return 1
    fi
    if mkdir "$LOCK_DIR/recovery" 2>/dev/null; then
      if recover_stale_transaction; then
        LOCK_HELD=1
        write_lock_owner
        rmdir "$LOCK_DIR/recovery"
        echo "已恢复上次中断的安装事务。" >&2
        return 0
      fi
      rmdir "$LOCK_DIR/recovery" 2>/dev/null || true
      echo "✗ 上次安装事务无法自动恢复；保留备份与日志：$LOCK_DIR" >&2
      return 1
    fi
    sleep 0.1
  done
  echo "✗ 无法取得安装锁：$LOCK_DIR" >&2
  return 75
}

finalize_transaction() {
  local i cleanup_failed=0
  printf '%s\n' committed > "$LOCK_DIR/state.tmp"
  mv -f "$LOCK_DIR/state.tmp" "$LOCK_DIR/state"
  TRANSACTION_ACTIVE=0
  TRANSACTION_COMMITTED=1
  for ((i=0; i<${#TX_BACKUPS[@]}; i++)); do
    rm -rf "${TX_BACKUPS[$i]}" "${TX_STAGES[$i]}" || cleanup_failed=1
  done
  if [ "$cleanup_failed" -eq 0 ]; then
    rm -f "$LOCK_DIR/targets" "$LOCK_DIR/state" || cleanup_failed=1
  fi
  if [ "$cleanup_failed" -eq 0 ]; then
    rm -rf "$LOCK_DIR"
    LOCK_HELD=0
  else
    echo "! 新版已安装，但旧版备份清理未完成；下次运行会自动清理：$LOCK_DIR" >&2
  fi
}

cleanup() {
  local status=$?
  trap - EXIT INT TERM HUP
  if [ "$TRANSACTION_ACTIVE" -eq 1 ]; then
    if rollback_current_transaction; then
      echo "! 安装未完成，已恢复更新前状态。" >&2
    else
      echo "✗ 自动回滚未完成；备份和事务日志保留在：$LOCK_DIR" >&2
      status=1
    fi
  fi
  if [ -n "$TMP" ] && [ -d "$TMP" ]; then rm -rf "$TMP" || status=1; fi
  if [ "$LOCK_HELD" -eq 1 ] && [ "$TRANSACTION_ACTIVE" -eq 0 ] && [ "$TRANSACTION_COMMITTED" -eq 0 ]; then
    rm -rf "$LOCK_DIR" || status=1
  fi
  exit "$status"
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM HUP
if [ "$DRY" -eq 0 ]; then acquire_lock || exit $?; fi

# ── 卸载。不需要源码，提前处理
if [ "$UNINSTALL" = 1 ]; then
  echo "卸载 adhd-md"
  echo "$HOSTS" | while IFS='|' read -r host cli dir; do
    asset="$dir/adhd-md"
    if [ "$SCOPE" = user ]; then
      if [ -L "$asset" ]; then
        if [ "$(readlink "$asset")" = "$CANON" ]; then
          echo "  - ${asset}（指向本工具 canonical）"
          run rm -f "$asset"
        else
          echo "  ! 保留非本工具 canonical 链接：${asset}"
        fi
      elif [ -e "$asset" ]; then
        echo "  ! 保留无法确认归属的宿主目录：${asset}"
      fi
    elif [ -L "$asset" ]; then
      echo "  ! 保留符号链接形式的项目资产：${asset}"
    elif [ -d "$asset" ]; then
      if marker_matches "$asset/$PROJECT_OWNER_FILE"; then
        echo "  - ${asset}（有本工具所有权标记）"
        run rm -rf "$asset"
      else
        echo "  ! 保留无法确认归属的项目目录：${asset}"
      fi
    elif [ -e "$asset" ]; then
      echo "  ! 保留非目录项目资产：${asset}"
    fi
  done
  if [ "$SCOPE" = project ]; then
    project_canon_managed=0
    if marker_matches "$PROJECT_CANON_OWNER"; then project_canon_managed=1; fi
    if [ -L "$PROJECT_CANON" ]; then
      echo "  ! 保留符号链接形式的项目 canonical：${PROJECT_CANON}"
    elif [ -d "$PROJECT_CANON" ]; then
      if [ "$project_canon_managed" = 1 ]; then
        echo "  - ${PROJECT_CANON}（有本工具所有权标记）"
        run rm -rf "$PROJECT_CANON"
      else
        echo "  ! 保留无法确认归属的项目 canonical：${PROJECT_CANON}"
      fi
    elif [ -e "$PROJECT_CANON" ]; then
      echo "  ! 保留非目录项目 canonical：${PROJECT_CANON}"
    fi
    if [ "$project_canon_managed" = 1 ]; then
      echo "  - $PROJECT_CANON_OWNER"
      run rm -f "$PROJECT_CANON_OWNER"
    elif [ -e "$PROJECT_CANON_OWNER" ] || [ -L "$PROJECT_CANON_OWNER" ]; then
      echo "  ! 保留无效或非本工具项目 canonical 所有权标记：${PROJECT_CANON_OWNER}"
    fi
  fi
  if [ "$SCOPE" = user ] && [ -f "$INSTALL_HOME/.codex/prompts/adhd-md.md" ] && [ ! -L "$INSTALL_HOME/.codex/prompts/adhd-md.md" ]; then
    echo "  - $INSTALL_HOME/.codex/prompts/adhd-md.md"
    run rm -f "$INSTALL_HOME/.codex/prompts/adhd-md.md"
  elif [ "$SCOPE" = user ] && { [ -e "$INSTALL_HOME/.codex/prompts/adhd-md.md" ] || [ -L "$INSTALL_HOME/.codex/prompts/adhd-md.md" ]; }; then
    echo "  ! 保留非普通文件形式的 Codex prompt"
  fi
  if [ "$SCOPE" = user ]; then
    canon_managed=0
    if marker_matches "$CANON_OWNER"; then canon_managed=1; fi
    if [ -L "$CANON" ]; then
      echo "  - ${CANON}（删除链接本身）"
      run rm -f "$CANON"
    elif [ -d "$CANON" ]; then
      if [ "$canon_managed" = 1 ]; then
        echo "  - ${CANON}（有本工具所有权标记）"
        run rm -rf "$CANON"
      else
        echo "  ! 保留无法确认归属的 canonical 目录：${CANON}"
      fi
    elif [ -e "$CANON" ]; then
      echo "  ! 保留非目录 canonical 资产：${CANON}"
    fi
    if [ "$canon_managed" = 1 ]; then
      echo "  - $CANON_OWNER"
      run rm -f "$CANON_OWNER"
    elif [ -e "$CANON_OWNER" ] || [ -L "$CANON_OWNER" ]; then
      echo "  ! 保留无效或非本工具 canonical 所有权标记：${CANON_OWNER}"
    fi
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
  TMP="$(mktemp -d "${TMPDIR:-/tmp}/adhd-md-install.XXXXXX")"
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

# ── 规划所有需要切换的资产，先检查冲突再准备事务
if [ "$SCOPE" = user ]; then TARGET="$CANON"; else TARGET="$PROJECT_CANON"; fi
declare -a PLAN_DEST=()
declare -a PLAN_KIND=()
declare -a PLAN_SOURCE=()
declare -a HOST_TARGETS=()

add_plan() {
  PLAN_DEST+=("$1")
  PLAN_KIND+=("$2")
  PLAN_SOURCE+=("$3")
}

if [ "$SCOPE" = user ]; then
  add_plan "$CANON" canonical "$SRC"
  add_plan "$CANON_OWNER" marker "$OWNER_TOKEN"
else
  add_plan "$PROJECT_CANON" project-canonical "$SRC"
  add_plan "$PROJECT_CANON_OWNER" marker "$OWNER_TOKEN"
fi

while IFS='|' read -r host cli dir; do
  if ! command -v "$cli" >/dev/null 2>&1 && [ ! -d "$dir" ]; then continue; fi
  asset="$dir/adhd-md"
  HOST_TARGETS+=("$asset")
  if [ "$SCOPE" = project ]; then
    add_plan "$asset" project-host "$SRC"
  else
    add_plan "$asset" host-link "$TARGET"
  fi
done <<< "$HOSTS"

PROMPT="$INSTALL_HOME/.codex/prompts/adhd-md.md"
if [ "$SCOPE" = user ] && { command -v codex >/dev/null 2>&1 || [ -d "$INSTALL_HOME/.codex" ]; }; then
  add_plan "$PROMPT" prompt "$TARGET"
fi

path_exists() { [ -e "$1" ] || [ -L "$1" ]; }

preflight_target() {
  local target="$1" kind="$2"
  if ! path_exists "$target"; then return 0; fi
  case "$kind" in
    canonical)
      if [ -L "$target" ]; then
        if marker_matches "$CANON_OWNER" || [ "$(readlink "$target")" = "$SRC" ]; then return 0; fi
      elif [ -d "$target" ] && marker_matches "$CANON_OWNER"; then
        return 0
      fi
      ;;
    project-canonical)
      if [ -d "$target" ] && [ ! -L "$target" ] && marker_matches "$PROJECT_CANON_OWNER"; then return 0; fi
      ;;
    host-link)
      if [ -L "$target" ] && [ "$(readlink "$target")" = "$CANON" ]; then return 0; fi
      ;;
    project-host)
      if [ -d "$target" ] && [ ! -L "$target" ] && marker_matches "$target/$PROJECT_OWNER_FILE"; then return 0; fi
      ;;
    marker)
      if marker_matches "$target"; then return 0; fi
      ;;
    prompt)
      if [ ! -d "$target" ] || [ -L "$target" ]; then return 0; fi
      ;;
  esac
  echo "✗ 目标已存在但无法确认由本工具管理，保留原内容并停止：$target" >&2
  return 1
}

if [ "$DRY" -eq 1 ]; then
  if [ "$SCOPE" = project ]; then echo "项目 canonical skill → $PROJECT_CANON"; else echo "canonical skill → $CANON"; fi
  echo "安装到宿主："
  while IFS='|' read -r host cli dir; do
    asset="$dir/adhd-md"
    if [ -d "$dir" ] || command -v "$cli" >/dev/null 2>&1; then
      printf "  %-14s ✓ %s\n" "$cli" "$asset"
    else
      printf "  %-14s 跳过（未安装）\n" "$cli"
    fi
  done <<< "$HOSTS"
  if [ "$HOST_COUNT" -eq 0 ]; then echo "! 没检测到已安装的宿主 CLI 或 skills 目录；计划 canonical 路径为 ${TARGET}。"; fi
  if [ "${#PLAN_DEST[@]}" -gt 0 ] && [[ " ${PLAN_DEST[*]} " == *" $PROMPT "* ]]; then echo "  + 生成 $PROMPT"; fi
  exit 0
fi

for i in "${!PLAN_DEST[@]}"; do preflight_target "${PLAN_DEST[$i]}" "${PLAN_KIND[$i]}"; done

RUN_ID="$$.$RANDOM.$RANDOM"
TX_COUNT=0
register_target() {
  local target="$1" parent base stage backup had_old=0
  parent="${target%/*}"
  base="${target##*/}"
  mkdir -p "$parent"
  stage="$parent/.${base}.adhd-md-stage-${RUN_ID}-${TX_COUNT}"
  backup="$parent/.${base}.adhd-md-backup-${RUN_ID}-${TX_COUNT}"
  if path_exists "$stage" || path_exists "$backup"; then
    echo "✗ 暂存路径冲突：$stage" >&2
    return 1
  fi
  if path_exists "$target"; then had_old=1; fi
  printf '%s\0%s\0%s\0%s\0' "$target" "$backup" "$stage" "$had_old" >> "$LOCK_DIR/targets"
  TX_TARGETS+=("$target")
  TX_BACKUPS+=("$backup")
  TX_STAGES+=("$stage")
  TX_HAD_OLD+=("$had_old")
  TX_COUNT=$((TX_COUNT + 1))
}

printf '%s\n' active > "$LOCK_DIR/state"
TRANSACTION_ACTIVE=1
for i in "${!PLAN_DEST[@]}"; do
  target="${PLAN_DEST[$i]}"
  kind="${PLAN_KIND[$i]}"
  source="${PLAN_SOURCE[$i]}"
  register_target "$target"
  stage="${TX_STAGES[${#TX_STAGES[@]}-1]}"
  case "$kind" in
    canonical)
      if [ "$MODE" = copy ]; then cp -R "$source" "$stage"; else ln -s "$source" "$stage"; fi
      ;;
    project-canonical|project-host)
      cp -R "$source" "$stage"
      ;;
    host-link)
      ln -s "$source" "$stage"
      ;;
    marker)
      printf '%s\n' "$source" > "$stage"
      ;;
    prompt)
      if [ -r "$REPO/adapters/codex/adhd-md.prompt.md" ]; then
        escaped_target="${source//\\/\\\\}"
        escaped_target="${escaped_target//&/\\&}"
        escaped_target="${escaped_target//|/\\|}"
        sed "s|__CANON__|$escaped_target|g" "$REPO/adapters/codex/adhd-md.prompt.md" > "$stage"
      else
        cat > "$stage" <<EOF
---
description: 把 Markdown 改造成 ADHD 友好（可只改格式 / 只改内容 / 兼改）
argument-hint: <文件.md> [--scope=format|content|both] [--level=light|standard|deep]
---

读取并严格执行 \`$TARGET/SKILL.md\` 里定义的工作流。参数在 \`\$ARGUMENTS\` 里。

铁律：只重排信息，绝不删信息。当前 \`verify --scope=format\` 比较正文 token 多重集，不检查词序或语义；先预览并人工复核后再写回。详细边界见 \`SKILL.md\`。
EOF
      fi
      ;;
  esac
  if [ "$kind" = project-host ]; then printf '%s\n' "$OWNER_TOKEN" > "$stage/$PROJECT_OWNER_FILE"; fi
done

# Validate the exact staged canonical copy before any installed path is moved.
if command -v python3 >/dev/null 2>&1; then
  staged_canonical="${TX_STAGES[0]}"
  if ! python3 "$staged_canonical/scripts/adhd_md.py" selftest >/dev/null 2>&1; then
    echo "✗ 暂存副本自检失败，现有安装保持不变。" >&2
    exit 1
  fi
  echo "  ✓ 暂存副本自检通过"
else
  echo "! 没找到 python3，跳过自检；审计、格式修复和不变量检查需要 python3" >&2
fi

for i in "${!PLAN_DEST[@]}"; do
  target="${PLAN_DEST[$i]}"
  backup="${TX_BACKUPS[$i]}"
  stage="${TX_STAGES[$i]}"
  if path_exists "$backup"; then
    echo "✗ 备份路径被占用，停止切换：$backup" >&2
    exit 1
  fi
  if path_exists "$target"; then mv "$target" "$backup"; fi
  if path_exists "$target"; then
    echo "✗ 切换期间目标被其他进程创建，停止切换：$target" >&2
    exit 1
  fi
  mv "$stage" "$target"
done

if [ "$SCOPE" = user ]; then
  echo "canonical skill → $CANON"
else
  echo "项目 canonical skill → $PROJECT_CANON"
fi
echo "安装到宿主："
while IFS='|' read -r host cli dir; do
  asset="$dir/adhd-md"
  if [[ " ${HOST_TARGETS[*]} " == *" $asset "* ]]; then
    printf "  %-14s ✓ %s\n" "$cli" "$asset"
  elif ! command -v "$cli" >/dev/null 2>&1 && [ ! -d "$dir" ]; then
    printf "  %-14s 跳过（未安装）\n" "$cli"
  fi
done <<< "$HOSTS"
if [ "$HOST_COUNT" -eq 0 ]; then
  echo "! 没检测到已安装的宿主 CLI 或 skills 目录；canonical 已保存在 ${TARGET}，可稍后重跑安装器。"
fi
if [ -e "$PROMPT" ] && [ "$SCOPE" = user ]; then echo "  ✓ /adhd-md"; fi

finalize_transaction

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
