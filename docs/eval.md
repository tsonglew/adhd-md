# 验证结论

记录最初建于 2026-08-13。以下宿主与分数实测多基于当时的规则定义和二态 verifier；2026-10-13 起 verifier 增加 `pass` / `fail` / `unknown` 三态，规则与评分另迁入 `rule-definitions.json`。历史「通过」不自动等于当前校验通过，历史分数也不能直接和当前版本横向比较。当前状态以本文件的重测记录和执行清单为准。

- [已验证](#已验证)
- [没验证](#没验证)
- [已知局限](#已知局限)

## 已验证

### 1. 六个宿主都能加载（实证）

装完之后逐个检查软链能否解析、`SKILL.md` 能否读到、frontmatter 能否解析：

| 宿主 | 路径 | 结果 |
|---|---|---|
| Claude Code | `~/.claude/skills/adhd-md/SKILL.md` | ✓ `name=adhd-md` |
| Codex | `~/.codex/skills/adhd-md/SKILL.md` | ✓ `name=adhd-md` |
| Grok Build | `~/.grok/skills/adhd-md/SKILL.md` | ✓ `name=adhd-md` |
| Gemini CLI | `~/.gemini/skills/adhd-md/SKILL.md` | ✓ `name=adhd-md` |
| Cursor | `~/.cursor/skills/adhd-md/SKILL.md` | ✓ `name=adhd-md` |
| opencode | `~/.config/opencode/skills/adhd-md/SKILL.md` | ✓ `name=adhd-md` |

复现：

```bash
for d in ~/.claude ~/.codex ~/.grok ~/.gemini ~/.cursor ~/.config/opencode; do
  p="$d/skills/adhd-md/SKILL.md"
  [ -r "$p" ] && echo "$d ✓ $(sed -n 's/^name: //p' "$p")" || echo "$d ✗"
done
```

### 2. Claude Code 与 Codex 运行时确实识别并能照做（实证）

**Claude Code**：装完之后当前会话的可用 skill 列表里出现 `adhd-md`，description 完整。这是运行时识别，不只是文件存在。

**Codex**：headless 跑了一次完整流程，独立复现全部工作流。

```bash
codex exec "把 t1.md 改成 ADHD 友好的排版，只改格式不要改任何一个字" \
  -C /tmp/adhd-eval -s workspace-write
```

Codex 自主完成了：

- 跑 `git status` 发现 `t1.md` 有未提交改动 → **自己决定写到旁路文件 `t1.adhd.md`，没覆盖原文件**（SKILL.md 第 0 步的逻辑）
- 跑 `audit` 拿到 87.8
- 只改格式：结论前置、拆段、标识符包成行内代码、告警内容改引用块
- 跑 `verify` 与 `report`
- 按输出契约给报告：scope/level、分数 delta、维度表、verify 结论、改了什么、故意没改什么

独立校验它的产物（不采信它的自述）：

| 项 | 结果 |
|---|---|
| `verify --scope=format`（旧版二态） | 通过，正文 token 多重集完全一致 |
| 脚本分 | 87.8 → 100.0 |
| 反模式扣分 | 0 |

它的成品与我手写的 `02-zh-readme.after.md` **不同但人工审阅认为符合 format 约定**：我把四句配置说明转成列表，它选择拆成两段并把两条警告合成一个引用块。两种都拿 100 分。早期三态校验曾把所有词序改变都报为 `unknown`；VER-02 后，仅未改写且唯一映射的完整块移动可以通过并附指代提示，句内换序和重复块歧义仍需人工复核。

这条比「六个宿主都能加载」更有说服力：**另一个厂商的模型照着同一份 SKILL.md，做出了合格且风格自主的结果。**

### 3. 确定性层与宿主无关（199 项自测）

`adhd_md.py` 是纯标准库 Python，不依赖任何宿主。**审计分数、格式修复与当前实现的不变量检查会在六个宿主上执行相同逻辑** —— 因为跑的是同一个进程，不是同一个模型。这只说明检查结果一致，不代表检查范围外的内容完整。

这是整个设计里最重要的一条：把能算准的部分从模型手里拿走，跨 agent 一致性就不再依赖模型能力。

```bash
python3 skill/scripts/adhd_md.py selftest    # 2026-10-13：199 项通过
```

其中包含示例语料回归门禁：4 组 before/after 必须分数上升、反模式扣分为 0，并符合逐组声明的 verifier 状态。

### 4. 示例语料（回归门禁）

| 组 | scope / level | 脚本分 | verify |
|---|---|---|---|
| 01 中文会议记录 | `both` / `deep` | 76.6 → 100 | `unknown`：含 `<details>` 原始 HTML |
| 02 中文 README | `format` / `standard` | 87.8 → 100 | `unknown`：块顺序变化需人工核对 |
| 03 英文运维手册 | `both` / `standard` | 72.8 → 100 | `pass` |
| 04 英文 API 参考 | `format` / `light` | 83.9 → 89.2 | `pass` |

04 停在 89.2 分是正确结果：`format` + `light` 写不了 TL;DR。

### 5. 自己吃自己的狗粮

仓库全部文档跑 `audit`：

| 文件 | 脚本分 |
|---|---|
| README.md | 100.0 |
| AGENTS.md | 100.0 |
| doc-types.md | 97.0 |
| host-matrix.md | 96.7 |
| rubric.md / cjk.md | 95.8 |
| antipatterns.md | 94.6 |
| rules.md | 94.2 |
| SKILL.md | 93.8 |
| examples/README.md | 89.8 |
| standalone 单文件 | 89.0 |

狗粮抓出来的真 bug（都已修，都补了回归测试）：

1. 句长统计被短列表项稀释 —— 88 字的怪物句混在一堆三字列表项里，均值 26，p90 也抓不到。改成逐句判定
2. H1 把文档中段的短句当成首屏结论 —— 改成只看第一个 H2 之前，且背景铺垫开头不算
3. 中英混排 tokenizer 不一致 —— `另外Node18` 逐字拆、`另外 Node18` 按词拆，导致加空格被误判成丢词
4. verify 比序列而不是多重集 —— 「结论块前置」是合法 format 操作，却被判失败
5. 行内代码被剥掉导致误报 —— 把裸标识符包成 `` `code` `` 被当成丢词
6. 代码块里的示例 emoji 被当成违规 —— 反模式文档演示「emoji 汤」时自己扣分
7. W4/W6 行号全指向首个匹配 —— 而且重复计数
8. N2/N6 把行内代码里的 `![]()` 当成真链接
9. X2 碎片化阈值没分语言，也没排除含代码块的章节 —— 误伤合法的步骤文档
10. `fmt --toc` 生成的目录被自己的 H2/L6 规则报出来 —— 工具自相矛盾

自己的示例也被抓过一次：03 的第一版 X 扣分 −14（整句加粗 + 每步一节）。

### 5. H4 提到 standard 之后的真实 agent 评测（2026-08-15）

问题：H4 从 `deep` 提到 `standard` 后，模型会不会到处加时间预估？新增的 A7/A8/N7 会不会被执行？

环境：Codex 0.36.0 + `gpt-5.6-sol`，`/tmp/adhd-eval` 干净的 git 仓库，skill 源码同步到 `/tmp/adhd-upstream/skill`，四个语料独立会话跑 `scope=both` 全流程。

| 用例 | scope / level | 脚本分 before → after | verify | H4 行为 | 新规则行为 |
|---|---|---|---|---|---|
| t1 中文 README | both / standard | 87.8 → 100 | 通过 | `约 1 分钟读完`，合理 | A1 下一步正常 |
| t2 英文 API 参考 | both / light | 83.9 → 89.2 | 通过 | **没有加**，符合 light 排除 | — |
| t4 中文会议记录 | both / deep | 76.2 → 100 | 通过 | `约 2 分钟` + 读完可确认事项，合理 | 待办前置成复选框 |
| t3 英文 runbook | both / standard | 72.8 → 100 | 通过 | 见下面迭代 | 见下面迭代 |

结论一：**没有发现滥用**。四个用例没有一个出现「每节都塞时间」或编造时长；light 档正确不加。

结论二：**judge 规则只写在规则表里不够，模型会漏。** t3 前两轮都漏掉 H4（runbook 首屏没有时间/篇幅预估），A7 也只做了判断条件、没做预期输出。第三轮在 `rules.md` 的「需要判断的规则详解」里补了 H4/A7/A8/N7 的写法示例后重跑：

| 轮次 | H4 | N7 | A7 | A8 |
|---|---|---|---|---|
| 第 1 轮（旧 skill，H4 还是 deep） | 无 | 无 | 部分 | 部分 |
| 第 2 轮（H4 已提前，但规则表无详解） | 无 | 无（3 步，本来就不该有） | 部分 | 部分 |
| 第 3 轮（补详解与骨架示例后） | `四步响应路径` | `Step 1 of 4` 到 `Step 4 of 4` | 每步有预期或验证条件 | 复合动作拆成子步骤 |

第 2 轮 N7 无标注不算违规：当时模型只拆出 3 步，而 N7 的阈值是 ≥4 步。第 3 轮拆出 4 步后自动带上了进度。

复现：`python3 skill/scripts/adhd_md.py selftest` 覆盖脚本分与当前实现的不变量检查，不覆盖 judge 规则，也不能证明完整保留。2026-10-13 最近复验 199 项自测和 217 项完整 unittest；此前记录的 190 / 198 项是早期结果。judge 规则的回归仍需实际宿主运行并逐条留证。

## 没验证

**Grok / Gemini / Cursor / opencode 四个宿主的运行时执行效果。** 只验证了它们能加载 skill，没验证模型照着 SKILL.md 做出来的结果好不好。

2026-10-13 的当前版本试跑也未产生模型结果：Codex CLI 无法初始化只读状态目录；Claude Code 的本机前置 hook 因缓存目录只读而拒绝运行，返回 0 turns、0 成本。两次都没有模型输出，不能算宿主验收；当前执行环境下六宿主矩阵仍未完成。

`grok ... --output-format plain --always-approve` 跑了 300 秒无输出、未改文件，headless 模式可能仍需 TTY。没继续深究。

自己动手验：

```bash
mkdir -p /tmp/adhd-eval && cd /tmp/adhd-eval
cp <repo>/skill/references/examples/02-zh-readme.before.md t1.md
cp t1.md t1.orig.md
# 在任一 agent 里说：把 t1.md 改成 ADHD 友好的排版，只改格式不要改任何一个字
python3 <repo>/skill/scripts/adhd_md.py verify t1.orig.md t1.md --scope=format
python3 <repo>/skill/scripts/adhd_md.py report  t1.orig.md t1.md --scope=format
```

只有当前 `verify` 返回 `pass` 且反模式扣分为 0，才算机器检查过关。`unknown` 要人工复核并单独记录，不能计为 pass。

**多篇语料 × 多宿主的矩阵评测。** 当前 4 组语料的 after 有 3 组是我手写的，只有 02 拿到了 Codex 独立跑出的第二个版本。真实评测应当让每个宿主自己跑 after，再比较分数、`pass`、`fail` 与 `unknown` 的比例。

### EVAL-01 的执行与记录约定

`skill/references/examples/` 的 4 组样例已参与调参与 `selftest` 回归，只能作为回归集，不能再称为保留评测集。独立评测应另建至少 12 个冻结案例，覆盖中英文 README、教程、参考、runbook、会议记录和边界 Markdown；每例保存输入、来源、语言、类型、scope / level、不可变约束、SHA-256 和精确提示词。模型输出与人工复核结果不得回写输入文件。

首批 12 个合成案例已放在 [`docs/eval-corpus/held-out/`](eval-corpus/held-out/)，包含独立答案键和 SHA-256 清单；清单核验通过前不得开始运行。该候选集尚无模型输出，也尚未完成独立人工复核。

每次运行至少记录：案例 ID 与输入哈希、宿主和模型版本、CLI 版本、skill 提交、启动方式与权限参数、精确提示词、运行序号、skill 是否被发现与加载、是否调用工具、原始输出位置与哈希、verify 三态、反模式扣分、脚本分、未判定规则及独立复核结论。宿主发现、skill 加载、工具执行和结果质量分开记录，任一阶段失败都不能记作完整通过。

当前规则开发期间创建的案例只作为候选冻结集。它们一旦用于调参，就转入回归集，并需另行建立新的保留集；不能用同一批输入反复修规则后再声称是独立评测。单次模型运行记录用[记录模板](eval-run-template.md)；读者试验与结论边界见[阅读试验方案](reader-study-protocol.md)。

## 已知局限

| 局限 | 说明 |
|---|---|
| 历史脚本分覆盖不完整 | 旧版把 34 条 judge-only 与 3 条提示项按零扣分处理。当前默认 standard + both 有 23 条需模型判断、7 条仅提示；报告标明未判定项，不能把它们说成通过 |
| H1 是代理指标 | 「这段是结论还是铺垫」靠关键词模式判断，会漏 |
| 讲规则的文档会自报 | 文档里写「如上所述」当反面例子，W4 照样命中。无解，也不该解 |
| `fmt` 的中文标点规范化会改字符 | 不是逐字节无损；`verify` 对词序变化返回 `unknown`，也不能证明完整内容无损 |
| 只测过 macOS + Python 3.14 | 声明兼容 3.9+，未在其他版本上跑过 |
