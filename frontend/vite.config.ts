import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  server: {
    port: 5173,
    proxy: {
      '/upload':       { target: 'http://localhost:8000', changeOrigin: true },
      '/events':       { target: 'http://localhost:8000', changeOrigin: true },
      '/progress':     { target: 'http://localhost:8000', changeOrigin: true },
      '/download':     { target: 'http://localhost:8000', changeOrigin: true },
      '/cancel':       { target: 'http://localhost:8000', changeOrigin: true },
      '/pause':        { target: 'http://localhost:8000', changeOrigin: true },
      '/resume':       { target: 'http://localhost:8000', changeOrigin: true },
      '/tasks':        { target: 'http://localhost:8000', changeOrigin: true },
      '/system-info':  { target: 'http://localhost:8000', changeOrigin: true },
      '/languages':    { target: 'http://localhost:8000', changeOrigin: true },
      '/health':       { target: 'http://localhost:8000', changeOrigin: true },
      '/embed':        { target: 'http://localhost:8000', changeOrigin: true },
      '/combine':      { target: 'http://localhost:8000', changeOrigin: true },
      '/subtitles':    { target: 'http://localhost:8000', changeOrigin: true },
      '/api':          { target: 'http://localhost:8000', changeOrigin: true },
      '/track':        { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
