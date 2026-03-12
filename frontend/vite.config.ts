import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// Backend route prefixes that must be forwarded to FastAPI.
// HTML page routes handled by the React SPA (/, /status, /dashboard, /analytics)
// are intentionally excluded so Vite keeps serving index.html for them.
const BE_PATHS = [
  'api',          // /api/status, /api/capabilities, /api/status/page, …
  'upload',
  'events',
  'progress',
  'download',
  'cancel', 'pause', 'resume',
  'tasks',
  'system-info',
  'languages',
  'health', 'ready',
  'embed',
  'combine',
  'subtitles',
  'track',
  'metrics',
  'monitoring',
  'security',
  'auth',
  'scale',
  'export',
  'query',
  'logs',
  'feedback',
  'webhooks',
]

const BE_PROXY = {
  target: 'http://localhost:8000',
  changeOrigin: true,
}

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  server: {
    port: 5173,
    proxy: {
      // WebSocket needs a separate entry with ws:true
      '/ws': { target: 'ws://localhost:8000', ws: true, changeOrigin: true },
      // Single regex covers every known backend path prefix.
      // Add new prefixes to BE_PATHS above — no other change needed.
      [`^/(${BE_PATHS.join('|')})(/.*)?$`]: BE_PROXY,
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
