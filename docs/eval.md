# 验证结论

2026-08-13。分清「验证过的」和「没验证的」—— 后者一律不写成结论。

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
- 跑 `audit` 拿到 86.4
- 只改格式：结论前置、拆段、标识符包成行内代码、告警内容改引用块
- 跑 `verify` 与 `report`
- 按输出契约给报告：scope/level、分数 delta、维度表、verify 结论、改了什么、故意没改什么

独立校验它的产物（不采信它的自述）：

| 项 | 结果 |
|---|---|
| `verify --scope=format` | 通过，正文 token 多重集完全一致 |
| 脚本分 | 86.4 → 100.0 |
| 反模式扣分 | 0 |

它的成品与我手写的 `02-zh-readme.after.md` **不同但同样合格**：我把四句配置说明转成列表，它选择拆成两段并把两条警告合成一个引用块。两种都在 `format` 档的边界内，都拿 100 分。

这条比「六个宿主都能加载」更有说服力：**另一个厂商的模型照着同一份 SKILL.md，做出了合格且风格自主的结果。**

### 3. 确定性层与宿主无关（36 项单测）

`adhd_md.py` 是纯标准库 Python，不依赖任何宿主。**审计分数、格式修复、无损校验在六个宿主上必然一致** —— 因为跑的是同一个进程，不是同一个模型。

这是整个设计里最重要的一条：把能算准的部分从模型手里拿走，跨 agent 一致性就不再依赖模型能力。

```bash
python3 skill/scripts/adhd_md.py selftest    # 36 项
```

其中包含示例语料回归门禁：4 组 before/after 必须分数上升、反模式扣分为 0、`verify` 通过。

### 4. 示例语料（回归门禁）

| 组 | scope / level | 脚本分 | verify |
|---|---|---|---|
| 01 中文会议记录 | `both` / `deep` | 73.6 → 100 | 通过 |
| 02 中文 README | `format` / `standard` | 86.4 → 100 | 通过（严格 token 比对） |
| 03 英文运维手册 | `both` / `standard` | 68.5 → 100 | 通过 |
| 04 英文 API 参考 | `format` / `light` | 81.8 → 88 | 通过 |

04 停在 88 分是正确结果：`format` + `light` 写不了 TL;DR。

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

## 没验证

**Grok / Gemini / Cursor / opencode 四个宿主的运行时执行效果。** 只验证了它们能加载 skill，没验证模型照着 SKILL.md 做出来的结果好不好。

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

`verify` 通过且反模式扣分为 0，就算这个宿主过关。

**多篇语料 × 多宿主的矩阵评测。** 当前 4 组语料的 after 有 3 组是我手写的，只有 02 拿到了 Codex 独立跑出的第二个版本。真实评测应当让每个宿主自己跑 after，再比分数与 `verify` 通过率。

## 已知局限

| 局限 | 说明 |
|---|---|
| 脚本分系统性虚高 | 31 条 `judge` 规则按满分计入。脚本分低说明一定有问题，脚本分高不说明没问题 |
| H1 是代理指标 | 「这段是结论还是铺垫」靠关键词模式判断，会漏 |
| 讲规则的文档会自报 | 文档里写「如上所述」当反面例子，W4 照样命中。无解，也不该解 |
| `fmt` 的中文标点规范化会改字符 | 严格说不是逐字节无损，但 `verify` 的 token 归一化把全/半角折叠，词一级仍可证明无损 |
| 只测过 macOS + Python 3.14 | 声明兼容 3.9+，未在其他版本上跑过 |
