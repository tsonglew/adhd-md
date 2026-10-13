# adhd-md 改进执行清单

先完成 M0，再按依赖处理 M1。共 22 项任务，每项都列出修改范围、操作和验收。阶段安排及工期见 [路线图](../ROADMAP.md)。

基线为 2026-10-13 的 `3c8b1fb`。清单已开始执行；空复选框表示尚未验收，勾选项附有本机验证证据。基线的 155 项测试通过不代表当时的问题已修复。

- [执行和关闭规则](#执行和关闭规则)
- [M0 建立检查和边界](#m0-建立检查和边界)
- [M1 保护原文和安装范围](#m1-保护原文和安装范围)
- [M2 修复提取和阅读](#m2-修复提取和阅读)
- [M3 完善分发和官网](#m3-完善分发和官网)
- [M4 统一规则和评分](#m4-统一规则和评分)
- [M5 建立评测和发布记录](#m5-建立评测和发布记录)
- [检查入口](#检查入口)
- [交付记录模板](#交付记录模板)

## 执行和关闭规则

P1 表示优先处理的信息破坏、误放行或操作越界；P2 表示正确性、可靠性和覆盖缺口；P3 表示构建维护与效果评估。

每项认领时填写负责人和关联 PR。任务操作逐条勾选；只有验收通过并填写证据后，才勾选该任务的关闭项。

测试应先证明修复前的失败，再证明修复后的预期行为。不要把当前实现的输出直接复制成预期值。未修复样例可以先作为独立复现保存，不能永久标为跳过后声称已覆盖。

安装测试使用可注入的测试目录根、命令桩和本地 tarball。写入与删除前确认目标在夹具目录内；测试不得操作真实用户的 skill、prompt 或项目。

新增测试放入现有测试体系或明确接入 CI。以下新文件路径均为规划建议，实施前检查是否已有合适入口。

## M0 建立检查和边界

### CI-01 建立隔离测试和 PR 检查

P1；无前置任务。新增 [独立 CI 工作流](../.github/workflows/ci.yml)，保留 Pages 工作流作为单独的部署流程，并建立安装夹具。

- [x] 建立临时用户根和项目根，并通过 `ADHD_MD_HOME` 注入用户级安装路径
- [x] 用受控 `git`、`rm`、`cat` 命令桩跑卸载回归；`rm` 桩拒绝操作临时根外的目标
- [x] 用六个宿主 CLI 命令桩验证安装探测，并用本地 tarball 模拟 curl 下载、解包、自检和复制安装
- [x] 配置 PR 和主分支运行 Python、CLI、安装器回归、单文件同步和官网构建
- [x] 在 GitHub 验证 PR 检查实际运行，并注入失败测试与生成产物漂移，确认变红且不触发部署
- [x] 增加并运行实际 npm tarball 清单与包内 CLI 冒烟检查
- [x] PR 工作流采用只读仓库权限；Pages 发布仍由独立工作流执行
- [x] 配置 Python 3.9 / 3.14 与 macOS / Linux 核心检查矩阵
- [x] 等托管矩阵通过后，再确认并记录 Python 支持范围
- [x] 配置 Node 18 CLI 检查和 Node 22.12.0 官网构建，直接测试站点声明的最低版本
- [x] 在 Ubuntu 检查 job 安装 Poppler、Tesseract 和简体中文模型，并运行真实 PDF/OCR 集成用例

验收时在临时分支制造一个失败测试和一次生成产物漂移，确认检查变红且不触发部署。不能把缺少 PDF/OCR 工具导致的跳过记为通过；至少一个 job 安装工具跑真实集成测试。

本机证据（2026-10-13）：`selftest` 通过（168 项）；完整 `unittest discover` 通过（172 项）；本地 tarball 安装只触发一次下载桩，真实解包、自检和六宿主探测均在临时根内完成；`build_standalone.py --check`、CLI 入口、`bash -n`、工作流 YAML 解析和官网构建通过。GitHub 实际运行与失败注入仍待验收。

补充本机证据（2026-10-13）：`bash scripts/check_npm_package.sh` 对当前源码执行 `npm pack`，核对包内必需文件并拒绝缓存 / 临时文件；从解包后的临时目录验证 CLI 版本、帮助和 `selftest`（190 项），通过，实际 tarball 共 36 个文件。仓库完整 `unittest discover`（201 项）、`build_standalone.py --check`、官网构建和 `git diff --check` 也通过。该结果验证本机包内容与 smoke test，不代替 GitHub Actions 托管运行及失败注入。

Node 边界说明：官网 GitHub Actions 已在 `22.12.0` 完成 `npm ci` 和 Astro 构建，Node CLI job 在 `18.20.8` 完成实际 tarball smoke。lockfile 中 `undici@8.10.0` 声明 Node `>=22.19.0`；当前证据证明锁定版本可完成站点构建，不扩大到未运行的 Node 运行时场景。

初始外部权限阻塞（2026-10-13，已解决）：`gh auth status` 最初显示本机令牌无效；连接器可读取 `tsonglew/adhd-md`，但创建 Git blob 返回 403 `Resource not accessible by integration`，当时没有创建分支、提交或 PR。用户完成本机设备登录后恢复了写权限，实际 PR 与托管验收记录见下。

权限恢复与托管验收（2026-10-13）：用户完成本机 `gh` 设备登录后，创建了 [草稿 PR #2](https://github.com/tsonglew/adhd-md/pull/2)。干净代码提交 `aa79c8d` 对应 GitHub Actions run `38398278808` 六个 job 全部通过：Python 3.9 / 3.14 × Ubuntu / macOS、Node CLI 和官网构建；Ubuntu Python 3.14 job 安装 Poppler、Tesseract 与 `chi_sim` 并通过真实 PDF/OCR 用例。实际解释器为 Python 3.9.25（Ubuntu）、3.9.13（macOS 26 arm64）、3.14.8（Ubuntu）和 3.14.7（macOS 26 arm64）；Node CLI 为 18.20.8，官网为 22.12.0。

失败注入分别运行，避免一个失败短路另一个门禁。Run `38398646992` 的临时失败测试被 Python selftest 和 Node tarball smoke 明确捕获为 `AssertionError: temporary CI failure injection`；run `38398894878` 的 standalone 漂移被四个 Python job 的 `build_standalone.py --check` 捕获，Node CLI 与官网 job 通过。两次注入分支上 `gh run list --workflow pages.yml --branch codex/adhd-md-reliability-m0-m5` 均无结果，Pages 工作流没有启动。临时提交已从分支移除，standalone 同步检查恢复通过。

跳过项记录：Python 3.9 / Ubuntu、Python 3.9 / macOS 和 Python 3.14 / macOS 三个 job 各跳过 3 个 `RealPopplerTest`，原因均为 `Poppler is optional; install it for the real PDF smoke test`；Python 3.14 / Ubuntu job 安装 Poppler、Tesseract 与 `chi_sim` 后 217 项全通过，没有跳过。

本机终检更新（2026-10-13）：`python3 skill/scripts/adhd_md.py selftest` 199 项通过，完整 unittest 217 项通过，规则生成器 unittest 4 项通过。重新生成并检查单文件版、`python3 scripts/build_rules.py --check`、官网构建和 `git diff --check` 均通过；npm tarball 共 37 个文件，包内 smoke 通过。以上为托管权限恢复前的本机证据；GitHub 结果随后补记。

M0 要求现有检查和隔离夹具可用。后续新增回归随各自任务接入，CI-01 不等待这些任务完成。

- [x] CI-01 已验收，PR 链接、环境、失败与恢复记录已填写

### SAFE-01 明确格式变换与校验边界

P1；可与 CI-01 并行。修改 [SKILL.md](../skill/SKILL.md)、[README](../README.md)、[阅读说明](../skill/references/reading.md) 和 [官网文案](../site/src/i18n/ui.ts)。

- [x] 列出支持的代码、列表、引用、表格、frontmatter、链接和折叠语法
- [x] 定义允许的拆段、列表化、整块移动、加反引号、目录和标题复用方式
- [x] 明确不支持结构的结果，保留原样或停止写回，并给出源位置
- [x] 区分检查通过、检查失败和无法可靠判断，未知结果不使用成功文案
- [x] 收窄现有无损表述，说明 token 计数、顺序、代码块、链接目标与语义复核的已知边界
- [x] 定义旧 JSON 与 CLI 调用的兼容策略，新增状态不会被旧调用方误判为成功
- [x] 同步中英文官网说明并重建单文件版，保留无 shell 时的人工流程

验收采用支持矩阵，每种语法至少有一组合法输入和一组越界输入。文档不能将词频一致表述为完整语义等价，也不能把 PDF 文本提取表述为视觉内容完整保留。

本机证据（2026-10-13）：`verify` 支持 `pass` / `fail` / `unknown`，JSON 保留旧字段且 `ok=false` 覆盖 unknown，CLI 返回 4 并显示“无法判断”；`fmt --write` 在 fail / unknown 时保留原文件。支持矩阵覆盖标题、段落、围栏代码、列表、引用、表格、frontmatter、链接、目录、折叠、缩进代码和引用链接的正反例。168 项自测、172 项完整测试、单文件同步检查与官网构建通过；README、SKILL、阅读说明、中英文站点文案已同步。

- [x] SAFE-01 已验收，支持矩阵和输出约定已填写

## M1 保护原文和安装范围

### FMT-01 保留代码与结构空白

P1；依赖 CI-01、SAFE-01。修改 [adhd_md.py](../skill/scripts/adhd_md.py) 的块解析、CJK 间距和标点处理。

- [x] 将空格修复限制在正文，保留行首缩进、列表续行和行尾双空格硬换行
- [x] 识别普通缩进代码，以及列表和引用内的 fenced code
- [x] 覆盖不同长度围栏、代码内较短围栏、未闭合围栏、制表符和 CRLF
- [x] 保护代码字符串、命令、路径、版本号和 URL 中的标点
- [x] 对无法可靠识别的区域保留原样，并给出可定位的说明
- [x] 为正文仍能修复、代码体逐字不变和第二次格式化无变化编写独立预期输出
- [x] 用 Python 语法解析与字符串值断言复核代码样例，开发测试可使用独立 Markdown 解析器核对结构

验收必须包含缩进式 `if True` 和含 `中文,示例` 的字符串。修复后嵌套关系、代码值和硬换行保留；不能只依赖 `verify(old, fmt(old))` 的布尔值。

本机证据（2026-10-13）：新增缩进式 `if True` 与 `"中文,示例"` 字符串用例，执行 AST 解析并断言字符串值；另验证列表续行、制表符代码、列表/引用内围栏、不同长度与未闭合围栏、硬换行双空格和 CRLF 字节写回。 `fmt(fmt(x)) == fmt(x)` 回归通过；完整 `selftest` 168 项、`unittest discover` 172 项通过。

- [x] FMT-01 已验收，预期文件和独立结构检查记录已填写

### VER-01 精确比较各类不变量

P1；依赖 SAFE-01、FMT-01。修改 [adhd_md.py](../skill/scripts/adhd_md.py) 的不变量提取、比较和报告。

- [x] 让三个 scope 共用代码、链接目标和受保护字面量的检查
- [x] 比较类型化值和出现次数，替换字符串包含判断
- [x] 在 format 模式保护 frontmatter；为 content 和 both 明确元数据变更政策
- [x] 列出数字和单位的合法归一化，声明为硬约束的变化必须失败
- [x] 保留新增反引号等合法格式包装，按原文来源识别内容身份
- [x] 覆盖域名替换、相对路径变化、`--timeout` 变为 `--timeoutExtra`、权限值变化和重复项遗漏
- [x] 确保报告区分硬失败与警告，并包含原值、新值或缺失位置

数字单位只忽略数字和支持单位之间的空白（如 `2 MB` / `2MB`）；单位别名不互换。`format` 的数字或单位变化硬失败，`content` / `both` 发出带新旧值的警告并返回 `unknown`。原有代码块正文、链接目标、行内代码值、选项、路径、权限和大小写敏感技术标识符按类型与次数检查；`content` / `both` 允许新增代码块和链接，不允许丢失原值。常见缩写只要求至少保留一次。

本机证据（2026-10-13）：对三个 scope 分别验证域名替换、`../config/app.yaml` 路径替换、`--timeout` → `--timeoutExtra`、权限值和 `maxEntries` 大小写变化均硬失败；重复代码块、行内字面值、链接目标和标识符遗漏按次数报告源行。新增反引号和把既有命令移入代码块的正例通过。`2 MB` / `2MB` 归一通过；`2 MB` / `2 GB` 在 format 下失败、在 content / both 下返回 unknown 并报告新旧值。metadata 在 format 下硬失败，在 content / both 下提示并返回 unknown。CLI 状态码 3 / 4 回归通过。`selftest` 174 项、`unittest discover` 178 项、`build_standalone.py --check` 和官网构建通过。

- [x] VER-01 已验收，不变量矩阵和 CLI 退出结果已填写

### VER-02 区分合法重排和句内改写

P1；依赖 SAFE-01、VER-01。修改 [adhd_md.py](../skill/scripts/adhd_md.py) 的 format 比较逻辑。

- [x] 建立有顺序的内容片段及来源映射，淘汰全文词频作为唯一判据
- [x] 允许既有整块移动，并支持认可边界上的拆段和列表化
- [x] 保持每个可映射片段内部词序，拒绝句内交换对象、条件和否定关系
- [x] TOC 只豁免与已有标题及锚点匹配的生成内容，折叠 summary 只复用有来源的标题
- [x] 拒绝利用伪目录、折叠或新增标记隐藏正文删改的情况
- [x] 覆盖重复段落、相似句子、多次出现的标题和顺序敏感列表，歧义时输出无法判断
- [x] 保留指代复核提示，合法块移动仍可能需要人工确认语义关联

验收包含 `允许甲，禁止乙。` 与 `禁止甲，允许乙。` 的反例。正例必须覆盖拆段、列表化、整块移动、加反引号、TOC 和折叠，不能通过禁止所有重排来绕过问题。

本机证据（2026-10-13）：整块标题与段落可唯一映射时重排通过，并在 CLI / report 输出指代复核提示；句内条件对象换序、顺序敏感列表重排、重复段落和重复标题映射歧义均返回 `unknown`。原顺序拆段/列表化、匹配现有标题的 TOC 和复用唯一原 H2 的 `<details>` 折叠通过；伪目录、重复 summary 和折叠内删正文不能通过。`selftest` 177 项、`unittest discover` 181 项、单文件同步检查、官网构建与 `git diff --check` 全部通过。

- [x] VER-02 已验收，正反例及歧义处理记录已填写

### FMT-02 在写回前执行保护检查

P1；依赖 FMT-01、VER-01、VER-02。修改 [adhd_md.py](../skill/scripts/adhd_md.py) 的 `fmt --write` 流程。

- [x] 在内存或临时文件生成结果，检查通过后才替换目标文件
- [x] 校验失败、无法判断或输出失败时保留原文件，并返回非零退出结果
- [x] 使用同目录临时文件完成替换，确认文件权限和编码处理策略
- [x] 检测读取后原文件被外部修改的情况，避免覆盖并发编辑
- [x] 明确符号链接的处理，保证替换和拒绝策略与 CLI 文档一致
- [x] 为 `--strip-emoji` 等已声明有损选项定义独立策略，不输出格式无损成功提示
- [x] 覆盖写入失败、中断、权限不足和多文件部分失败，报告逐文件状态

验收以修改前后的文件字节与权限为依据。失败路径原文不变，成功路径符合预期，临时文件得到清理；历史默认输出和退出约定有兼容测试。

本机证据（2026-10-13）：写回经三态校验后通过同目录临时文件原子替换，重读原路径的 inode、时间戳、权限、所有者和字节，检测并发替换 / 编辑；保留 CRLF、UTF-8 内容、POSIX mode 位和所有者 / 组，拒绝符号链接、硬链接及非 UTF-8 输入。故障注入覆盖 `fsync` 与 `os.replace` 失败、并发编辑、校验 unknown 和多文件部分失败，原字节不变且临时文件清理；`--strip-emoji` 明确输出有损状态。系统 ACL、扩展属性和文件 flags 不保留，已写入 CLI 文档。`selftest` 183 项、`unittest discover` 187 项、单文件同步检查、官网构建、CLI / 安装器静态检查和 `git diff --check` 通过。

- [x] FMT-02 已验收，故障注入和原文件保留证据已填写

### INS-01 将卸载限定在选定范围

P1；依赖 CI-01 的安装夹具。修改 [install.sh](../scripts/install.sh) 的卸载资产和作用域判断。

- [x] 限制用户级 Codex prompt 的删除，只在用户级卸载时处理
- [x] 分别列出用户级 canonical、宿主链接、prompt 和项目级安装资产
- [x] 验证项目卸载保留用户级 prompt 和另一个项目的 skill
- [x] 验证用户卸载不会改变项目级 skill
- [x] 验证重复卸载、断链和部分安装的行为，避免删除无法确认归属的目录
- [x] 验证 dry-run 前后临时夹具快照一致，输出不包含用户级 prompt

验收全部在临时根内完成。原先会计划删除全局 prompt 的 `--project --uninstall --dry-run` 场景必须回归，不能在真实用户目录试卸载。

卸载资产与归属判据：

| 范围 | 资产 | 卸载条件 |
|---|---|---|
| 用户级 | `~/.agents/skills/adhd-md` canonical | 软链只删除链接本身；实体目录要求同级 `.adhd-md-managed-canonical` 标记匹配 |
| 用户级 | `.claude/skills/adhd-md`、`.codex/skills/adhd-md`、`.grok/skills/adhd-md`、`.gemini/skills/adhd-md`、`.cursor/skills/adhd-md`、`.config/opencode/skills/adhd-md` | 只删除目标恰为 canonical 路径的软链 |
| 用户级 | `.codex/prompts/adhd-md.md` | 只在用户级卸载时删除普通文件；符号链接和其他非普通文件保留 |
| 项目级 | git 根目录下 `.claude/skills/adhd-md`、`.grok/skills/adhd-md`、`.cursor/skills/adhd-md`、`.codex/skills/adhd-md` | 只删除真实目录且其中 `.adhd-md-managed` 标记匹配的副本 |

无法确认归属的目录、非预期链接和旧版无标记副本会保留并提示检查；因此需要手动清理的旧资产不会在卸载时被递归删除。

本机证据（2026-10-13）：安装器为新建的 canonical 与项目副本写入所有权标记；用户宿主软链按目标匹配，项目副本按标记匹配。`python3 -m unittest skill.scripts.tests.test_install -v` 的 8 项隔离安装测试通过，覆盖用户 / 项目作用域、跨项目与 prompt 保留、dry-run 全树快照、重复卸载、预期和非预期断链、未标记部分目录保留，以及项目安装后可被正确卸载。所有文件操作由临时根和 `rm` / `readlink` 命令桩约束。`python3 skill/scripts/adhd_md.py selftest` 183 项通过，`python3 -m unittest discover -s skill/scripts/tests -v` 191 项通过，单文件同步检查、`bash -n scripts/install.sh` 和 `git diff --check` 通过。

- [x] INS-01 已验收，作用域矩阵和目录快照已填写

## M2 修复提取和阅读

### READ-01 保持 HTML 文本的显示内容

P2；依赖 SAFE-01，测试接入 CI-01。修改 [extract_web.py](../skill/scripts/extract_web.py) 与 [reader.py](../skill/scripts/reader.py)。

- [x] 区分原 HTML 文本节点与生成的 Markdown 标记，按上下文转义特殊字符
- [x] 同步实现阅读器的转义解释，避免把辅助反斜杠展示为正文
- [x] 覆盖星号、反引号、括号、行首井号、列表符号和反斜杠本身
- [x] 覆盖 HTML 强调、链接、代码、表格、中文混排及 Markdown 教程
- [x] 同时保存原始 HTML、提取文本、来源信息和分段 source
- [x] 添加 HTML 到最终 DOM 可见文本的独立断言，不只检查嵌入的 JSON

验收时 `2*3*4=24` 和单独的 `***` 都按原普通文本显示。原有强调和链接仍正常，分段 source 拼接严格等于提取文本。

本机证据（2026-10-13）：`test_html_text_survives_markdown_extraction_and_reader_dom` 先验证原 HTML、来源位置、转义后的提取稿及 `chunks[*].source` 拼接守恒，再将生成的阅读片段交给独立 HTML DOM 文本解析器，与源 HTML 的可见文本逐字比较（忽略结构造成的空白差异）。可见断言覆盖 `2*3*4=24`、`***`、括号、代码标记、链接语法、行首标题 / 列表、反斜杠；结构断言确认原强调、真实链接、行内代码和表格仍按结构显示。`selftest` 184 项、完整 unittest 192 项、单文件同步检查及 `git diff --check` 通过。

- [x] READ-01 已验收，可见文本和 source 守恒证据已填写

### READ-02 保留本地相对链接与图片来源

P2；依赖 SAFE-01，与 READ-01 协调转义约定。修改 [sources.py](../skill/scripts/sources.py) 和 [extract_web.py](../skill/scripts/extract_web.py)。

- [x] 区分网络 URL 与本地来源，保留原始相对引用
- [x] 保留路径、片段、查询参数、中文和空格，并定义 `<base>` 的处理
- [x] 让导出的 Markdown 保留目标地址，阅读器显示不可执行的本地来源文字
- [x] 保持 `file://` 不自动打开，保持本地文件和远程图片不被自动读取
- [x] 修正来源提示，只在目标确实保留时声称已保留链接
- [x] 覆盖上级目录、仅锚点、危险协议、损坏 URL 和没有来源的图片

验收时 `next.html#section`、`chart.png` 均可从导出稿找回。浏览器网络记录与文件读取桩证明没有隐式加载，危险协议仍不可点击。

本机证据（2026-10-13）：本地 HTML 的相对链接和图片来源保留为有效 Markdown 目标；空格与中文 percent-encode，query / fragment 留存。仅锚点、query-only、上级目录、`file://`、坏百分号、危险协议和无来源图片均有回归；本地 `<base>` 换算为相对源目录路径，HTTP(S) `<base>` 产生绝对 URL，坏 `<base>` 被忽略并提示。`extract` 输出稿能找回 `next.html#section`、`chart.png`。夹具实际创建链接目标文件，`Path.read_bytes` 桩只允许读取输入 HTML，`fetch_url` 桩确认没有网络请求；阅读 DOM 片段没有 `<img>`，本地与 file 链接没有可点击 `<a>`。`selftest` 187 项、完整 unittest 195 项、单文件同步检查与 `git diff --check` 通过。

- [x] READ-02 已验收，目标保留和资源请求记录已填写

### READ-03 控制异常输入的解析成本

P2；依赖 CI-01，可独立实现。修改 [reader.py](../skill/scripts/reader.py) 的行内识别和句子保护逻辑。

- [x] 为未闭合括号、反引号、长链接和大段正文建立性能夹具
- [x] 用有界或线性扫描消除逐位置重复扫描剩余全文的行为
- [x] 检查分段和渲染两条路径，避免同一内容被重复解析
- [x] 在固定环境记录 10 KB、20 KB、40 KB 和更大输入的多轮中位数
- [x] 分别定义网络、外部提取工具和本地解析的预算，说明 `--timeout` 的实际范围
- [x] 超限或失败时明确报错并保留原文，不用截断内容换取速度
- [x] 优化后通过已有显示测试和分段 source 守恒测试，向 READ-04 提供集成回归样例

建议目标已在本地固定环境校准：40 KB 异常输入低于 1 秒，10–80 KB 密集句界输入每翻倍增长不超过 2.5 倍。CI 用进程 CPU 时间和交错轮次减少机器调度噪声；壁钟中位数作为对照记录，不直接推广为所有机器的硬门槛。

本机证据（macOS 27.0.1 arm64、Python 3.14.5；基线 `3c8b1fb`，基线 3 轮中位数、修复版 7 轮中位数）：

| 输入 | 10 KB 基线 → 修复 | 20 KB 基线 → 修复 | 40 KB 基线 → 修复 | 80 KB 修复版 |
|---|---:|---:|---:|---:|
| 密集短强调与句界（原二次扫描热点） | 0.1954 → 0.0044 秒 | 0.7316 → 0.0084 秒 | 3.7307 → 0.0187 秒 | 0.0406 秒 |
| 未闭合括号 | 0.0019 → 0.0021 秒 | 0.0038 → 0.0052 秒 | 0.0102 → 0.0092 秒 | — |
| 未闭合反引号 | 0.0027 → 0.0026 秒 | 0.0052 → 0.0049 秒 | 0.0112 → 0.0105 秒 | — |
| 长未闭合链接 | 0.0030 → 0.0030 秒 | 0.0078 → 0.0072 秒 | 0.0153 → 0.0180 秒 | — |
| 普通句子正文 | 0.0024 → 0.0024 秒 | 0.0064 → 0.0051 秒 | 0.0108 → 0.0100 秒 | — |

修复版密集输入 10→20→40→80 KB 的壁钟中位数增长分别为 1.91×、2.23×、2.17×；80 KB 的单轮最大值为 0.0647 秒。`tracemalloc` 记录 80 KB 输入构建阶段峰值 0.37 MiB、89 个片段。行内 span、句界及片段都按前向流迭代；`build_reading_data` 先识别块，再只对最终片段渲染一次。超限策略是拒绝整个输入：网页下载 20 MiB，普通本地输入 / PDF / 标准输入 50 MiB，PDF 最多 500 页。`--timeout` 限制网页请求整体期限与每次 PDF/OCR 子进程，不限制同步的本地读取、解析和渲染。

`python3 skill/scripts/adhd_md.py selftest` 通过 190 项，`python3 -m unittest discover -s skill/scripts/tests` 通过 198 项；`python3 scripts/build_standalone.py` 后 `--check` 及 `git diff --check` 通过。显示、源字符拼接、SHA-256 和连续片段索引仍由阅读器回归覆盖。

- [x] READ-03 已验收，前后性能记录和正式预算已填写

### READ-04 验证阅读页的完整交互

P2；最终验收依赖 READ-01、READ-02、READ-03 和 CI-01。修改 [reader.html](../skill/assets/reader.html) 及浏览器测试入口。

先验证交互与进度。

- [x] 验证翻段、回看全文、目录定位和键盘操作，检查首尾边界的焦点
- [x] 验证字号、行距和重新打开后的进度恢复
- [x] 验证存储禁用、记录损坏、文档更新及分段大小变化后的恢复策略

再验证内容与资源。

- [x] 验证 Markdown 下载内容与进入阅读器的 source 一致，HTML/PDF 下载内容与提取稿一致且含来源说明
- [x] 验证全文打印包含所有片段，并重跑 READ-01 的显示用例与 READ-03 的性能样例
- [x] 验证移动端、长代码、宽表格和空文档可操作
- [x] 用脚本标签、事件属性、危险 URL 和远程图片检查无执行及无自动请求
- [x] 检查安全链接只在用户明确操作后打开，保留来源和必要隔离属性

本机浏览器证据（2026-10-13；Ego Lite Chromium，桌面 1368×900、移动 390×844；浏览器版本查询接口不可用）：逐段按钮、方向键和目录定位可达正确片段并聚焦阅读标题；首段上一段禁用，末段方向键不越界，结束/回看/重启及暂停/继续焦点正确。全文视图有 10 段且标记齐全；原文视图与输入字节对应文本完全相同，Markdown 下载 1,284 字节逐字节相同。字号 25px、紧凑行距和 3/10 进度重载后恢复；损坏记录回退到首段并修复，存储写入被拒时仍可读且提示未保存。相同原文改用 100 字分段后以 source offset 310 映射到正确的新片段；更新 source hash 后从首段开始。HTML 提取页显示原始 HTML 和来源提示，脚本未执行、图片未创建；HTML 458 字节及 PDF 305 字节下载均与 CLI 导出稿逐字节相同，PDF 页码定位正确。浏览器 `printToPDF` 输出 2 页，全部 10 段、代码 24 次重复、表格行、远程图片替代文字和原始脚本文本均可见；表格列在版面中换行，关键视图已目视核对。移动端文档宽度为 390px，代码块与表格没有造成页面横向溢出。网络事件只有本地阅读页文件请求；DOM 无 `<img>` 和危险链接，`window.readerAttack` 未定义，安全链接带 `_blank`、`noopener noreferrer` 与 `no-referrer`。

截图：

- [390px 移动阅读页](evidence/read04-mobile.png)
- [打印第 1 页](evidence/read04-print-page-1.png)
- [打印第 2 页](evidence/read04-print-page-2.png)

空文件 CLI 回归验证 `read` 与 `extract` 都返回错误且不生成半成品；空 chunk 页面使用 `role=alert` 提示重新生成阅读器。`selftest` 199 项、完整 unittest 217 项通过。READ-01 显示用例和 READ-03 性能样例都包含在自测中。所有本机浏览器验收项通过；CI-01 托管矩阵现已通过。

- [x] READ-04 已验收，浏览器回归与异常状态记录已填写（本机浏览器与 CI-01 托管工作流均通过）

## M3 完善分发和官网

### INS-02 统一宿主探测和稳定路径

P2；依赖 CI-01，先确定项目 canonical 路径。修改 [install.sh](../scripts/install.sh)、[cli.js](../bin/cli.js) 和安装说明。

- [x] 集中维护宿主 CLI 名与目录，统一 Cursor 的 `cursor-agent` 和 `cursor` 探测规则
- [x] 明确项目安装的稳定根及升级方式，成功提示指向实际可用的工具
- [x] 验证 npx 与 curl 的复制模式，清理缓存和下载目录后仍可运行
- [x] 验证 git clone 模式的软链与更新路径，保留开发用途
- [x] 验证只有 CLI、只有宿主目录、没有宿主及多个宿主的场景
- [x] 三条入口继续调用同一份安装脚本，站点脚本由工作流复制

验收在模拟下载清理后执行安装器给出的 audit 命令。六个宿主都要检查路径解析，运行时效果另由 EVAL-01 记录，不能用文件存在替代运行验证。

本机证据（2026-10-13）：`scripts/install.sh` 用单一宿主表维护宿主名、CLI 候选及用户 / 项目 skills 目录；Cursor 优先选 `cursor-agent`，并回退到 `cursor`。项目 canonical 固定在仓库 `.agents/skills/adhd-md`，宿主目录仍写入带归属标记的实体副本，重新运行同一安装命令升级。11 项隔离安装测试通过，分别覆盖 npx 缓存路径强制复制、curl 用户与项目模式解包后删除下载目录、git clone 软链重装后读取更新内容、Cursor 两种 CLI、仅 CLI、仅已有目录、无宿主、多宿主及项目卸载保留用户资产。包内 smoke 还调用解包后的实际 CLI 安装到临时用户根，删除解包包目录后从 canonical 副本重跑自测。`bash -n scripts/install.sh`、实际 npm tarball 检查和 `git diff --check` 通过；`site` 工作流仍从 `scripts/install.sh` 复制官网脚本。

- [x] INS-02 已验收，三条入口和宿主探测矩阵已填写

### INS-03 让更新失败可恢复

P2；依赖 INS-01、INS-02。修改 [install.sh](../scripts/install.sh) 的更新与清理流程。

- [x] 在目标同级位置准备新副本，校验完成后再切换
- [x] 处理目录替换、链接替换和跨文件系统的边界，避免先删旧版再复制
- [x] 将宿主链接与 Codex prompt 纳入一致的更新和恢复流程
- [x] 模拟复制、自检和切换失败，保留旧版或提供可验证的恢复路径
- [x] 处理中断和并发安装，避免新旧文件混用
- [x] 成功后清理临时资产，失败后保留必要恢复记录并给出明确提示

本机证据（2026-10-13，macOS 27.0.1 / Bash 5.3.9）：安装器为 canonical、宿主入口、所有权标记和 Codex prompt 在各自目标同级准备暂存项；复制版在切换前对暂存副本运行 `selftest`。同目录备份和重命名避免跨文件系统移动；NUL 分隔事务日志记录原目标、备份、暂存路径及原目标是否存在。SIGINT / SIGTERM 会回滚；进程异常退出后，下次安装或卸载会检查死锁所有者并恢复 active 事务，已提交事务则只清理旧备份。用户级宿主链接、项目级副本和 Codex prompt 通过同一事务提交。互斥锁阻止两个安装器并发写入，失败现场保留恢复日志。

`python3 -m unittest skill.scripts.tests.test_install -v` 通过（18 项）。故障注入覆盖暂存复制、自检、项目目录切换、用户级 host link 与 Codex prompt 切换、SIGTERM 中断、过期锁恢复和并发安装；每次失败都用临时根目录快照确认旧版完整或恢复到旧版。成功安装与重装检查链接目标不指向解包临时目录。`python3 skill/scripts/adhd_md.py selftest`（190 项）与 `python3 scripts/build_standalone.py --check` 通过。

切换多个宿主目录由同一锁和事务日志管理，但文件系统不提供跨多个目录的单次原子交换；更新期间路径按顺序切换，若被中断会回滚或在下次运行时恢复。此项不宣称多宿主读者在切换瞬间观察到单一全局原子版本。

- [x] INS-03 已验收，故障注入、恢复与并发记录已填写

### PKG-01 验证实际分发包

P2；依赖 CI-01，安装验收依赖 INS-02、INS-03。修改 [package.json](../package.json)、包排除配置和 [cli.js](../bin/cli.js)。

- [x] 排除 `__pycache__`、`.pyc`、临时文件和开发产物
- [x] 断言脚本、assets、references、单文件版及许可证完整
- [x] 从实际 `npm pack` tarball 解包运行 CLI 和自检，避免借用源码目录文件
- [x] 验证先跑测试再打包与干净工作区打包的有效文件清单一致
- [x] 修正 CLI 错误提示中的安装入口，统一版本与帮助说明
- [x] 删除或自动生成安装脚本和文档中硬编码的测试数量
- [x] 将包内缺文件和夹带缓存的断言加入 CI

验收时清理模拟 npx 缓存，已安装副本仍工作。包内运行覆盖 audit、verify、read、extract 及安装入口；远程提取使用本地服务或桩。

- [x] PKG-01 已验收，包清单和解包运行记录已填写（本机及 Node 18.20.8 托管 tarball smoke 均通过）

本机证据（2026-10-13）：`bash scripts/check_npm_package.sh` 通过。`npm pack` 清单共 36 个文件，运行 `python3 -m unittest discover -s skill/scripts/tests` 前后清单一致；必需脚本、reader asset、references、tests、standalone、README 与 MIT license 全部存在，未夹带缓存或临时产物。把实际 tarball 解到模拟 `_npx/.../node_modules/adhd-md` 后，验证 CLI 版本、帮助和错误调用提示，并运行 `audit`、`verify`、`read`、本地 HTML `extract`、HTTP 响应桩驱动的 URL `extract` 与 `selftest`。再从 tarball 安装到隔离 `ADHD_MD_HOME`，删除模拟 npx 缓存，确认安装副本仍可运行上述命令；安装目录无临时锁，链接不指向缓存。`.github/workflows/ci.yml` 的 Node CLI job 运行同一包检查脚本。脚本不依赖本机监听端口或外网。

最终补充（2026-10-13）：加入 `skill/references/rule-definitions.json` 后重新打包，tarball 共 37 个文件；测试前后清单仍一致。修正后的本地远程安装夹具将该 JSON 纳入模拟已提交源码，`test_remote_install_uses_local_tarball_and_stays_in_temp_root` 通过；包检查脚本完整通过。GitHub Actions 仍待实际运行。

### WEB-01 修复移动端和英文页

P2；依赖 CI-01，可独立修复。修改 [样式](../site/src/styles/global.css)、[布局](../site/src/layouts/Layout.astro)、[交互脚本](../site/src/scripts/app.js) 和 [ui.ts](../site/src/i18n/ui.ts)。

- [x] 在移动端保留语言切换入口，并确认导航不会挤出视口
- [x] 让两种语言的图标路径都包含正确的站点 base
- [x] 将复制成功、复制失败及动态主题提示统一放入 i18n 文案
- [x] 处理剪贴板拒绝和回退失败，不在复制失败时显示成功
- [x] 检查键盘焦点、缩放、明暗主题和减少动态效果设置
- [x] 在 390px 和桌面宽度验证两种语言，确认资源无 404

验收包含浏览器操作和官网构建。中英文复制提示正确，手机语言切换可见可用，三个图标都返回有效资源。

- [x] WEB-01 已验收，两种语言的视图和资源记录已填写

本机证据（2026-10-13）：`cd site && npm run build` 通过。ego-browser 实际访问构建预览，在中文、英文路由分别检查 390×844 与 1440×1000；四种视图的文档宽度都与视口相同，手机导航保留 `EN` / `中文` 入口。复制三图标资源并逐个 `fetch`，SVG、32px PNG、Apple touch PNG 均返回 HTTP 200；英文资源路径同样以 `/adhd-md/` 开头。浏览器交互确认中文原生复制成功、英文剪贴板拒绝后回退成功、回退 API 返回 false 时播报英文失败且不保留成功样式；主题切换后的 aria-label 与当前语言和主题一致。键盘 Tab 可见聚焦 Skip to content，2px focus outline 生效；减少动态效果媒体查询使滚动变为 auto、首屏动画缩至 0.001ms。移动端捏合后 `visualViewport.scale` 达到 1.5，viewport 声明没有禁用缩放。

### BUILD-01 去除 OG 构建的个人环境依赖

P3；依赖 CI-01。修改 [build-og.sh](../scripts/build-og.sh) 和构建说明。

- [x] 移除作者个人 gstack 绝对路径，提供明确的工具发现或参数入口
- [x] 记录浏览器、字体、运行时和安装方式，缺依赖时报出可操作的信息
- [x] 在干净环境生成中文、英文 OG 与图标的既有产物
- [x] 验证输出尺寸、文本、对比度和裁切，保留视觉检查记录
- [x] 明确允许的渲染差异，未固定全部环境前不承诺像素级一致

验收至少由一个没有作者个人目录的环境完成。模板仍为源码，位图按既有约定写入 `site/public/`，不手工修改生成位图。

- [x] BUILD-01 已验收，环境说明和视觉记录已填写

本机证据（2026-10-13）：`scripts/build-og.sh` 改为从 PATH、macOS 标准应用目录发现 Chrome/Chromium，支持 `OG_CHROME` 和 `--chrome PATH`，不再使用作者 gstack 目录或固定本地端口；缺失或无效二进制会说明安装方式和参数。Chrome 155.0.8059.40、macOS 27.0.1、Bash 5.3.9、Python 3.14.5 下显式指定系统 Chrome 完成渲染。随后在 `/private/tmp` 的隔离目录仅复制脚本、模板和 favicon SVG，再次生成四个 PNG；脚本验证签名和尺寸，中文/英文图卡均为 1200×630，Apple 图标为 180×180，favicon 为 32×32。对生成图目视检查标题、校验说明、脚本分与页脚无裁切；文本改为当前三态不变量校验的准确说明。相对亮底 `#f2efe7`，`#6f695f` 对比度为 4.73、`#bf3b26` 为 4.72；评分卡底 `#eae5d9` 上小字 `#57534b` 为 6.09。模板请求 Instrument Serif、Noto Sans SC、IBM Plex Mono，Google Fonts 不可达时退回系统字体；浏览器和字体差异允许影响字形与少量排版，不承诺像素一致。README 与站点开发说明已同步。

## M4 统一规则和评分

### LINT-01 恢复链接和图片检测

P2；依赖 CI-01，可提前修复。修改 [adhd_md.py](../skill/scripts/adhd_md.py) 的 N2、N6 检测。

- [x] 调整保护区顺序，遮蔽代码示例时保留待检查的链接目标
- [x] 分别处理 Markdown 链接、图片和裸 URL，避免互相吞掉匹配
- [x] 覆盖无意义链接文本、空 alt 和裸 URL 的命中
- [x] 覆盖有意义链接、非空 alt 和代码示例的非命中
- [x] 覆盖转义括号、中英混排与真实文件行号

验收独立断言 `[here](https://example.com)`、空 alt 和裸链接的规则 ID 与行号。代码内同样文本不误报，正常链接不新增扣分。

- [x] LINT-01 已验收，命中与非命中样例已填写

本机证据（2026-10-13）：重现了旧逻辑漏掉 Markdown 链接、图片空 alt 和裸 URL 的问题；`_protect()` 会把 URL 与 `](...)` 目标一起替换，后续链接正则因此没有输入可匹配。新增仅供 lint 使用的扫描器，按等长反引号闭合遮蔽代码，保留行宽，单独解析嵌套方括号及转义/嵌套括号目标；匹配后的链接区域从裸 URL 扫描中屏蔽，HTML tag、自定义代码片段和引用式目标定义不误报。命中样例在第 3 行报告 N2「here」，第 4 行报告 N6 空 alt，第 5 行报告 N2 裸 URL；链接目标含 `\(draft\)`、中文 URL 与中文图片 alt 均按预期处理。有效的中英链接、非空图片 alt、尖括号 autolink、行内及围栏代码例子和引用定义没有 N2/N6。两个独立 SelfTest 用例通过，完整自测和仓库集成测试在本轮终检中运行。

### RULE-01 集中维护规则定义

P2；依赖 SAFE-01，生成检查接入 CI-01。修改 [rules.md](../skill/references/rules.md)、[rubric.md](../skill/references/rubric.md)、[evidence.md](../skill/references/evidence.md) 和 [adhd_md.py](../skill/scripts/adhd_md.py)。

- [x] 定义规则 ID、轴、最低档位、自动化类型、阈值、扣分和封顶值
- [x] 建立单一结构化来源，使用标准库可读取的格式
- [x] 生成规则表和评分表的确定部分，解释性文字继续人工维护
- [x] 修复仅 C5 有最低档位过滤的问题，覆盖三个 level 与三个 scope 的行为
- [x] 声明每条规则的实现、提示或人工判断状态，校验证据映射引用
- [x] 为缺 ID、重复 ID、非法档位和生成漂移提供失败检查
- [x] 保持迁移前后的既定阈值，确需改变时单独记录理由并更新证据映射

验收三处规则数据一致，`light` 不执行仅 standard 或 deep 生效的规则。新定义进入 skill 分发包，单文件版的说明保持同步。

- [x] RULE-01 已验收，生成检查和过滤矩阵已填写

本机证据（2026-10-13）：以 `skill/references/rule-definitions.json` 为单一来源，含 86 条规则（78 条正文规则、8 条反模式），字段覆盖 ID、轴、最低档位、自动化状态、判据、实现状态、finding ID、维度、扣分、单项封顶和全局反模式上限。运行时阈值从 JSON 载入；Python 标准库生成 `rules.md`、`rubric.md` 和 `evidence.md` 的确定表格，解释文字仍手工维护。验证器检查维度权重总和、规则/发现/评分 ID 唯一性、轴、档位、实现类型、阈值字段、运行时 Finding 一致性及生成漂移。`scripts/tests/test_build_rules.py` 的缺 ID、重复 ID、非法档位与表格漂移 4 项全部通过；`python3 scripts/build_rules.py --check` 通过。

覆盖矩阵的每格依次表示“适用 / 脚本检查 / 仅提示 / 需判断 / 仅自动修复 / 硬门禁”；矩阵测试同时断言没有未实现规则：

| scope | light | standard | deep |
|---|---|---|---|
| format | 24 / 16 / 2 / 3 / 2 / 1 | 39 / 23 / 4 / 9 / 2 / 1 | 41 / 23 / 5 / 10 / 2 / 1 |
| content | 2 / 0 / 0 / 1 / 0 / 1 | 37 / 19 / 3 / 14 / 0 / 1 | 46 / 20 / 3 / 22 / 0 / 1 |
| both | 25 / 16 / 2 / 4 / 2 / 1 | 75 / 42 / 7 / 23 / 2 / 1 | 86 / 43 / 8 / 32 / 2 / 1 |

`skill/references/rule-definitions.json` 已由 `package.json` 的 `skill/` 文件规则收录；重新生成并检查 `dist/adhd-md.standalone.md` 后通过同步检查。既有阈值和扣分从原定义迁入；C5 仍只在 deep 生效，回归覆盖三个 level。

### SCORE-01 区分脚本分与未评分项

P2；依赖 RULE-01、LINT-01。修改 [adhd_md.py](../skill/scripts/adhd_md.py) 的 audit、report 和 JSON 输出，以及相应说明。

- [x] 从规则定义计算适用、已检查、仅提示和需判断的规则数量
- [x] 输出脚本分时同时显示覆盖范围，未判定项目保持未判定状态
- [x] 明确 scope 对过滤展示、扣分和覆盖率的影响，并记录选择依据
- [x] 文本与 JSON 使用相同计算结果，保留字段兼容或提供版本迁移说明
- [x] 用独立手算样例验证权重、封顶、边界阈值和 X 组全局扣分
- [x] 报告包含不变量警告与失败，避免出现有警告却声称全部保全的文案
- [x] 修订评分变化后的示例与官网，保留版本和旧结果的比较依据

验收已知未判定项不会被表述成通过。脚本分和完整评价明确分开，同一输入的文本、JSON、report 与独立手算一致。

- [x] SCORE-01 已验收，输出兼容和手算对照已填写

本机证据（2026-10-13）：`coverage_summary()` 按规则定义及 `level` / `scope` 统计适用、脚本检查、可计分、仅提示、需判断、自动修复、硬门禁和未实现项；所有 3×3 组合均有精确断言。`scope` 只过滤 findings 和 coverage，审计分按全文所有适用轴计算。JSON 升至 schema 2，保留旧 `findings` 全轴字段并新增 `shown_findings`、覆盖范围和 scope 说明；文本与 JSON 的 `audit`、`report` 共享评分及覆盖计算。脚本分的 `band` 为 null，报告明确尚需人工判断的项目不代表通过；warning、fail 和 unknown 均有对应显示 / 状态。

独立回归覆盖手算维度权重与单项封顶、X 组全局 20 分上限、完整评分纳入 judge findings、评分档位边界及 C5 最低档位。报告 JSON 与 `audit` 的 after 分数及覆盖数据逐项比较；数值变化的 warning 样例返回 `unknown` 并在文本报告中显示警告。规则定义、评分表、证据索引、SKILL、评测说明、示例说明和中英文官网覆盖数已同步；旧评测样例明确标为历史口径，避免与新规则分数直接比较。`selftest` 199 项、完整 unittest 217 项、规则生成器测试 4 项、规则表检查、standalone 重建 / 检查、官网构建、npm tarball smoke 与 `git diff --check` 均通过。

## M5 建立评测和发布记录

### EVAL-01 建立模型执行回归

P2；最终验收依赖 FMT-02、SCORE-01，测试夹具可提前准备。更新 [eval.md](eval.md) 与 [host-matrix.md](host-matrix.md)。

- [x] 扩充中英语料，覆盖 README、教程、参考、runbook、会议记录和边界 Markdown
- [x] 将调参用例与保留评测集分开，冻结输入、预期约束和来源
- [ ] 记录模型、宿主、skill 提交、参数、提示词和重复运行次数
- [ ] 检查 scope 越界、信息遗漏、judge 规则完成情况和反模式，保留原始产物
- [ ] 由独立人工或已标注约束复核信息保留，不能只依赖同一模型的自述
- [ ] 分别记录宿主发现、技能加载、工具执行和最终结果，不将其中一项代替全部
- [x] 对无法运行的宿主标为未验证，按可复现步骤补齐支持矩阵

建议首轮使用至少 12 篇语料，并对代表组合重复 3 次。样本规模属于初始预算；报告逐例结果和失败原因，不能仅展示平均分上升。

准备进度（2026-10-13）：已冻结 [`held-out v1 语料与答案键`](eval-corpus/held-out/manifest.md)，共 12 篇中英文合成案例，覆盖 README、教程、参考、runbook、会议记录和边界 Markdown；与已参与调参及 `selftest` 的 4 组回归样例分开。`shasum -a 256 -c SHA256SUMS` 验证全部 12 例与 manifest 均通过；运行模板包含宿主发现、加载、工具、参数、原始产物、verify、分数、未判定项和独立复核字段。曾尝试在临时目录启动 Codex CLI，但只读用户态状态目录阻止 CLI 初始化；Claude Code 又被本机前置 hook 因缓存目录只读而阻止，返回 0 turns、0 成本。两次都没有模型响应或可计入的评测结果。模型矩阵与人工复核尚未执行，EVAL-01 保持未完成。

宿主状态补充（2026-10-13）：[`host-matrix.md`](host-matrix.md) 已记录六个宿主 CLI 的本机版本和本轮执行状态；版本可用性不等于 skill 加载或任务执行。未产生响应的 Codex 与 Claude 仍标为未验证，Grok、Gemini、Cursor 和 opencode 本轮未运行。Python / Node 与 PDF/OCR 的本机精确版本，以及 GitHub Actions 实测版本已记录；CI 只验证 Python 3.9 / 3.14 两端点和所列 Node 版本，不推断所有中间版本或宿主模型行为。

- [ ] EVAL-01 已验收，原始产物和独立复核记录已填写

### EVAL-02 验证真实阅读任务效果

P3；依赖 EVAL-01、READ-04。新增读者试验方案和结果记录。

- [ ] 选择实际查找信息、理解约束和执行步骤的任务，预先写好标准答案
- [ ] 记录理解正确率、任务耗时、信息遗漏及主观阅读负担
- [ ] 平衡原版与改写版的阅读顺序，避免同一篇重复阅读产生学习偏差
- [ ] 将改写效果与阅读器效果分开比较，避免同时改变两个变量
- [ ] 首轮以 5–8 位自愿参与者发现可用性问题，明确样本与结论限制
- [ ] 取得试验参与和结果使用同意，记录匿名结果与退出方式
- [ ] 根据失败任务调整规则，保留未改善或变差的结果

首轮用于发现产品问题，不能用于证明 ADHD 疗效或总体效果。招募时间未计入开发人日；若延期，记录原因和后续条件，继续保持此任务未完成。

准备状态（2026-10-13）：已新增 [首轮试验方案](reader-study-protocol.md)，包含匿名记录字段、同意说明、2×2 排版 / 阅读器条件、平衡顺序和结论边界。用户说明目前暂时无法安排参与者；尚未招募、取得参与同意或收集数据。本节暂缓执行但保持未完成，不能以延期代替试验结果。

- [ ] EVAL-02 已验收，试验方案、结果和结论边界已填写

### REL-01 核对发布候选及说明

P2；完整候选依赖 M0 至 M4、EVAL-01。EVAL-02 可以明确延期，延期时本路线图仍有未完成项。

- [x] 跑完通用检查及受影响模块的回归，记录工具版本与跳过原因
- [x] 从隔离夹具和实际 npm tarball 验证三种安装入口、更新、卸载和缓存清理后的运行
- [x] 核对 Python、Node、宿主和 PDF/OCR 的本机与 CI 实测范围
- [x] 更新 README、skill、英文官网、单文件版和变更记录的行为说明
- [x] 核对 parser、verify 和 JSON 兼容变化，在变更记录中提供迁移或恢复方法
- [x] 检查未关闭任务、已知限制和评测结论，变更记录引用对应证据
- [ ] 准备版本与产物，按项目既有发布流程交付

本清单只规划发布动作。制作 roadmap 不会自动推送、创建 PR、发版或部署。候选验收通过后，实际发布仍按届时的任务授权执行。

- [ ] REL-01 已验收，候选版本、检查结果和发布记录已填写

本机候选准备记录（2026-10-13）：新增 [`CHANGELOG.md`](../CHANGELOG.md)，保持版本 `0.1.0` 不变并标为 Unreleased；其中列出本轮用户可见改动、JSON / verify / 写回 / 卸载迁移说明、已知限制和未关闭门禁。变更记录纳入 npm `files`，实际 `npm pack` tarball 38 个文件；测试前后清单一致，解包副本的 CLI、audit、verify、read、HTML / URL extract、自检及隔离安装通过。三种安装入口、更新、作用域卸载和模拟缓存清理由隔离测试覆盖；curl 路径使用本地 tarball 夹具，不访问发布站点。README、skill、英中文案、standalone 与规则表同步检查均通过；官网在本机 Node 24.14.0 和 GitHub Node 22.12.0 构建通过。精确本机与托管工具版本见 [宿主矩阵](host-matrix.md)。CI-01、READ-04、PKG-01 已通过；EVAL-01 模型结果与独立复核仍未完成，EVAL-02 依用户说明暂缓；因此没有创建版本标签或正式发行产物，REL-01 保持未关闭。

终检（2026-10-13）：`python3 skill/scripts/adhd_md.py selftest` 199 项通过；`python3 -m unittest discover -s skill/scripts/tests -v` 217 项通过；`python3 -m unittest discover -s scripts/tests -v` 4 项通过。`python3 scripts/build_rules.py --check`、`python3 scripts/build_standalone.py --check`、`bash -n scripts/install.sh scripts/check_npm_package.sh scripts/build-og.sh`、`bash scripts/check_npm_package.sh`、`cd site && npm run build` 与 `git diff --check` 均通过。代码验收 run `38398278808` 与最终文档提交 run `38399525064` 的六个 job 均通过；两类故障注入均使预期 PR 检查变红，且没有触发 Pages。未运行的检查仅剩模型回归、独立人工复核和自愿读者试验；EVAL-02 暂缓，REL-01 因评测未完成保持开放。

## 检查入口

在仓库根目录执行必跑检查。预期所有测试通过，单文件版与源同步；测试数量随着新增回归变化，不固定为 155。

```bash
python3 skill/scripts/adhd_md.py selftest
python3 scripts/build_standalone.py --check
```

修改 `skill/SKILL.md` 或 `skill/references/` 下的 `rules.md`、`antipatterns.md`、`cjk.md` 后，先生成再检查。其他被生成器读取的来源变更也要同步，禁止手改 `dist/`。

```bash
python3 scripts/build_standalone.py
python3 scripts/build_standalone.py --check
```

修改官网页面或组件后，在站点目录构建。预期构建成功，产物位于忽略的 `site/dist/`。

```bash
cd site
npm run build
```

其余入口在对应任务中实现并接入 CI，当前不能当作已有命令执行。范围包括独立结构语料、安装故障注入、实际 tarball 验证、浏览器回归和性能预算。

命令执行成功后仍需阅读结果。只有跳过记录、构建成功或分数上升，都不足以代替对应任务的验收。

## 交付记录模板

复制下列模板填写到关联 PR 或验收记录。证据可链接到测试输出、提交和截图，避免在清单中堆积日志。

```text
任务 ID
负责人和复核人
关联提交或 PR
复现输入和修复前行为
修复后预期与实际结果
独立验收依据
测试命令、版本、环境与结果
兼容变化与恢复方法
剩余问题及关联任务
关闭日期
```

关闭一个里程碑时，将实际投入和剩余任务同步到路线图。拆任务时保留原 ID 的关联记录，不能删除尚未完成的验收条件。
