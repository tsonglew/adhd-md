# adhd-md

把 Markdown 改造成 ADHD 友好的样子：结论前置、段落切碎、动作明确。**只重排信息，绝不删信息。**

也能保留已有文档，在 AI 对话里逐段陪读，或生成离线专注阅读页。

同一份 skill 在 Claude Code、Codex、Grok Build、Gemini CLI、Cursor、opencode 里都能用。

<img width="962" height="741" alt="image" src="https://github.com/user-attachments/assets/da16f89a-f732-471c-9bfc-509714e05a66" />

[看官网的 before/after 对照](https://tsonglew.github.io/adhd-md/)

- [能干什么](#能干什么)
- [装 + 跑（约 2 分钟）](#装--跑约-2-分钟)
- [阅读已有文档](#阅读已有文档)
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
- **去 AI 味**：翻案腔、预告式冒号、装深刻的话、黑话、破折号密度，逐条报位置
- **确定性修复**：中英文间距、中文标点、序号、空行、代码块语言标签，脚本直接修，不用模型

阅读已有资料：

- **对话陪读**：一次读一小段，解释重点与术语，可以回看、跳过、暂停和用书签续读
- **离线阅读页**：把已有 Markdown / 文本生成 HTML，逐段阅读、调字号行距、保存进度，原文保持不变

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

## 阅读已有文档

想有人带着读，在装好 skill 的 agent 里说：

> 用 adhd-md 陪我读这份文档，一次一小段，先别修改它。

agent 会保留原文，指出当前读到的位置，再讲解这一段。可以随时说「继续」「解释一下」「回到上一段」「跳过」或「暂停」。

暂停时会给书签，下次贴回书签即可续读；跳过的内容会留在待读清单里。对话陪读不需要命令执行能力。

支持本地 Markdown、纯文本或粘贴内容。网页和 PDF 需要宿主先取得可读文本；无法访问或识别的部分会明确标出。

想自己专注阅读，运行下面任一命令（需要 Python 3；第一种另需 Node）：

```bash
npx github:tsonglew/adhd-md read 文档.md
python3 skill/scripts/adhd_md.py read 文档.md
```

命令生成 `文档.reader.html`，用浏览器打开即可。页面支持逐段切换、回看完整原文、调整字号与行距，并在浏览器允许时保存本地进度。

生成器不上传原文、不调用模型；生成文件包含原文，分享时请按原文的分享范围处理。

自定义片段大小和输出位置：

```bash
python3 skill/scripts/adhd_md.py read 文档.txt --chunk-size 900 -o /tmp/文档.reader.html
```

`--chunk-size` 是目标字符数，代码块或表格可能超过目标。输出路径已存在时拒绝覆盖，换一个新路径即可。需要 AI 解释时继续在 agent 中陪读，也可以直接说「生成阅读页，再陪我读第一段」。

完整行为与书签格式见 [陪读与离线阅读页](skill/references/reading.md)。

## 两个参数

下面的 `scope`、`level` 用于改写文档。陪读使用 `mode=read`，保留原文件；原有改写功能使用 `mode=edit`。

| scope | 边界 | 怎么说 |
|---|---|---|
| `format` | 正文词序列逐字不变，只动标记、空白、块顺序 | 只改格式 / 别动我的字 |
| `content` | 只改措辞与信息组织，不碰排版风格 | 只改内容 / 句子太长 |
| `both`（默认） | 全都改 | 优化一下 |

| level | 适用 | 力度 |
|---|---|---|
| `light` | 规范、合同、API 文档 | 只做零风险项 |
| `standard`（默认） | README、教程、设计文档 | 拆段、列表化、改标题、写 TL;DR、给时间预估 |
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
  references/             规则库、评分、中文专项、反模式、文档骨架、示例语料、证据库
  scripts/adhd_md.py      确定性工具层，纯标准库，零依赖
dist/                     自包含单文件版（由脚本生成，勿手改）
site/                     官网，Astro 构建，GitHub Actions 部署到 Pages
  src/components/          七个区块组件
  src/layouts/             页头 / 页脚 / 元信息
  public/                  图标与预览图位图产物
  og.html icon-square.svg  预览图与图标的源模板（位图产物由 scripts/build-og.sh 渲染）
docs/
  eval.md                  验证结论
  host-matrix.md           六个宿主的实证结论
  adhd-research.md         产品与研究的调研快照
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

阅读页命令：

```bash
adhd_md.py read FILE [-o OUTPUT] [--chunk-size 900] [--json]
```

`read --json` 只输出分段和来源定位数据，供 agent 使用，不生成 HTML。`read` 接收 UTF-8 Markdown / 文本；网页和 PDF 先通过宿主工具提取文本。

输入 `-` 可从标准输入读取，默认生成 `stdin.reader.html`。`--json` 不能与 `-o` 同用。

接 CI：

```bash
python3 skill/scripts/adhd_md.py fmt --check docs/*.md
python3 skill/scripts/adhd_md.py audit --min-score 70 docs/*.md
```

## 出错了看这里

| 症状 | 原因与解法 |
|---|---|
| 分数很高但文档明显很烂 | `audit` 输出的是脚本分，把 37 条需模型判断的规则按满分计入。脚本分低说明一定有问题，脚本分高不说明没问题 |
| `verify --scope=format` 失败 | 改动越界了。`prose_tokens_added` 是新写了措辞，`prose_tokens_missing` 是删了词。回退，或改用 `scope=content` |
| agent 没自动触发 | Codex 用 `/adhd-md`，其他宿主明确说「用 adhd-md skill」 |
| 想卸载 | `npx github:tsonglew/adhd-md install --uninstall`，或 `bash scripts/install.sh --uninstall` |

## 开发官网

```bash
cd site && npm install
npm run dev      # 本地预览（中文在 /，英文在 /en/）
npm run build    # 构建到 site/dist/，Pages workflow 部署的就是它
```

站点文案在 `site/src/i18n/ui.ts`，中英两套。加第三种语言就是加一个字典对象 + 一个 `src/pages/<lang>/index.astro`。

改 `og.html` 或 `icon-square.svg` 之后重跑 `bash scripts/build-og.sh`，位图产物写进 `site/public/`。

## 深入

[陪读与离线阅读页](skill/references/reading.md) 介绍来源范围、分段讲解、跳过与续读书签。

- [规则库](skill/references/rules.md)：78 条规则，带轴/档/阈值。去 AI 味的 M 组十四条也在里面，每条写明它是哪一种阅读成本
- [规则证据库](skill/references/evidence.md)：每条规则对应的 ADHD 机制、产品模式与文献出处
- [调研与依据](docs/adhd-research.md)：市面 ADHD 友好产品扫描 + 相关研究综述 + 采纳/不采纳清单
- [反模式](skill/references/antipatterns.md)：八种优化过头，附自检清单
- [示例语料](skill/references/examples/README.md)：4 组 before/after，含「故意没改什么」
- [评分细则](skill/references/rubric.md)
- [中文专项](skill/references/cjk.md)

## License

MIT
