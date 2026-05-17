<template>
  <div class="db-wrap">
    <!-- Top bar -->
    <div class="db-topbar">
      <div class="db-title">Node Monitoring</div>
      <div class="db-topbar-right">
        <span class="db-ts">{{ lastUpdated }}</span>
        <el-button :icon="Refresh" circle :loading="loading" @click="load" />
      </div>
    </div>

    <el-alert v-if="errorMsg" :title="errorMsg" type="error" show-icon closable @close="errorMsg=''"
      style="margin:0 24px 12px" />

    <div class="db-body" v-loading="loading">
      <!-- Summary cards -->
      <div class="db-summary">
        <div class="sum-card" v-for="s in summaryCards" :key="s.label">
          <div class="sum-val" :style="{ color: s.color }">{{ s.value }}</div>
          <div class="sum-label">{{ s.label }}</div>
        </div>
            </div>

      <!-- Cloud node -->
      <div class="db-section-title">CLOUD NODE</div>
      <div class="node-card cloud-card" v-if="cloudNode">
        <div class="node-header">
          <span class="node-dot" :class="'dot-' + cloudNode.status" />
          <span class="node-id">{{ cloudNode.node_id }}</span>
          <span class="node-name">{{ cloudNode.node_name }}</span>
          <el-tag size="small" effect="dark" :type="cloudNode.status === 'active' ? 'success' : 'danger'">
            {{ cloudNode.status === 'active' ? 'Online' : 'Offline' }}
          </el-tag>
        </div>
        <div class="node-metrics">
          <div class="nm-item">
            <span class="nm-label">CPU</span>
            <el-progress :percentage="cloudNode.cpu_percent" :stroke-width="6" :show-text="false"
              :color="cloudNode.cpu_percent > 80 ? '#f87171' : '#38bdf8'" />
            <span class="nm-val">{{ cloudNode.cpu_percent }}%</span>
          </div>
          <div class="nm-item">
              <span class="nm-label">Memory</span>
            <el-progress :percentage="cloudNode.memory_percent" :stroke-width="6" :show-text="false"
              :color="cloudNode.memory_percent > 80 ? '#f87171' : '#a78bfa'" />
            <span class="nm-val">{{ cloudNode.memory_percent }}%</span>
          </div>
          <div class="nm-stat">
            <span>Active Queries</span><strong>{{ cloudNode.active_tasks }}</strong>
          </div>
          <div class="nm-stat">
            <span>Total Processed</span><strong>{{ cloudNode.total_tasks_processed }}</strong>
          </div>
          <div class="nm-stat">
            <span>Address</span><strong class="mono">{{ cloudNode.host }}:{{ cloudNode.port }}</strong>
          </div>
            </div>
            </div>

      <!-- Fog nodes list -->
      <div class="db-section-title">FOG NODES</div>
      <div class="fog-grid">
        <div class="node-card" v-for="node in fogNodes" :key="node.node_id">
          <div class="node-header">
            <span class="node-dot" :class="'dot-' + node.status" />
            <span class="node-id">{{ node.node_id }}</span>
            <span class="node-name">{{ node.node_name }}</span>
            <el-tag size="small" effect="dark" :type="node.status === 'active' ? 'success' : 'info'">
              {{ node.status === 'active' ? 'Online' : 'Offline' }}
            </el-tag>
            </div>
          <div class="node-metrics">
            <div class="nm-item">
              <span class="nm-label">CPU</span>
              <el-progress :percentage="node.cpu_percent" :stroke-width="5" :show-text="false"
                :color="node.cpu_percent > 80 ? '#f87171' : '#34d399'" />
              <span class="nm-val">{{ node.cpu_percent }}%</span>
            </div>
            <div class="nm-item">
              <span class="nm-label">Memory</span>
              <el-progress :percentage="node.memory_percent" :stroke-width="5" :show-text="false"
                :color="node.memory_percent > 80 ? '#f87171' : '#fbbf24'" />
              <span class="nm-val">{{ node.memory_percent }}%</span>
            </div>
            <div class="nm-stat"><span>Active Tasks</span><strong>{{ node.active_tasks }}</strong></div>
            <div class="nm-stat"><span>Reserved Tasks</span><strong>{{ node.reserved_tasks ?? 0 }}</strong></div>
            <div class="nm-stat"><span>Address</span><strong class="mono">{{ node.host }}</strong></div>
          </div>
        </div>
      </div>
      <!-- Global architecture logs - RECENT QUERIES -->
      <div class="db-section-title rq-title-row">
        RECENT QUERIES
        <span class="rq-live-dot"></span>
        <span class="rq-live-label">LIVE</span>
        <span class="rq-count">{{ demoApp.systemLogs.length }} records</span>
        <button class="rq-clear-btn" @click="demoApp.clearSystemLogs()">Clear</button>
      </div>
      <div class="arch-log-card">
        <div v-if="demoApp.systemLogs.length === 0" class="arch-log-empty">
          <span class="arch-empty-icon">📡</span>
          <span>No query logs · Please initiate encrypted query from 【Query Map】</span>
        </div>
        <div v-else class="arch-log-list">
          <div
            v-for="log in demoApp.systemLogs"
            :key="log.id"
            class="arch-log-row"
          >
            <span class="arch-log-ts">{{ fmtLogTime(log.timestamp) }}</span>
            <span class="arch-log-node" :class="'node-tag-' + nodeClass(log.node)">{{ log.node }}</span>
            <span class="arch-log-action">{{ log.action }}</span>
            <span class="arch-log-status" :class="'status-' + log.status">
              {{ log.status === 'success' ? '✓' : log.status === 'error' ? '✗' : '…' }}
            </span>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Refresh, Loading } from '@element-plus/icons-vue'
