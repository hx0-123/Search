<template>
  <div id="app">
    <router-view v-if="routerReady" />
    <div v-else style="display: flex; align-items: center; justify-content: center; height: 100vh;">
      <p>加载中...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const routerReady = ref(false);

onMounted(() => {
  console.log('App 根组件已挂载');
  router.isReady().then(() => {
    console.log('路由已就绪');
    routerReady.value = true;
  }).catch((error) => {
    console.error('路由初始化失败:', error);
    routerReady.value = true; // 即使失败也显示内容
  });
});
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  width: 100%;
  height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol',
    'Noto Color Emoji';
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  margin: 0;
  padding: 0;
  overflow: hidden;
}
</style>