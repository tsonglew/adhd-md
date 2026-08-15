# AGENTS.md

本仓库提供一个跨 agent 通用的 skill：把 Markdown 改造成 ADHD 友好、可扫读的版本。

## 要改文档时

读 `skill/SKILL.md` 并严格执行其中的工作流。确定性工具层在 `skill/scripts/adhd_md.py`（纯标准库，`python3` 直接跑）。

**铁律：只重排信息，绝不删信息。** 篇幅太长就折叠或移到附录。

`scope=format` 时 `verify` 是硬门禁，不通过必须回退。

## 要改本仓库时

改完必须跑：

```bash
python3 skill/scripts/adhd_md.py selftest        # 48 项，含示例语料回归
python3 scripts/build_standalone.py --check      # dist/ 是否与 skill/ 同步
```

改了 `skill/SKILL.md` 或 `skill/references/{rules,antipatterns,cjk}.md` 之后，重新生成单文件版：

```bash
python3 scripts/build_standalone.py
```

`dist/` 是生成产物，不要手改。

规则的阈值、扣分、轴/档在三处必须一致：`references/rules.md` 的表、`references/rubric.md` 的扣分表、`scripts/adhd_md.py` 的 `DEDUCT` 字典。改一处就要同步另两处。

新增或改动规则的机制依据时，同步更新 `references/evidence.md` 的映射。

## 分发相关

三条安装路径共用 `scripts/install.sh`，不要分叉出第二份：

- `npx github:tsonglew/adhd-md` —— `bin/cli.js` 调它，并强制 `--copy`（npx 缓存会被清理，软链会变死链）
- `curl … | bash` —— 脚本自己下 tarball。站点上的 `install.sh` 由 Pages workflow 从 `scripts/` 复制，不是第二份源码
- `git clone` + `bash scripts/install.sh` —— 软链到仓库，方便开发

给 `skill/` 加新文件时，检查 `package.json` 的 `files` 字段是否覆盖 —— 漏了的话 npx 装出来会缺文件，本地却看不出问题。

## 官网（site/）

Astro 项目。文案统一在 `site/src/i18n/ui.ts`（中英两套，改文案改这里，不要直接改组件里的字）。改了页面或组件之后跑 `cd site && npm run build` 确认能过，产物在 `site/dist/`（已 gitignore，不提交）。设计源模板（`site/og.html`、`site/icon-square.svg`）改动后重跑 `scripts/build-og.sh`，位图产物写进 `site/public/`。`site/public/install.sh` 由 Pages workflow 从 `scripts/install.sh` 复制，不手改。
