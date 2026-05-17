import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import en from 'element-plus/dist/locale/en.mjs'

import App from './App.vue'
import router from './router'

const app = createApp(App)

// Register Element Plus icons (defer significantly to avoid blocking)
// CRITICAL: Register icons in batches to prevent blocking
const registerIcons = () => {
  const entries = Object.entries(ElementPlusIconsVue);
  const batchSize = 10; // Register 10 icons at a time
  
  let index = 0;
  const registerBatch = () => {
    const end = Math.min(index + batchSize, entries.length);
    for (let i = index; i < end; i++) {
      const [key, component] = entries[i];
      app.component(key, component);
    }
    index = end;
    
    if (index < entries.length) {
      // Use requestAnimationFrame for next batch to avoid blocking
      requestAnimationFrame(registerBatch);
    }
  };
  
  // Start registration after a delay
  setTimeout(() => {
    registerBatch();
  }, 200);
}

// Defer icon registration significantly to allow app to mount first
if ('requestIdleCallback' in window) {
  (window as any).requestIdleCallback(registerIcons, { timeout: 1000 });
} else {
  setTimeout(registerIcons, 200);
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, {
  locale: en,
})

// CRITICAL: Mount app immediately - don't wait for anything
app.mount('#app')
