<template>
  <div class="demo-panel">
    <div class="panel-title"><span>⚙️</span>Configuration Loading</div>
    <div class="cfg-grid">
      <div class="cfg-item" v-for="item in cfgItems" :key="item.key"
           :class="{ loaded: item.loaded }">
        <div class="cfg-key">{{ item.key }}</div>
        <div class="cfg-val">
          <transition name="val-pop">
            <span v-if="item.loaded" key="v">{{ item.value }}</span>
            <span v-else key="d" class="cfg-placeholder">— — —</span>
          </transition>
        </div>
        <div class="cfg-desc">{{ item.desc }}</div>
      </div>
    </div>
    <div class="cfg-done" v-if="allLoaded">✅ All system configurations loaded</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
const cfgItems = ref([
  { key: 'safeZoneRadius', value: '1000 m',   desc: 'Privacy Zone Radius',   loaded: false },
  { key: 'alpha',          value: '0.6',       desc: 'Spatial/Text Weight', loaded: false },
  { key: 'keySize',        value: '1024 bit',  desc: 'Paillier Key Size',   loaded: false },
  { key: 'updateInterval', value: '5000 ms',   desc: 'Update Interval',     loaded: false },
  { key: 'topK',           value: '10',        desc: 'Result Count',        loaded: false },
  { key: 'queryMode',      value: 'Continuous', desc: 'Query Mode',        loaded: false },
]);
const allLoaded = computed(() => cfgItems.value.every(i => i.loaded));
onMounted(() => {
  cfgItems.value.forEach((item, idx) => {
    setTimeout(() => { item.loaded = true; }, 300 + idx * 350);
  });
});
</script>

<style scoped>
.demo-panel { padding: 32px; height: 100%; display: flex; flex-direction: column; gap: 24px; }
.panel-title { font-size: 20px; font-weight: 700; color: #60a5fa; display: flex; align-items: center; gap: 10px; }
.cfg-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.cfg-item {
  background: #0d1424; border: 1px solid #1e3a5f; border-radius: 10px;
  padding: 16px; transition: border-color 0.3s, box-shadow 0.3s; opacity: 0.4;
}
.cfg-item.loaded { border-color: #2563eb; box-shadow: 0 0 14px rgba(37,99,235,0.2); opacity: 1; }
.cfg-key { font-size: 11px; color: #64748b; margin-bottom: 6px; font-family: monospace; }
.cfg-val { font-size: 22px; font-weight: 700; color: #60a5fa; min-height: 32px; }
.cfg-placeholder { color: #1e3a5f; }
.cfg-desc { font-size: 11px; color: #475569; margin-top: 6px; }
.cfg-done { padding: 12px 20px; background: rgba(52,211,153,0.1); border: 1px solid #34d399; border-radius: 8px; color: #34d399; font-size: 14px; }
.val-pop-enter-active { transition: all 0.3s cubic-bezier(0.34,1.56,0.64,1); }
.val-pop-enter-from { opacity: 0; transform: scale(0.6); }
</style>






