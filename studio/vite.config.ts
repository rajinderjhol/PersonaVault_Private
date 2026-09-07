import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  base: '/studio/',
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/v2': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: true,
        cookieDomainRewrite: '',
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log('🔀 Proxying /v2:', req.url, '→', proxyReq.path);
          });
          proxy.on('error', (err, req, res) => {
            console.log('❌ Proxy error /v2:', err);
          });
        },
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: true,
        cookieDomainRewrite: '',
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            console.log('🔀 Proxying /api:', req.url, '→', proxyReq.path);
          });
          proxy.on('error', (err, req, res) => {
            console.log('❌ Proxy error /api:', err);
          });
        },
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
        secure: false,
      },
    },
    hmr: {
      overlay: false,
    },
  },
  resolve: {
    extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json'],
    alias: {
      '@': '/src',
    },
  },
  optimizeDeps: {
    include: ['react', 'react-dom'],
    entries: ['src/main.tsx', 'src/pages/Search.tsx'],
  },
  build: {
    sourcemap: true,
  },
});
