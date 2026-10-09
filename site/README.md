# adhd-md 官网

Astro 构建的静态单页，校样台设计。开发：

需要 Node 22.12 以上版本，以及能通过 `python3` 运行的 Python 3.9 以上版本。构建会调用仓库里的阅读生成器，产出中英文完整阅读示例。

```bash
npm install
npm run dev      # 本地预览
npm run build    # 构建到 dist/，Pages workflow 部署的就是它
```

- 页面骨架 `src/pages/index.astro`，区块在 `src/components/`，全局样式 `src/styles/global.css`，交互 `src/scripts/app.js`
- 位图产物（og.png、图标）在 `public/`，由仓库根的 `scripts/build-og.sh` 从 `og.html` / `icon-square.svg` / `public/favicon.svg` 渲染，不手改 PNG
- `public/install.sh` 由 CI 从 `scripts/install.sh` 复制，不手改
- 阅读示例文案在 `src/i18n/ui.ts`，首页预览和 `/reader-demo.html`、`/en/reader-demo.html` 共用同一份原文
