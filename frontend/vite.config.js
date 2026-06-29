import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// Dev: Vite serves the SPA and proxies /api to the FastAPI backend so that
// session cookies remain same-origin. Prod: `vite build` -> ../frontend/dist,
// which FastAPI serves directly.
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8100', changeOrigin: true },
    },
  },
  build: { outDir: 'dist', emptyOutDir: true },
});