import { getDashboardStats } from '@/services/metrics.service'
import type { NodeInfo, NodeStatusResponse } from '@/services/metrics.service'
import { api } from '@/services/api.client'
import { useDemoAppStore } from '@/stores/useDemoStore'
import type { LogNode } from '@/stores/useDemoStore'
import dayjs from 'dayjs'

const demoApp = useDemoAppStore()

const loading    = ref(false)
const errorMsg   = ref('')
const lastUpdated = ref('—')
const data       = ref<NodeStatusResponse | null>(null)

const cloudNode  = computed(() => data.value?.cloud_node ?? null)
const fogNodes   = computed(() => data.value?.fog_nodes ?? [])

const summaryCards = computed(() => {
  const s = data.value?.summary
  return [
    { label: 'Total Nodes',       value: s?.total_nodes ?? '—',      color: '#38bdf8' },
    { label: 'Active Fog Nodes',     value: s?.active_fog_nodes ?? '—', color: '#34d399' },
    { label: 'Current Active Tasks',   value: s?.active_tasks ?? '—',     color: '#fbbf24' },
    { label: '24h Completed Queries',   value: s?.completed_24h ?? '—',    color: '#a78bfa' },
  ]
})

async function load() {
  loading.value  = true
  errorMsg.value = ''
  try {
    data.value     = await getDashboardStats()
    lastUpdated.value = dayjs().format('HH:mm:ss')
  } catch (e: any) {
    errorMsg.value = `Loading failed：${e?.message ?? 'Please confirm backend is running (http://127.0.0.1:8000)'}`
  } finally {
    loading.value = false
  }
  // Load recent queries synchronously
  loadRecentQueries()
}

// ── Recent query history ─────────────────────────────────────────
interface RecentQuery {
  query_id: string
  keyword: string
  status: string
  duration_ms: number | null
  created_at: string
}
const recentQueries  = ref<RecentQuery[]>([])
const recentLoading = ref(false)

async function loadRecentQueries() {
  recentLoading.value = true
  try {
    const res: any = await api.get('/query/history/', { params: { page: 1, page_size: 5 } })
    recentQueries.value = (res?.records ?? []).slice(0, 5)
  } catch {
    recentQueries.value = []
  } finally {
    recentLoading.value = false
  }
}

