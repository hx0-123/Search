<template>
  <div class="demo-panel">
    <div class="panel-title"><span>📊</span>Performance Summary</div>
    <div class="summary-grid">
      <div
        v-for="kpi in kpis" :key="kpi.label"
        class="summary-kpi"
        :class="{ visible: kpi.visible }"
      >
        <div class="kpi-icon">{{ kpi.icon }}</div>
        <div class="kpi-val" :style="{ color: kpi.color }">{{ kpi.display }}{{ kpi.suffix }}</div>
        <div class="kpi-label">{{ kpi.label }}</div>
        <div class="kpi-compare good">{{ kpi.compare }}</div>
      </div>
    </div>

    <div class="compare-section">
      <div class="cs-title">Safe Zone ON vs OFF — Query Latency Comparison</div>
      <div class="cs-bars">
        <div class="cs-row">
          <span class="cs-label">✅ Safe Zone Enabled</span>
          <el-progress :percentage="7" :stroke-width="16" :show-text="false" color="#34d399" style="flex:1" />
          <span class="cs-val" style="color:#34d399">62 ms</span>
        </div>
        <div class="cs-row">
          <span class="cs-label">❌ Safe Zone Disabled</span>
          <el-progress :percentage="100" :stroke-width="16" :show-text="false" color="#ef4444" style="flex:1" />
          <span class="cs-val" style="color:#ef4444">850 ms</span>
        </div>
      </div>
      <div class="cs-note">
        <span>🚀 Safe Zone cache hit speed improvement <strong>13.7×</strong>!</span>
      </div>
    </div>

    <div class="summary-footer">
      <el-tag type="success" size="large" effect="dark">✅ SKTAQ System Demo Complete</el-tag>
      <span class="footer-desc">Privacy Protection · Efficient Query · Visual Analysis</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const kpis = ref([
  { icon: '⚡', label: 'Avg Latency',          val: 182,  display: 0, suffix: ' ms', color: '#60a5fa', compare: '4.7× faster than baseline', visible: false },
  { icon: '🛡️', label: 'Safe Zone Hit Rate',  val: 82,   display: 0, suffix: '%',   color: '#34d399', compare: 'High cache efficiency', visible: false },
  { icon: '🔐', label: 'Encryption Overhead', val: 5.2,  display: 0, suffix: '%',   color: '#f59e0b', compare: 'Acceptable overhead',   visible: false },
  { icon: '📍', label: 'Avg Results',         val: 10,   display: 0, suffix: '',    color: '#a78bfa', compare: 'Top-K = 10',          visible: false },
  { icon: '🕒', label: 'P95 Latency',         val: 320,  display: 0, suffix: ' ms', color: '#e2e8f0', compare: '< 500ms SLA',       visible: false },
  { icon: '🔄', label: 'Total Queries',       val: 24,   display: 0, suffix: '',    color: '#64748b', compare: 'This session',      visible: false },
]);

onMounted(() => {
  kpis.value.forEach((kpi, idx) => {
    setTimeout(() => {
      kpi.visible = true;
      let cur = 0;
      const target = kpi.val;
      const steps = 24;
      const step = target / steps;
      const t = setInterval(() => {
        cur = Math.min(target, cur + step);
        kpi.display = parseFloat(cur.toFixed(1));
        if (cur >= target) clearInterval(t);
      }, 40);
    }, 200 + idx * 280);
  });
});
</script>

<style scoped>
.demo-panel { padding: 32px; display: flex; flex-direction: column; gap: 20px; height: 100%; overflow-y: auto; }
.panel-title { font-size: 20px; font-weight: 700; color: #60a5fa; display: flex; align-items: center; gap: 10px; flex-shrink: 0; }

.summary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.summary-kpi {
  background: #0d1424; border: 1px solid #1e3a5f; border-radius: 12px;
  padding: 20px 16px; text-align: center;
  opacity: 0; transform: translateY(16px);
  transition: all 0.45s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.summary-kpi.visible { opacity: 1; transform: translateY(0); }
.kpi-icon  { font-size: 22px; margin-bottom: 8px; }
.kpi-val   { font-size: 26px; font-weight: 700; font-variant-numeric: tabular-nums; }
.kpi-label { font-size: 11px; color: #64748b; margin-top: 4px; }
.kpi-compare {
  font-size: 10px; margin-top: 6px;
  padding: 2px 8px; border-radius: 10px; display: inline-block;
}
.kpi-compare.good { background: rgba(52,211,153,0.12); color: #34d399; }

.compare-section {
  background: #0d1424; border: 1px solid #1e3a5f;
  border-radius: 12px; padding: 20px;
}
.cs-title  { font-size: 13px; font-weight: 600; color: #94a3b8; margin-bottom: 14px; }
.cs-bars   { display: flex; flex-direction: column; gap: 12px; }
.cs-row    { display: flex; align-items: center; gap: 12px; }
.cs-label  { font-size: 12px; color: #94a3b8; min-width: 140px; flex-shrink: 0; }
.cs-val    { font-size: 13px; font-weight: 700; font-variant-numeric: tabular-nums; min-width: 60px; text-align: right; }
.cs-note   { margin-top: 14px; padding: 10px 14px; background: rgba(52,211,153,0.08); border-radius: 8px; font-size: 13px; color: #94a3b8; }
.cs-note strong { color: #34d399; }

.summary-footer { display: flex; align-items: center; gap: 16px; flex-shrink: 0; }
.footer-desc    { font-size: 13px; color: #475569; }
</style>






