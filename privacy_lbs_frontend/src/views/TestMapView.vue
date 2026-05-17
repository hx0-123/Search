<!--
  Minimal map test page
  Only renders a button and map component for troubleshooting
-->
<template>
  <div class="test-map-view">
    <div class="test-controls">
      <button @click="testClick">Test Button (Click me!)</button>
      <p>If this button can be clicked, the page is responsive.</p>
      <p>Map Status: {{ mapStatus }}</p>
    </div>
    <div class="test-map-container">
      <SecureMap />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import SecureMap from '@/components/map/SecureMap.vue';

const mapStatus = ref('Initializing...');

function testClick() {
  alert('Button clicked! Page is responsive.');
  console.log('[TestMapView] Button clicked - page is responsive');
}

onMounted(() => {
  console.log('[TestMapView] Component mounted');
  mapStatus.value = 'Loaded';
  
  setTimeout(() => {
    mapStatus.value = 'Ready';
    console.log('[TestMapView] Page should be ready now');
  }, 2000);
});
</script>

<style scoped>
.test-map-view {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.test-controls {
  padding: 20px;
  background: #f0f0f0;
  border-bottom: 2px solid #ccc;
}

.test-controls button {
  padding: 10px 20px;
  font-size: 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.test-controls button:hover {
  background: #0056b3;
}

.test-map-container {
  flex: 1;
  width: 100%;
  height: 100%;
}
</style>
