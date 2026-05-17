<template>
  <div id="app">
    <!-- CRITICAL: Always show router-view immediately, don't wait for router ready -->
    <!-- This prevents the "Loading..." screen from blocking the UI -->
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

onMounted(() => {
  // CRITICAL: Ensure page is responsive by yielding to browser immediately
  // This allows F12 and other keyboard shortcuts to work
  if ('requestIdleCallback' in window) {
    (window as any).requestIdleCallback(() => {
      setTimeout(() => {
        console.log('App root component mounted');
      }, 0);
    }, { timeout: 100 });
  } else {
    setTimeout(() => {
      console.log('App root component mounted');
    }, 0);
  }
  
  // Initialize router asynchronously (non-blocking)
  // Don't block UI rendering - router will work even if not immediately ready
  setTimeout(() => {
    router.isReady().then(() => {
      setTimeout(() => {
        console.log('Router ready');
      }, 0);
    }).catch((error) => {
      setTimeout(() => {
        console.error('Router initialization failed:', error);
      }, 0);
      // Don't block UI - continue anyway
    });
  }, 100);
});
</script>

<style>
/* ── Global root font: Base size, all rem/em units follow automatically ── */
html {
  font-size: 16px;
}

/* ── Element Plus CSS variable overrides: Uniform component font size scaling ── */
:root {
  --el-font-size-base:        15px;
  --el-font-size-small:       13px;
  --el-font-size-extra-small: 12px;
  --el-font-size-medium:      16px;
  --el-font-size-large:       18px;
  --el-font-size-extra-large: 20px;

  /* Line height for tables, forms, menus also increased appropriately */
  --el-component-size:        36px;
  --el-component-size-small:  28px;
  --el-component-size-large:  44px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  width: 100%;
  height: 100vh;
  overflow: hidden; /* Overall container doesn't scroll, each page decides */
  font-size: 15px;
  font-family: 'PingFang SC', 'Microsoft YaHei', -apple-system, BlinkMacSystemFont,
    'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  margin: 0;
  padding: 0;
  overflow: hidden;
}
</style>