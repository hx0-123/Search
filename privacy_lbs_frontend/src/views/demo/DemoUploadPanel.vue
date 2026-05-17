<template>
  <div class="demo-panel upload-panel">
    <div class="panel-title"><span>📁</span>Data Upload</div>
    <div class="upload-flow">
      <div class="flow-step" :class="{ done: phase >= 1, active: phase === 0 }">
        <div class="fs-icon">{{ phase >= 1 ? '✅' : '📄' }}</div>
        <div class="fs-body">
          <div class="fs-name">CSV File Parsing</div>
          <el-progress :percentage="phase >= 1 ? 100 : csvProgress" :stroke-width="6" :show-text="false" color="#60a5fa" />
          <div class="fs-desc">{{ phase >= 1 ? 'Parsing completed: 500 POI records' : `Parsing... ${csvProgress}%` }}</div>
        </div>
      </div>
      <div class="flow-arrow">▶</div>
      <div class="flow-step" :class="{ done: phase >= 2, active: phase === 1 }">
        <div class="fs-icon">{{ phase >= 2 ? '✅' : '👁️' }}</div>
        <div class="fs-body">
          <div class="fs-name">Data Preview</div>
          <div class="preview-table" v-if="phase >= 1">
            <div class="pt-row pt-head"><span>ID</span><span>Name</span><span>Category</span><span>Coord</span></div>
            <div class="pt-row" v-for="r in previewRows" :key="r.id">
              <span>{{ r.id }}</span><span>{{ r.name }}</span><span>{{ r.cat }}</span><span>{{ r.coord }}</span>
            </div>
          </div>
          <div class="fs-desc" v-else>Waiting for parsing to complete…</div>
        </div>
      </div>
      <div class="flow-arrow">▶</div>
      <div class="flow-step" :class="{ done: phase >= 3, active: phase === 2 }">
        <div class="fs-icon">{{ phase >= 3 ? '✅' : '🔐' }}</div>
        <div class="fs-body">
          <div class="fs-name">Paillier Encryption</div>
          <el-progress :percentage="phase >= 3 ? 100 : encProgress" :stroke-width="6" :show-text="false" color="#34d399" />
          <div class="fs-desc">{{ phase >= 3 ? 'Encryption complete: 412 ms' : phase >= 2 ? `Encrypting… ${encProgress}%` : 'Waiting for encryption…' }}</div>
        </div>
      </div>
    </div>
    <div class="upload-done" v-if="phase >= 3">
      <span>✅ 500 POI records uploaded and encrypted!</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
const phase = ref(0);
const csvProgress = ref(0);
const encProgress = ref(0);
const previewRows = [
  { id: '001', name: 'Da Dong Roast Duck', cat: 'Restaurant', coord: '116.40,39.91' },
  { id: '002', name: 'Quan Jude Peking Duck', cat: 'Restaurant', coord: '116.39,39.90' },
  { id: '003', name: 'Bian Lifeng', cat: 'Convenience Store', coord: '116.41,39.92' },
];
let timer: any = null;
onMounted(() => {
  let p = 0;
  timer = setInterval(() => {
    if (phase.value === 0) { csvProgress.value = Math.min(100, csvProgress.value + 8); if (csvProgress.value >= 100) phase.value = 1; }
    else if (phase.value === 1) { setTimeout(() => { phase.value = 2; }, 600); phase.value = 1.5 as any; }
    else if (phase.value === 2) { encProgress.value = Math.min(100, encProgress.value + 6); if (encProgress.value >= 100) phase.value = 3; }
  }, 80);
});
onUnmounted(() => clearInterval(timer));
</script>

<style scoped>
.demo-panel { padding: 32px; height: 100%; display: flex; flex-direction: column; gap: 24px; }
.panel-title { font-size: 20px; font-weight: 700; color: #60a5fa; display: flex; align-items: center; gap: 10px; }
.upload-flow { display: flex; align-items: flex-start; gap: 12px; flex-wrap: wrap; }
.flow-step {
  flex: 1; min-width: 180px; background: #0d1424; border: 1px solid #1e3a5f;
  border-radius: 10px; padding: 16px; display: flex; gap: 12px;
  transition: border-color 0.3s, box-shadow 0.3s; opacity: 0.5;
}
.flow-step.active { border-color: #60a5fa; box-shadow: 0 0 16px rgba(96,165,250,0.2); opacity: 1; }
.flow-step.done   { border-color: #34d399; opacity: 1; }
.fs-icon { font-size: 24px; flex-shrink: 0; }
.fs-body { flex: 1; display: flex; flex-direction: column; gap: 6px; }
.fs-name { font-size: 13px; font-weight: 600; color: #e2e8f0; }
.fs-desc { font-size: 11px; color: #64748b; }
.flow-arrow { font-size: 20px; color: #1e3a5f; align-self: center; }
.preview-table { font-size: 10px; }
.pt-row { display: grid; grid-template-columns: 36px 80px 60px 80px; gap: 4px; padding: 2px 0; border-bottom: 1px solid #1e293b; color: #94a3b8; }
.pt-head { color: #60a5fa; font-weight: 700; }
.upload-done { padding: 12px 20px; background: rgba(52,211,153,0.1); border: 1px solid #34d399; border-radius: 8px; color: #34d399; font-size: 14px; }
</style>






