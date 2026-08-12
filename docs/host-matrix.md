# 宿主兼容矩阵（P0 实证结论）

本机 2026-08-13 实测，非文档推测。探测方法附在末尾，可复现。

## 一句话结论

六个宿主**全部**支持同一套 `SKILL.md` 目录格式。因此 adhd-md 只需维护一份 skill，用软链分发；不需要为每个宿主写不同的适配器。

## 矩阵

| 宿主 | 用户级 skills 目录 | 项目级 | 实测状态 |
|---|---|---|---|
| Claude Code | `~/.claude/skills/<name>/SKILL.md` | `.claude/skills/` | 已实测：86 个 skill，其中 23 个是指向 `~/.agents/skills/` 的软链 |
| Codex | `~/.codex/skills/<name>/SKILL.md` | 未实测 | 已实测：目录存在，含软链与实体目录混合；另有 `~/.codex/prompts/*.md` 提供斜杠命令，`~/.codex/AGENTS.md` 提供全局指令 |
| Grok Build | `~/.grok/skills/<name>/SKILL.md` | `.grok/skills/` | 已实测（二进制内字符串）：**还会读 `~/.claude/skills/` 与 `.claude/skills/`**，原文 `Loaded as skills (same as .grok/skills/)`；`.cursor/skills/` 在 cursor 兼容开启时也读 |
| Gemini CLI | `~/.gemini/skills/<name>/SKILL.md` | 未实测 | 已实测：3 个 skill，全部是指向 `~/.agents/skills/` 的软链 |
| Cursor | `~/.cursor/skills/<name>/SKILL.md` | `.cursor/skills/`（据 Grok 兼容表） | 已实测：4 个，软链 + 实体目录混合 |
| opencode | `~/.config/opencode/skills/<name>/SKILL.md` | 未实测 | 已实测：3 个，全部软链到 `~/.agents/skills/` |

未实测项在 P5 安装脚本里按「目录存在则装」处理，不写死假设。

## 关键发现

### 1. `~/.agents/skills/` 是事实上的共享真源

本机 19 个 skill 存在这里，各宿主目录里放相对软链：

```text
~/.gemini/skills/find-skills -> ../../.agents/skills/find-skills
~/.config/opencode/skills/find-skills -> ../../../.agents/skills/find-skills
~/.claude/skills/agent-development -> ../../.agents/skills/agent-development
```

adhd-md 直接沿用这个约定：装到 `~/.agents/skills/adhd-md/`，再往六个宿主目录各放一条软链。改一处，六个宿主同时生效。

### 2. frontmatter 最小公倍数只有两个字段

跨宿主共用的 skill（如 `find-skills`）frontmatter 只写：

```yaml
---
name: find-skills
description: ...（含触发场景描述）
---
```

**结论**：canonical `SKILL.md` 只用 `name` + `description`。`allowed-tools` 这类 Claude 专有字段不进主文件，避免其他宿主解析报错。

### 3. Grok 读 Claude 目录 → 项目级安装成本减半

仓库内装一份 `.claude/skills/adhd-md/`，Claude Code 和 Grok Build 同时可用。项目级安装因此只需覆盖 4 个目录：`.claude/`、`.grok/`、`.cursor/`、`.codex/`。

### 4. 能力分档仍然需要

| 档 | 宿主 | 差异 |
|---|---|---|
| A | 全部六个 CLI | 有 shell + 能读相对路径 references → 完整体验，含确定性校验 |
| C | 网页版 LLM、无工具环境 | 需要自包含单文件 `dist/adhd-md.standalone.md`，纯 prompt 降级，报告里必须声明「未做机器校验」 |

原计划的 Tier B（单文件薄壳指向安装路径）**取消** —— 实测所有 CLI 都能吃目录格式，不需要这一层。

### 5. Codex 额外提供斜杠命令入口

`~/.codex/prompts/*.md` 是 `description` + `argument-hint` frontmatter 的单文件格式，会注册成斜杠命令。这是 skill 之外的**显式调用**通道，值得额外生成一个薄壳，解决「模型没自动触发」的场景。

## 探测方法（可复现）

```bash
# 1. 哪些宿主已安装
for c in codex grok gemini cursor-agent opencode claude; do
  printf "%-12s %s\n" "$c" "$(command -v $c || echo '—')"
done

# 2. 各宿主 skills 目录与软链关系（find 默认不跟软链，必须加 -L）
for d in ~/.claude/skills ~/.codex/skills ~/.grok/skills \
         ~/.gemini/skills ~/.cursor/skills ~/.config/opencode/skills; do
  echo "### $d"
  ls -la "$d" 2>/dev/null | head -5
  echo "  SKILL.md=$(find -L "$d" -maxdepth 2 -name SKILL.md 2>/dev/null | wc -l)"
done

# 3. 原生二进制的 skill 支持（Grok 是 Mach-O，路径约定藏在字符串里）
strings ~/.grok/bin/grok | grep -iE 'skills?/|SKILL\.md' | sort -u
```

第 2 步的 `-L` 是坑：不加会漏掉全部软链装的 skill，误判成「该宿主不支持」。
