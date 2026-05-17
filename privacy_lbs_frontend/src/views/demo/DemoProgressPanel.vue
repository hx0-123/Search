<template>
  <div class="demo-panel">
    <div class="panel-title"><span>⚡</span>Query Process Visualization</div>
    <div class="stages">
      <div
        v-for="s in stages" :key="s.key"
        class="stage-row"
        :class="{ active: s.active, done: s.done }"
      >
        <div class="s-icon">{{ s.done ? '✅' : s.active ? '⚡' : '○' }}</div>
        <div class="s-body">
          <div class="s-top">
            <span class="s-name">{{ s.label }}</span>
            <span class="s-meta">{{ s.meta }}</span>
          </div>
          <el-progress :percentage="s.progress" :stroke-width="8" :show-text="false" :color="s.color" />
          <div class="s-desc">{{ s.desc }}</div>
        </div>
      </div>
    </div>
    <div class="elapsed">Total Time: <span>{{ elapsed }} ms</span></div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue';
const elapsed = ref(0);
const stages = reactive([
  { key: 'enc',  label: 'Stage 1: Location/Keyword Encryption', color: '#60a5fa', progress: 0, active: false, done: false, meta: '',          desc: 'Waiting to start…' },
  { key: 'prune',label: 'Stage 2: Cloud Spatial Pruning',   color: '#f59e0b', progress: 0, active: false, done: false, meta: '',          desc: 'Waiting…' },
  { key: 'score',label: 'Stage 3: Fog Node Scoring',     color: '#a78bfa', progress: 0, active: false, done: false, meta: '0/5 nodes',  desc: 'Waiting…' },
  { key: 'agg',  label: 'Stage 4: Aggregation & Sorting',     color: '#34d399', progress: 0, active: false, done: false, meta: '',          desc: 'Waiting…' },
]);

let timer: any;
onMounted(() => {
  let t = 0;
  timer = setInterval(() => {
    t += 80;
    elapsed.value = t;
    if (t < 800) {
      stages[0].active = true; stages[0].progress = Math.min(100, Math.round(t / 8)); stages[0].desc = 'Encrypting location and keywords…';
    } else if (t === 800) { stages[0].progress = 100; stages[0].active = false; stages[0].done = true; stages[0].meta = '96 ms'; stages[0].desc = 'Encryption complete'; }
    if (t >= 800 && t < 2000) {
      stages[1].active = true; stages[1].progress = Math.min(100, Math.round((t - 800) / 12)); stages[1].desc = 'Cloud filtering (pruning rate: 96%)'; stages[1].meta = '5000 → ' + Math.max(200, 5000 - Math.round((t-800)*4)) ;
    } else if (t === 2000) { stages[1].progress = 100; stages[1].active = false; stages[1].done = true; stages[1].meta = '5000 → 200'; stages[1].desc = 'Pruning complete'; }
    if (t >= 2000 && t < 3200) {
      stages[2].active = true; const n = Math.min(5, Math.floor((t - 2000) / 240)); stages[2].completedNodes = n; stages[2].progress = Math.round(n / 5 * 100); stages[2].meta = n + '/5 nodes'; stages[2].desc = 'Fog nodes computing scores…';
    } else if (t === 3200) { stages[2].progress = 100; stages[2].active = false; stages[2].done = true; stages[2].meta = '5/5 nodes'; stages[2].desc = 'Scoring complete'; }
    if (t >= 3200 && t < 3800) {
      stages[3].active = true; stages[3].progress = Math.min(100, Math.round((t-3200) / 6)); stages[3].desc = 'Sorting and preparing display…';
    } else if (t >= 3800) { stages[3].progress = 100; stages[3].active = false; stages[3].done = true; stages[3].desc = 'Sorting complete, ready to display'; stages[3].meta = 'Top-10'; clearInterval(timer); }
  }, 80);
});
onUnmounted(() => clearInterval(timer));
</script>

<style scoped>
.demo-panel { padding: 32px; display: flex; flex-direction: column; gap: 16px; }
.panel-title { font-size: 20px; font-weight: 700; color: #60a5fa; display: flex; align-items: center; gap: 10px; }
.stages { display: flex; flex-direction: column; gap: 12px; }
.stage-row {
  display: flex; gap: 14px; align-items: flex-start;
  padding: 14px 16px; border-radius: 10px;
  background: #0d1424; border: 1px solid #1e3a5f;
  transition: all 0.25s; opacity: 0.45;
}
.stage-row.active { border-color: #60a5fa; box-shadow: 0 0 16px rgba(96,165,250,0.25); opacity: 1; }
.stage-row.done   { border-color: #34d399; opacity: 1; }
.s-icon { font-size: 20px; padding-top: 2px; flex-shrink: 0; }
.s-body { flex: 1; display: flex; flex-direction: column; gap: 6px; }
.s-top  { display: flex; justify-content: space-between; }
.s-name { font-size: 14px; font-weight: 600; color: #e2e8f0; }
.s-meta { font-size: 11px; color: #64748b; font-variant-numeric: tabular-nums; }
.s-desc { font-size: 11px; color: #64748b; }
.elapsed { font-size: 13px; color: #475569; text-align: right; }
.elapsed span { color: #60a5fa; font-weight: 700; font-variant-numeric: tabular-nums; }
</style>






