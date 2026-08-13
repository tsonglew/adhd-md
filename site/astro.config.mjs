// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  site: 'https://tsonglew.github.io',
  base: '/adhd-md',
  // 关闭 HTML 压缩，保证 <code> 块里的换行与缩进原样输出
  compressHTML: false,
});
