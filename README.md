# adhd-md

把 Markdown 改造成 ADHD 友好的样子：结论前置、段落切碎、动作明确。**只重排信息，绝不删信息。**

同一份 skill 在 Claude Code、Codex、Grok Build、Gemini CLI、Cursor、opencode 里都能用。

[看官网的 before/after 对照](https://tsonglew.github.io/adhd-md/)

- [能干什么](#能干什么)
- [装 + 跑（约 2 分钟）](#装--跑约-2-分钟)
- [两个参数](#两个参数)
- [无损保证](#无损保证)
- [支持哪些 agent](#支持哪些-agent)
- [目录结构](#目录结构)
- [CLI](#cli)
- [出错了看这里](#出错了看这里)
- [深入](#深入)
- [License](#license)

## 能干什么

- **审计**：给文档打分（0–100，七个维度），逐条指出问题与行号
- **只改格式**：正文一个词都不动，只重排结构。改动可被脚本证明无损
- **只改内容**：只改措辞，不动排版风格
- **两者兼改**：默认档
- **去 AI 味**：翻案腔、抬价式冒号、洞察路标、黑话、破折号密度，逐条报位置
- **确定性修复**：中英文间距、中文标点、序号、空行、代码块语言标签，脚本直接修，不用模型

## 装 + 跑（约 2 分钟）

三种装法，任选一种：

```bash
# 有 Node —— 不留任何文件在当前目录
npx github:tsonglew/adhd-md

# 没 Node
curl -fsSL https://tsonglew.github.io/adhd-md/install.sh | bash

# 想改源码
git clone https://github.com/tsonglew/adhd-md && cd adhd-md && bash scripts/install.sh
```

安装脚本会探测本机装了哪些 agent，只往存在的宿主里放软链。canonical skill 落在 `~/.agents/skills/adhd-md`，改一处六个宿主同时生效。

从 git 克隆装是软链，`git pull` 即更新；npx 与 curl 装是复制，重跑一次即更新。

跑一下试试：

```bash
npx github:tsonglew/adhd-md audit 你的文档.md
```

或者在任意 agent 里直接说人话：

> 把 README.md 改成 ADHD 友好的，只改格式

## 两个参数

| scope | 边界 | 怎么说 |
|---|---|---|
| `format` | 正文词序列逐字不变，只动标记、空白、块顺序 | 只改格式 / 别动我的字 |
| `content` | 只改措辞与信息组织，不碰排版风格 | 只改内容 / 句子太长 |
| `both`（默认） | 全都改 | 优化一下 |

| level | 适用 | 力度 |
|---|---|---|
| `light` | 规范、合同、API 文档 | 只做零风险项 |
| `standard`（默认） | README、教程、设计文档 | 拆段、列表化、改标题、写 TL;DR |
| `deep` | 会议记录、长文、乱笔记 | 全量重构骨架 |

## 无损保证

`scope=format` 下的改动可以证明无损。剥掉标记后的正文 token 多重集必须完全一致，删一个词或新写一个词都会被 `verify` 拒绝。

```bash
python3 skill/scripts/adhd_md.py verify 原文.md 新文.md --scope=format
# scope=format → 通过
```

`scope=content` 下检查不变量：代码块逐字、行内代码、URL、标识符、数字带单位，缺一即硬失败。

篇幅太长就折叠或移到附录，不删。

## 支持哪些 agent

六个宿主都原生支持同一套 `SKILL.md` 目录格式（2026-08-13 本机实证，见 [宿主兼容矩阵](docs/host-matrix.md)）。

| 宿主 | 用户级目录 |
|---|---|
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.codex/skills/` + `/adhd-md` 斜杠命令 |
| Grok Build | `~/.grok/skills/`（也读 `~/.claude/skills/`） |
| Gemini CLI | `~/.gemini/skills/` |
| Cursor | `~/.cursor/skills/` |
| opencode | `~/.config/opencode/skills/` |

装到当前仓库而不是用户目录：

```bash
bash scripts/install.sh --project
```

没有命令执行能力的环境（网页版 LLM）粘贴自包含单文件：`dist/adhd-md.standalone.md`。

## 目录结构

```text
skill/                    唯一真源
  SKILL.md                主流程
  references/             规则库、评分、中文专项、反模式、文档骨架、示例语料
  scripts/adhd_md.py      确定性工具层，纯标准库，零依赖
dist/                     自包含单文件版（由脚本生成，勿手改）
site/                     官网，GitHub Actions 部署到 Pages
  og.html favicon.svg     预览图与图标的源模板（位图产物由 scripts/build-og.sh 渲染）
docs/host-matrix.md       六个宿主的实证结论
scripts/install.sh        探测 + 安装
```

## CLI

有 Node 的话不用装，`npx` 直接跑：

```bash
npx github:tsonglew/adhd-md audit 文档.md
```

装过之后也可以直接调脚本：

```bash
adhd_md.py audit FILE [--json] [--min-score N] [--level 1|2|3]
adhd_md.py fmt FILE [--write] [--check] [--toc] [--strip-emoji]
adhd_md.py verify OLD NEW --scope=format|content|both
adhd_md.py report OLD NEW --scope=...
adhd_md.py init --type=readme|tutorial|reference|adr|runbook|notes
adhd_md.py selftest
```

接 CI：

```bash
python3 skill/scripts/adhd_md.py fmt --check docs/*.md
python3 skill/scripts/adhd_md.py audit --min-score 70 docs/*.md
```

## 出错了看这里

| 症状 | 原因与解法 |
|---|---|
| 分数很高但文档明显很烂 | `audit` 输出的是脚本分，把 33 条需模型判断的规则按满分计入。脚本分低说明一定有问题，脚本分高不说明没问题 |
| `verify --scope=format` 失败 | 改动越界了。`prose_tokens_added` 是新写了措辞，`prose_tokens_missing` 是删了词。回退，或改用 `scope=content` |
| agent 没自动触发 | Codex 用 `/adhd-md`，其他宿主明确说「用 adhd-md skill」 |
| 想卸载 | `npx github:tsonglew/adhd-md install --uninstall`，或 `bash scripts/install.sh --uninstall` |

## 深入

- [规则库](skill/references/rules.md)：71 条规则，带轴/档/阈值。去 AI 味的 M 组十条也在里面，每条写明它是哪一种阅读成本
- [反模式](skill/references/antipatterns.md)：八种优化过头，附自检清单
- [示例语料](skill/references/examples/README.md)：4 组 before/after，含「故意没改什么」
- [评分细则](skill/references/rubric.md)
- [中文专项](skill/references/cjk.md)

## License

MIT
