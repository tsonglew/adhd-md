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
- [校验边界](#校验边界)
- [支持哪些 agent](#支持哪些-agent)
- [目录结构](#目录结构)
- [CLI](#cli)
- [出错了看这里](#出错了看这里)
- [深入](#深入)
- [License](#license)

## 能干什么

- **审计**：给文档打分（0–100，七个维度），逐条指出问题与行号
- **只改格式**：目标是保留正文用词，只调整标记、空白和块顺序；当前校验边界见下文
- **只改内容**：只改措辞，不动排版风格
- **两者兼改**：默认档
- **去 AI 味**：翻案腔、预告式冒号、装深刻的话、黑话、破折号密度，逐条报位置
- **确定性修复**：中英文间距、中文标点、序号、空行、代码块语言标签，脚本直接修，不用模型

阅读已有资料：

- **对话陪读**：一次读一小段，解释重点与术语，可以回看、跳过、暂停和用书签续读
- **离线阅读页**：把已有 Markdown、文本、网页或 PDF 生成 HTML，逐段阅读、调字号行距、保存进度，原文件保持不变
- **书签互通**：阅读页和有命令执行能力的 agent 共用 JSON 书签，带走待读位置、跳过范围和待澄清问题
- **自动提取**：网页链接、本地 HTML 和 PDF 可直接读取；扫描页可用本机 OCR，并保留来源与页码

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

项目级安装会把可运行的 canonical 副本放进仓库 `.agents/skills/adhd-md`，再复制到受支持的宿主目录。它不依赖 npx 缓存或 curl 下载目录；升级时在同一仓库重新运行 `bash scripts/install.sh --project`。

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

支持本地 Markdown、纯文本或粘贴内容。网页链接、本地 HTML 和 PDF 可自动提取；有命令执行能力的 agent 可以直接运行生成器。

无法访问或识别的部分会明确标出。

想自己专注阅读，运行下面任一命令（需要 Python 3；第一种另需 Node）：

```bash
npx github:tsonglew/adhd-md read 文档.md
python3 skill/scripts/adhd_md.py read 文档.md
```

命令生成 `文档.reader.html`，用浏览器打开即可。页面支持逐段切换、回看全文、调整字号与行距，并在浏览器允许时保存本地进度。

加上 `--open`，生成成功后尝试直接打开阅读页：

```bash
python3 skill/scripts/adhd_md.py read 文档.md --open
```

打开失败会提示手动打开，已生成的文件仍保留。生成失败时不会打开浏览器。

### 在阅读页和对话之间继续

阅读页分别记住「当前查看」和「下次继续」的位置。回看前文后可回到待读处；跳过的内容单独保留，展示过也不代表已经读懂。

从阅读页转到对话时，优先点击「下载续读正文」，再复制或下载 JSON 书签，把两者交给 agent。续读正文与书签对应的文本逐字一致；未改动的本地原文也可以直接使用。

网页和 PDF 请一并保留原阅读页，方便核对来源、页码和提取缺口。「下载提取文本」会附加来源说明，不能直接替代续读正文；重新抓取网页也可能取得不同内容。

agent 用分段数据核对书签，把示例中的 `文档.md` 换成下载的续读正文文件：

```bash
python3 skill/scripts/adhd_md.py read 文档.md --session bookmark.json --json
```

对话结束后，把更新的 JSON 书签粘贴或导入阅读页。也可以生成带书签的新阅读页：

```bash
python3 skill/scripts/adhd_md.py read 文档.md --session bookmark.json --open -o /tmp/继续阅读.reader.html
```

书签含短原文锚点和用户记录的问题，不含完整原文；继续阅读仍需取得原文。

这是手动导入导出，不会自动跨设备同步。浏览器无法保存进度时会提示，可导出书签留存。

原文内容不同、书签格式不合法或锚点不匹配时，导入会被拒绝，原书签保留。同一份原文换片段大小仍可恢复；原文变了需按锚点人工核对后创建新会话，旧覆盖范围不能直接继承。

没有命令执行能力的 agent 仍可使用纯文本书签。旧文本书签交给 agent 核对位置，阅读页不能直接导入。

### 直接读取网页和 PDF

网址、HTML 和 PDF 使用同一入口：

```bash
python3 skill/scripts/adhd_md.py read "https://example.com/article" -o /tmp/article.reader.html
python3 skill/scripts/adhd_md.py read 文档.pdf
python3 skill/scripts/adhd_md.py read 保存的网页.html
```

想单独保存提取稿，再交给 agent 陪读：

```bash
python3 skill/scripts/adhd_md.py extract 文档.pdf
```

会生成 `文档.extracted.md`，保留来源和 PDF 页码。网页正文优先，其余可见文字放附录；依赖 JavaScript 或登录的页面需要宿主读取工具或导出正文。

生成器不上传原文、不调用模型；输入网址时会请求该地址。生成文件包含文本和来源信息，网页阅读页还保留取得的 HTML 源码，分享时请按原文的分享范围处理。

### 准备 PDF 与 OCR 工具

PDF 需要 Poppler；扫描页另需 Tesseract 与对应语言包。安装一次即可：

```bash
# macOS（Homebrew）
brew install poppler tesseract tesseract-lang

# Ubuntu / Debian
sudo apt install poppler-utils tesseract-ocr tesseract-ocr-chi-sim
```

默认对没有可读文本的 PDF 页尝试 OCR。可用 `--ocr never` 只读文本层，或 `--ocr always --ocr-lang chi_sim+eng` 对每页做中英文 OCR；已有文本层也会保留。

依赖缺失会给出安装提示，不自行安装。

提取稿保留页码、来源和缺口说明。图片、公式、表格和 OCR 结果仍需回看原 PDF 核对，文本提取不等同于 PDF 视觉内容的无损转换。

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
| `format` | 不改措辞；标题、代码、链接目标和 frontmatter 受保护。无法确认时返回 `unknown` | 只改格式 / 别动我的字 |
| `content` | 只改措辞与信息组织，不碰排版风格 | 只改内容 / 句子太长 |
| `both`（默认） | 全都改；校验范围与 `content` 相同 | 优化一下 |

| level | 适用 | 力度 |
|---|---|---|
| `light` | 规范、合同、API 文档 | 只做少量调整，并检查差异 |
| `standard`（默认） | README、教程、设计文档 | 拆段、列表化、改标题、写 TL;DR、给时间预估 |
| `deep` | 会议记录、长文、乱笔记 | 全量重构骨架 |

## 校验边界

### 支持的语法与变换边界

校验器实现的是 Markdown 子集，不是完整 CommonMark / GFM 解析器。遇到不能可靠解释的结构，结果为 `unknown`，并报告来源行；`fmt --write` 会拒绝写回。先保留原结构，改用人工复核，不要把 `unknown` 当通过。

| 结构 | 当前处理 | 写回约定 |
|---|---|---|
| 标题、段落、基础列表、引用块、简单 GFM 表格 | 参与正文 token 检查 | token 数变化失败；词序变化无法判断 |
| 成对围栏代码（反引号或波浪线） | 按正文逐字比较原有代码块及重复次数 | 不比较围栏样式、语言标签和位置；`format` 拒绝新增代码块，`content` / `both` 可添加；未闭合围栏为 `unknown` |
| 四空格缩进代码、复杂嵌套块 | 解析器不能稳定地区分代码与续行 | 有改动时为 `unknown`，保留原样 |
| 行内 Markdown 链接、图片与 HTTP(S) autolinks | 比较目标地址及重复次数 | 删除或改写原目标为硬失败；content / both 可添加目标；裸 URL 包成链接可通过 |
| 行内字面值、选项、相对路径、权限和技术标识符 | 按类型比较完整值与重复次数 | 更长字符串不能冒充旧值；通用缩写只要求至少保留一次 |
| 数字与单位 | 允许数字和单位之间的空白变化 | format 改数值或单位为硬失败；content / both 给警告并返回 `unknown` |
| 引用式链接、原始 HTML（含 `<details>`） | 不解释引用定义、显示和结构 | 有改动时为 `unknown`；唯一原 H2 被原样用作 `<summary>` 时允许标准折叠外壳 |
| YAML frontmatter（首行 `---` 且有闭合行） | format 模式逐字保护 | format 改动失败；content / both 可改，但会给出元数据复核警告 |
| HTML 注释、扩展 Markdown / MDX | 不在支持范围 | 有改动时为 `unknown`，保留原样 |

`scope=format` 允许在已有句界拆段、复用原词列表化、调整标题标记、加行内代码或强调、生成目录、折叠原有标题、移动整块，以及修空格和标点。它不允许改词、删内容、改数字或链接目标。未改写且能唯一映射的完整块重排可以通过，同时给出指代复核提示；句内换序、顺序敏感列表变化或重复块映射歧义返回 `unknown`。拆句时不能拆开条件、否定和适用对象。

`content` 与 `both` 可修改措辞和结构，但所有 scope 都保留原有代码块正文与重复次数、链接目标与重复次数，以及行内代码值、命令选项、常见相对路径、权限值和大小写敏感技术标识符。裸 URL 包成链接仍可通过；content / both 可以增加新代码块或链接，format 不可以。`format` 的 frontmatter 必须原样保留；`content` / `both` 改元数据时会报告新旧内容并要求复核。

校验有三种结果：`pass` 表示已声明的机器检查通过且没有待复核警告；`fail` 表示发现硬约束变化；`unknown` 表示当前解析器不能可靠判断，或有警告尚待人工复核。CLI 对应退出码为 `0`、`3`、`4`。JSON 保留原有 `scope`、`hard_failures`、`warnings`、`ok` 字段，新增 `status` 与 `unknowns`；确认完整块重排时附带 `notes` 指代复核提示。`ok` 仅在 `status=pass` 时为 `true`，因此旧调用方不会把未知当成功。警告不会变成硬失败，但会阻止报告为 `pass`。

```bash
python3 skill/scripts/adhd_md.py verify 原文.md 新文.md --scope=format
# scope=format → 通过 / 失败 / 无法判断
```

选项、路径、权限和技术标识符按完整值及重复次数比较，不会把 `--timeoutExtra` 当成 `--timeout`；通用缩写（如 API、CLI、URL、HTTP、HTML、JSON、PDF、ID）只要求至少保留一次。数字与单位之间的空白可归一（`2 MB` 与 `2MB`），数值或单位变化在 `format` 下失败，在 `content` / `both` 下产生警告并返回 `unknown`。校验器仍不证明语义等价，也无法识别所有句内条件关系；`pass` 只说明已声明的机器检查通过。

运行 `fmt 文件.md` 先查看格式化预览。`fmt --write` 在替换前运行 format 校验；硬失败或 `unknown` 都拒绝写回。它通过同目录临时文件原子替换，保留 UTF-8 字节内容、换行、POSIX mode 位和所有者 / 组；符号链接、硬链接会拒绝，系统 ACL、扩展属性和文件 flags 不保留。并发编辑或写入失败时原文件不变、临时文件清理。多文件逐个提交，失败可能出现部分成功，并逐文件报告。`--strip-emoji` 会跳过 format 校验，是显式有损选项，会单独标示，但仍使用原子写入流程。保留原文，并人工核对校验范围外的代码细节、句内语义和指代关系。

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

卸载只删除能确认归属的安装资产。用户级宿主仅移除指向 canonical skill 的软链；项目级 canonical、副本和用户级 canonical 目录都需要安装器写入的所有权标记。旧版或不完整安装若没有标记会被保留并提示检查；`--project --uninstall` 不会处理用户级 Codex prompt。

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
CHANGELOG.md               未发布改动与调用方迁移说明
scripts/install.sh        探测 + 安装
```

Python 模块只依赖标准库。`skill/scripts/` 中还包含提取与阅读模块；PDF / OCR 功能调用本机的 Poppler 与 Tesseract 工具。

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

独立提取正文：

```bash
adhd_md.py extract SOURCE [-o OUTPUT] [--json]
```

`read --json` 只输出分段和来源定位数据，供 agent 使用，不生成 HTML。`extract --json` 输出提取文本与来源元数据。

`read --json` 还提供初始阅读会话、各片段的 UTF-16 偏移和位置锚点；agent 必须使用返回值维护书签，不能猜哈希或偏移。传入 `--session bookmark.json` 时，先核对书签并输出规范化后的会话。

`read` 支持 `--session bookmark.json` 恢复 JSON 书签，以及 `--open` 在生成成功后尝试打开阅读页。`--open` 不能与 `--json` 同用。

`read` 的 `FILE` 和 `extract` 的 `SOURCE` 均支持 UTF-8 Markdown / 文本、本地 HTML、PDF 和 HTTP(S) 网页或 PDF 链接。两个命令都支持 `--timeout 20`、`--ocr auto|never|always` 和 `--ocr-lang chi_sim+eng`。

`--timeout` 限制网页请求整体时间，以及每次 PDF / OCR 外部工具调用时间；本地 HTML、Markdown 分段和阅读页渲染不受它控制。网页下载最多 20 MiB；本地文件、PDF 和标准输入最多 50 MiB，PDF 另限 500 页。超限会报错，不会截短输入。

`extract` 默认输出 `<原名>.extracted.md`；网址输出由标题或来源命名，保存在当前目录。

输入 `-` 可从标准输入读取，默认生成 `stdin.reader.html`。`--json` 不能与 `-o` 同用。

接 CI：

```bash
python3 skill/scripts/adhd_md.py fmt --check docs/*.md
python3 skill/scripts/adhd_md.py audit --min-score 70 docs/*.md
```

## 出错了看这里

| 症状 | 原因与解法 |
|---|---|
| 分数很高但文档明显很烂 | `audit` 输出的是脚本分。默认 standard + both 有 23 条规则需模型判断、7 条仅提示；未判断不代表通过 |
| `verify --scope=format` 失败 | 改动越界了。`prose_tokens_added` 是新写了措辞，`prose_tokens_missing` 是删了词。回退，或改用 `scope=content` |
| agent 没自动触发 | Codex 用 `/adhd-md`，其他宿主明确说「用 adhd-md skill」 |
| PDF 提示缺少工具 | 安装 Poppler；扫描件还需 Tesseract 和对应语言包。只读取文字层时可用 `--ocr never`，未识别页仍会标出 |
| 网页只读到登录或加载提示 | 自动提取不执行网页 JavaScript，也不读取浏览器登录态；用宿主浏览器取得正文，或导出 HTML / 文本 |
| JSON 书签导入失败 | 核对原文版本与书签格式；内容或锚点不匹配时保留旧书签，人工核对后创建新会话 |
| 阅读页提示无法保存进度 | 浏览器本地存储不可用；导出 JSON 书签，稍后手动导入 |
| `read --open` 没有打开浏览器 | 若文件已生成，按命令输出路径手动打开；打开失败不会删除文件 |
| 想卸载 | `npx github:tsonglew/adhd-md install --uninstall`，或 `bash scripts/install.sh --uninstall` |

## 开发官网

```bash
cd site && npm install
npm run dev      # 本地预览（中文在 /，英文在 /en/）
npm run build    # 构建到 site/dist/，Pages workflow 部署的就是它
```

站点文案在 `site/src/i18n/ui.ts`，中英两套。加第三种语言就是加一个字典对象 + 一个 `src/pages/<lang>/index.astro`。

改 `og.html` 或 `icon-square.svg` 之后重跑 `bash scripts/build-og.sh`，位图产物写进 `site/public/`。需要本机 Chrome/Chromium；脚本会从 PATH 和常见应用目录发现，也可以用 `OG_CHROME=/path/to/chrome` 或 `--chrome /path/to/chrome` 指定。模板请求 Google Fonts，离线时使用系统后备字体，细节可能因运行环境不同。

## 深入

[陪读与离线阅读页](skill/references/reading.md) 介绍来源范围、分段讲解、跳过与续读书签。

- [规则库](skill/references/rules.md)：86 条定义（78 条正文规则 + 8 条反模式），带轴/档/阈值与实现状态。去 AI 味的 M 组十四条也在里面，每条写明它是哪一种阅读成本
- [规则证据库](skill/references/evidence.md)：每条规则对应的 ADHD 机制、产品模式与文献出处
- [调研与依据](docs/adhd-research.md)：市面 ADHD 友好产品扫描 + 相关研究综述 + 采纳/不采纳清单
- [反模式](skill/references/antipatterns.md)：八种优化过头，附自检清单
- [示例语料](skill/references/examples/README.md)：4 组 before/after，含「故意没改什么」
- [评分细则](skill/references/rubric.md)
- [中文专项](skill/references/cjk.md)

## License

MIT
