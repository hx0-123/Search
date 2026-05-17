<template>
  <div class="demo-panel">
    <div class="panel-title"><span>🔍</span>Initiate Query</div>
    <div class="query-terminal">
      <div class="terminal-bar"><span>●</span><span>●</span><span>●</span><span class="t-title">Query Terminal</span></div>
      <div class="terminal-body">
        <div class="t-line" v-for="line in visibleLines" :key="line.id" :class="line.type">
          <span class="t-prompt" v-if="line.prompt">></span> {{ line.text }}
        </div>
        <div class="t-cursor" v-if="!done">▋</div>
      </div>
    </div>
    <div class="query-params" v-if="done">
      <div class="qp-item"><span class="qp-k">Keyword</span><span class="qp-v">Restaurant</span></div>
      <div class="qp-item"><span class="qp-k">Location</span><span class="qp-v">116.4074, 39.9042</span></div>
      <div class="qp-item"><span class="qp-k">Top-K</span><span class="qp-v">10</span></div>
      <div class="qp-item"><span class="qp-k">alpha</span><span class="qp-v">0.6</span></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
const done = ref(false);
const visibleLines = ref<{ id: number; text: string; type: string; prompt?: boolean }[]>([]);
const LINES = [
  { type: 'comment', text: '# SKTAQ Continuous Query System v2.0', prompt: false },
  { type: 'cmd',     text: 'sktaq init --mode continuous', prompt: true },
  { type: 'out',     text: '✓ Connected to server ws://localhost:8000/ws', prompt: false },
  { type: 'cmd',     text: 'sktaq query --keyword "restaurant" --k 10 --alpha 0.6', prompt: true },
  { type: 'out',     text: '✓ Location encrypted (Paillier): enc(116.4074, 39.9042)', prompt: false },
  { type: 'out',     text: '✓ Keyword hashed: hash("restaurant") = 0x4f2a...', prompt: false },
  { type: 'success', text: '→ Query submitted, Query ID: Q-2026031014', prompt: false },
];
onMounted(() => {
  LINES.forEach((line, idx) => {
    setTimeout(() => {
      visibleLines.value.push({ ...line, id: idx });
      if (idx === LINES.length - 1) done.value = true;
    }, 300 + idx * 380);
  });
});
</script>

<style scoped>
.demo-panel { padding: 32px; display: flex; flex-direction: column; gap: 20px; }
.panel-title { font-size: 20px; font-weight: 700; color: #60a5fa; display: flex; align-items: center; gap: 10px; }
.query-terminal { background: #020817; border: 1px solid #1e3a5f; border-radius: 10px; overflow: hidden; }
.terminal-bar { background: #111827; padding: 8px 14px; display: flex; gap: 6px; align-items: center; }
.terminal-bar span { width: 12px; height: 12px; border-radius: 50%; background: #374151; }
.terminal-bar span:nth-child(1) { background: #ef4444; }
.terminal-bar span:nth-child(2) { background: #f59e0b; }
.terminal-bar span:nth-child(3) { background: #10b981; }
.t-title { margin-left: auto; font-size: 11px; color: #475569; }
.terminal-body { padding: 16px; font-family: monospace; font-size: 13px; min-height: 180px; display: flex; flex-direction: column; gap: 6px; }
.t-line { display: flex; gap: 8px; align-items: baseline; }
.t-line.comment { color: #475569; }
.t-line.cmd     { color: #e2e8f0; }
.t-line.out     { color: #64748b; padding-left: 16px; }
.t-line.success { color: #34d399; font-weight: 600; }
.t-prompt { color: #60a5fa; font-weight: 700; }
.t-cursor { color: #60a5fa; animation: blink 1s step-end infinite; }
@keyframes blink { 50% { opacity: 0; } }
.query-params { display: flex; gap: 12px; flex-wrap: wrap; }
.qp-item { background: #0d1424; border: 1px solid #2563eb; border-radius: 8px; padding: 10px 16px; display: flex; flex-direction: column; gap: 4px; min-width: 120px; }
.qp-k { font-size: 10px; color: #64748b; }
.qp-v { font-size: 18px; font-weight: 700; color: #60a5fa; }
</style>