function fmtTime(t: string) {
  return t ? dayjs(t).format('MM-DD HH:mm') : '—'
}

// ── Architecture log helper functions ──────────────────────────────────────
function nodeClass(node: LogNode): string {
  if (node === 'User')      return 'user';
  if (node === 'Cloud C1')  return 'c1';
  if (node === 'Cloud C2')  return 'c2';
  if (node === 'Fog Array') return 'fog';
  return 'user';
}

function fmtLogTime(t: Date): string {
  return dayjs(t).format('HH:mm:ss');
}

// Auto refresh every 30 seconds
let timer: ReturnType<typeof setInterval> | null = null
onMounted(() => { load(); timer = setInterval(load, 30_000) })
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.db-wrap { min-height: 100%; background: #0d1117; display: flex; flex-direction: column; font-family: 'PingFang SC','Microsoft YaHei',sans-serif; }
.db-topbar { display: flex; align-items: center; justify-content: space-between; padding: 16px 24px; border-bottom: 1px solid #1e293b; }
.db-title { font-size: 20px; font-weight: 700; color: #f1f5f9; letter-spacing: 1px; }
.db-topbar-right { display: flex; align-items: center; gap: 10px; }
.db-ts { font-size: 12px; color: #475569; font-family: monospace; }
.db-body { flex: 1; padding: 20px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 20px; }

.db-summary { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; }
.sum-card { background: #1e222d; border: 1px solid #1e293b; border-radius: 8px; padding: 16px 20px; }
.sum-val { font-size: 32px; font-weight: 700; font-variant-numeric: tabular-nums; }
.sum-label { font-size: 12px; color: #64748b; margin-top: 4px; }

.db-section-title { font-size: 11px; font-weight: 700; letter-spacing: 2px; color: #334155; text-transform: uppercase; }

.node-card { background: #1e222d; border: 1px solid #1e293b; border-radius: 10px; padding: 16px 20px; }
.cloud-card { border-color: rgba(56,189,248,.3); }
.node-header { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.node-dot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }
.dot-active   { background: #34d399; box-shadow: 0 0 6px #34d399; }
.dot-inactive { background: #475569; }
.dot-error    { background: #f87171; box-shadow: 0 0 6px #f87171; }
.node-id   { font-family: monospace; font-weight: 700; color: #38bdf8; font-size: 15px; }
.node-name { color: #64748b; font-size: 13px; flex: 1; }

.node-metrics { display: flex; flex-direction: column; gap: 10px; }
.nm-item { display: flex; align-items: center; gap: 10px; font-size: 12px; }
.nm-label { width: 36px; color: #475569; flex-shrink: 0; }
.nm-val { width: 36px; text-align: right; color: #94a3b8; font-variant-numeric: tabular-nums; }
.nm-stat { display: flex; justify-content: space-between; font-size: 12px; color: #475569; }
.nm-stat strong { color: #94a3b8; }

.fog-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.mono { font-family: monospace; }

/* Recent queries table */
.recent-card { background: #1e222d; border: 1px solid #1e293b; border-radius: 10px; padding: 16px 20px; }
.recent-loading { color: #475569; font-size: 13px; display: flex; align-items: center; gap: 8px; padding: 16px 0; }
.recent-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.recent-table th { color: #334155; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; padding: 6px 8px; border-bottom: 1px solid #1e293b; text-align: left; }
.recent-table td { padding: 8px 8px; border-bottom: 1px solid #0d1117; color: #94a3b8; vertical-align: middle; }
.recent-table tr:last-child td { border-bottom: none; }
.recent-table tr:hover td { background: rgba(56,189,248,0.04); }

/* ══ Global architecture logs ══ */
.rq-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.rq-live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #34d399;
  box-shadow: 0 0 6px #34d399;
  animation: livePulse 1.2s ease-in-out infinite;
  flex-shrink: 0;
}
@keyframes livePulse {
  0%,100% { opacity: 1; box-shadow: 0 0 6px #34d399; }
  50%      { opacity: 0.4; box-shadow: 0 0 2px #34d399; }
}
.rq-live-label {
  font-size: 9px;
  font-weight: 700;
  color: #34d399;
  letter-spacing: 1px;
  font-family: 'JetBrains Mono', monospace;
}
.rq-count {
  font-size: 11px;
  color: #475569;
  margin-left: 4px;
}
.rq-clear-btn {
  margin-left: auto;
  font-size: 10px;
  color: #475569;
  background: transparent;
  border: 1px solid #1e293b;
  border-radius: 4px;
  padding: 2px 8px;
  cursor: pointer;
  transition: all 0.15s;
}
.rq-clear-btn:hover { color: #f87171; border-color: rgba(248,113,113,0.3); }

.arch-log-card {
  background: #0d1117;
  border: 1px solid #1e293b;
  border-radius: 10px;
  overflow: hidden;
}
.arch-log-empty {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 24px 20px;
  font-size: 13px;
  color: #334155;
}
.arch-empty-icon { font-size: 20px; }

.arch-log-list {
  display: flex;
  flex-direction: column;
  max-height: 340px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: #1e293b transparent;
}
.arch-log-list::-webkit-scrollbar { width: 4px; }
.arch-log-list::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 2px; }

.arch-log-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 9px 16px;
  border-bottom: 1px solid rgba(30,41,59,0.6);
  animation: logSlideIn 0.25s ease;
  font-size: 12px;
}
.arch-log-row:last-child { border-bottom: none; }
.arch-log-row:hover { background: rgba(56,189,248,0.03); }
@keyframes logSlideIn {
  from { opacity: 0; transform: translateX(-8px); }
  to   { opacity: 1; transform: translateX(0); }
}

.arch-log-ts {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #334155;
  flex-shrink: 0;
  padding-top: 1px;
  min-width: 62px;
}

.arch-log-node {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 4px;
  flex-shrink: 0;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.5px;
  white-space: nowrap;
}
/* Node colors */
.node-tag-user {
  background: rgba(167,139,250,0.15);
  color: #a78bfa;
  border: 1px solid rgba(167,139,250,0.25);
}
.node-tag-c1 {
  background: rgba(56,189,248,0.15);
  color: #38bdf8;
  border: 1px solid rgba(56,189,248,0.25);
}
.node-tag-c2 {
  background: rgba(52,211,153,0.15);
  color: #34d399;
  border: 1px solid rgba(52,211,153,0.25);
}
.node-tag-fog {
  background: rgba(251,191,36,0.12);
  color: #fbbf24;
  border: 1px solid rgba(251,191,36,0.22);
}

.arch-log-action {
  flex: 1;
  color: #64748b;
  line-height: 1.6;
  font-size: 11px;
}

.arch-log-status {
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
  padding-top: 1px;
}
.status-success { color: #34d399; }
.status-error   { color: #f87171; }
.status-pending { color: #fbbf24; }

/* ── Recent query history ── */
.recent-queries-card {
  background: #1e222d;
  border: 1px solid #1e293b;
  border-radius: 10px;
  padding: 14px 18px;
  overflow-x: auto;
}
.rq-loading { font-size: 13px; color: #475569; padding: 8px 0; }
.rq-table { display: flex; flex-direction: column; gap: 0; min-width: 500px; }
.rq-header {
  display: grid;
  grid-template-columns: 130px 1fr 80px 90px 110px;
  gap: 8px;
  padding: 6px 8px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
  color: #334155;
  text-transform: uppercase;
  border-bottom: 1px solid #1e293b;
}
.rq-row {
  display: grid;
  grid-template-columns: 130px 1fr 80px 90px 110px;
  gap: 8px;
  align-items: center;
  padding: 7px 8px;
  font-size: 12px;
  color: #94a3b8;
  border-bottom: 1px solid rgba(30,41,59,0.5);
  transition: background .15s;
}
.rq-row:last-child { border-bottom: none; }
.rq-row:hover { background: rgba(56,189,248,0.04); }
.rq-time { color: #475569; font-variant-numeric: tabular-nums; }
</style>
