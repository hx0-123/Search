import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    // 只在开发环境启用DevTools
    process.env.NODE_ENV === 'development' && vueDevTools(),
  ].filter(Boolean),
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  build: {
    // 生产环境构建优化
    target: 'es2015',
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false, // 生产环境不生成sourcemap
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // 移除console
        drop_debugger: true,
      },
    },
    rollupOptions: {
      output: {
        // 代码分割
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'element-plus': ['element-plus', '@element-plus/icons-vue'],
          'mapbox': ['mapbox-gl'],
        },
      },
    },
    chunkSizeWarningLimit: 1000, // 块大小警告限制
  },
  server: {
    port: 5173,
    host: true, // 允许外部访问
    proxy: {
      // 开发环境代理（可选）
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
