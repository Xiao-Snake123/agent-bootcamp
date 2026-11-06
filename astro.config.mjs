import { defineConfig } from 'astro/config';

// 静态内容站 + 站内问答（问答后端独立跑在 :8000）
export default defineConfig({
  server: { port: 4321 },
  trailingSlash: 'ignore',
});
