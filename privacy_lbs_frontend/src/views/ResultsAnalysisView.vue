<template>
  <div class="rav-root">
    <!-- Top bar -->
    <div class="rav-topbar">
      <div class="rav-title">Result Analysis</div>
      <div class="rav-filters">
        <el-select v-model="days" style="width:130px" @change="load">
          <el-option label="Last 1 day" :value="1" />
        <el-option label="Last 7 days" :value="7" />
        <el-option label="Last 30 days" :value="30" />
        </el-select>
        <el-button :icon="Refresh" circle :loading="loading" @click="load" />
        <span class="filter-label">Total {{ statsData?.total_queries ?? 0 }} queries</span>
      </div>
    </div>

    <el-alert v-if="errorMsg" :title="errorMsg" type="error" show-icon closable @close="errorMsg=''"
      style="margin:0 20px 12px" />

    <!-- Empty state -->
    <div v-if="!loading && isEmpty" class="rav-empty">
      <el-empty description="No query data yet, system just started or no queries have been initiated" :image-size="120">
        <el-button type="primary" @click="load">Refresh</el-button>
      </el-empty>
    </div>

    <div v-else class="rav-body" v-loading="loading">
      <!-- Left chart area -->
      <div class="rav-charts">
        <el-card class="chart-card">
          <template #header><span class="chart-title">Daily Query Volume</span></template>
          <div ref="dailyChartRef" class="echarts-box"></div>
        </el-card>
        <el-card class="chart-card">
          <template #header><span class="chart-title">Query Active Periods</span></template>
          <div ref="latencyChartRef" class="echarts-box"></div>
        </el-card>
        <el-card class="chart-card">
          <template #header><span class="chart-title">Safe Zone Hit Rate Trend</span></template>
          <div ref="hitChartRef" class="echarts-box"></div>
        </el-card>
        <el-card class="chart-card">
          <template #header><span class="chart-title">Time Consumption by Phase</span></template>
          <div ref="pieChartRef" class="echarts-box echarts-box--pie"></div>
        </el-card>
      </div>

      <!-- Right metrics cards -->
      <div class="rav-detail">
        <el-card class="detail-card">
          <template #header><span class="card-header-title">Performance Metrics</span></template>
          <div class="metrics-grid">
            <div class="metric-item">
              <span class="metric-val" style="color:#38bdf8">{{ statsData?.avg_latency_ms ?? '—' }} ms</span>
              <span class="metric-key">Avg Latency</span>
            </div>
            <div class="metric-item">
              <span class="metric-val" style="color:#34d399">{{ hitRate }} %</span>
              <span class="metric-key">Safe Zone Hit Rate</span>
            </div>
            <div class="metric-item">
              <span class="metric-val" style="color:#a78bfa">{{ statsData?.stageAvgMs?.encrypt ?? '—' }} ms</span>
              <span class="metric-key">Encryption Time</span>
            </div>
            <div class="metric-item">
              <span class="metric-val" style="color:#fbbf24">{{ statsData?.stageAvgMs?.fog_calc ?? '—' }} ms</span>
              <span class="metric-key">Fog Node Computation</span>
            </div>
          </div>
        </el-card>

        <el-card class="detail-card">
          <template #header><span class="card-header-title">Query Status Distribution</span></template>
          <div class="status-dist">
            <template v-if="hasStatusData">
              <div class="sd-row" v-for="(cnt, st) in statsData!.statusSummary" :key="st">
                <el-tag :type="statusTagType(st as string)" effect="dark" size="small">
                  {{ statusLabel(st as string) }}
                </el-tag>
                <span class="sd-bar-wrap">
                  <span class="sd-bar" :style="{ width: pct(cnt) + '%' }" />
                </span>
                <span class="sd-cnt">{{ cnt }}</span>
              </div>
            </template>
            <el-empty v-else description="No data" :image-size="40" />
          </div>
        </el-card>

        <el-card class="detail-card">
          <template #header><span class="card-header-title">Avg Time by Phase</span></template>
          <div class="stage-list" v-if="stageRows.length">
            <div class="st-row" v-for="s in stageRows" :key="s.name">
              <span class="st-name">{{ s.name }}</span>
              <span class="st-val" :style="{ color: s.color }">{{ s.val }} ms</span>
            </div>
          </div>
          <el-empty v-else description="No data" :image-size="40" />
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import {
  getPerformanceAnalysis,
  toLatencyBarOption,
  toHitRateLineOption,
  toStagePieOption,
  toDailyBarOption,
} from '@/services/metrics.service'
import type { QueryStatsResponse } from '@/services/metrics.service'
import * as echarts from 'echarts'

const loading   = ref(false)
const errorMsg  = ref('')
const days      = ref(7)
const statsData = ref<QueryStatsResponse | null>(null)

// Empty state check
const isEmpty = computed(() => {
  if (!statsData.value) return true
  return (
    statsData.value.total_queries === 0 ||
    (!statsData.value.dailyQueryCount?.length &&
      !statsData.value.latencyDistribution?.length)
  )
})

const hasStatusData = computed(() => {
  const s = statsData.value?.statusSummary
  return s && Object.keys(s).length > 0
})

// ECharts containers
const dailyChartRef   = ref<HTMLElement | null>(null)
const latencyChartRef = ref<HTMLElement | null>(null)
const hitChartRef     = ref<HTMLElement | null>(null)
const pieChartRef     = ref<HTMLElement | null>(null)
let charts: echarts.ECharts[] = []

// Safe fallback option for empty data
const EMPTY_BAR = {
  xAxis: { type: 'category' as const, data: [] },
  yAxis: { type: 'value' as const },
  series: [] as any[],
  graphic: [{ type: 'text', left: 'center', top: 'middle',
    style: { text: 'No data', fontSize: 14, fill: '#475569' }}],
}
const EMPTY_PIE = {
  series: [{ type: 'pie' as const, data: [] as any[] }],
  graphic: [{ type: 'text', left: 'center', top: 'middle',
    style: { text: 'No data', fontSize: 14, fill: '#475569' }}],
}

function safeOpt(opt: any, fallback: any): any {
  try {
    const hasData = (opt?.series?.[0]?.data?.length > 0) ||
                    (opt?.xAxis?.data?.length > 0)
    return hasData ? opt : fallback
  } catch {
    return fallback
  }
}

function initCharts() {
  charts.forEach(c => { try { c.dispose() } catch {} })
  charts = []
  if (!statsData.value || isEmpty.value) return
  const d = statsData.value

  const pairs: Array<[HTMLElement | null, any, any]> = [
    [dailyChartRef.value,   toDailyBarOption(d.dailyQueryCount ?? []),       EMPTY_BAR],
    [latencyChartRef.value, toLatencyBarOption(d.latencyDistribution ?? []), EMPTY_BAR],
    [hitChartRef.value,     toHitRateLineOption(d.hitRateTrend ?? []),       EMPTY_BAR],
    [pieChartRef.value,     toStagePieOption(d.stageCostBreakdown ?? []),    EMPTY_PIE],
  ]

  pairs.forEach(([el, opt, fallback]) => {
    if (!el) return
    try {
      const c = echarts.init(el, 'dark')
      c.setOption(safeOpt(opt, fallback))
      charts.push(c)
    } catch (e) {
      console.warn('[ResultsAnalysis] ECharts init error:', e)
    }
  })
}

async function load() {
  loading.value  = true
  errorMsg.value = ''
  try {
    statsData.value = await getPerformanceAnalysis(days.value)
    await nextTick()
    initCharts()
  } catch (e: any) {
    errorMsg.value  = `Failed to load: ${e?.message ?? 'Please ensure backend is running'}`
    statsData.value = null
  } finally {
    loading.value = false
  }
}

function onResize() { charts.forEach(c => { try { c.resize() } catch {} }) }

onMounted(() => { load(); window.addEventListener('resize', onResize) })
onUnmounted(() => {
  charts.forEach(c => { try { c.dispose() } catch {} })
  window.removeEventListener('resize', onResize)
})

// Weighted average hit rate
const hitRate = computed(() => {
  const trend = statsData.value?.hitRateTrend ?? []
  if (!trend.length) return '—'
  const totalHits    = trend.reduce((s, d) => s + d.hits, 0)
  const totalUpdates = trend.reduce((s, d) => s + d.updates, 0)
  return totalUpdates > 0 ? (totalHits / totalUpdates * 100).toFixed(1) : '0.0'
})

const stageRows = computed(() => {
  const m = statsData.value?.stageAvgMs
  if (!m) return []
  return [
    { name: 'Local Encryption',   val: m.encrypt,  color: '#38bdf8' },
    { name: 'Secure Pruning',     val: m.pruning,  color: '#34d399' },
    { name: 'Task Dispatch',      val: m.dispatch, color: '#fbbf24' },
    { name: 'Fog Node Calc',      val: m.fog_calc, color: '#a78bfa' },
  ]
})

const totalInSummary = computed(() => {
  const s = statsData.value?.statusSummary
  if (!s) return 1
  return Object.values(s).reduce((a, b) => a + b, 0) || 1
})
function pct(cnt: number) { return Math.round(cnt / totalInSummary.value * 100) }

function statusLabel(s: string) {
  return ({ completed: 'Completed', failed: 'Failed', cancelled: 'Cancelled',
            processing: 'Processing', pending: 'Pending' } as any)[s] ?? s
}
function statusTagType(s: string) {
  return ({ completed: 'success', failed: 'danger', cancelled: 'warning',
            processing: 'info', pending: 'info' } as any)[s] ?? 'info'
}
</script>

<style scoped>
.rav-root { display: flex; flex-direction: column; background: #0d1117; font-family: 'PingFang SC','Microsoft YaHei',sans-serif; }
.rav-topbar { display: flex; align-items: center; justify-content: space-between; padding: 16px 28px; border-bottom: 1px solid #1e293b; flex-shrink: 0; position: sticky; top: 0; z-index: 10; background: #0d1117; }
.rav-title { font-size: 22px; font-weight: 700; color: #f1f5f9; letter-spacing: 1px; }
.rav-filters { display: flex; align-items: center; gap: 12px; }
.filter-label { font-size: 15px; color: #475569; }

/* Empty state */
.rav-empty { flex: 1; display: flex; align-items: center; justify-content: center; min-height: 300px; }

.rav-body { display: flex; align-items: flex-start; }
.rav-charts { flex: 1; padding: 20px; display: flex; flex-direction: column; gap: 16px; min-width: 0; }
.chart-card { background: #1e222d; border: 1px solid #1e293b; border-radius: 8px; }
.chart-title { font-size: 15px; font-weight: 600; color: #94a3b8; }
.echarts-box { height: 240px; }
.echarts-box--pie { height: 320px; }

.rav-detail { width: 360px; flex-shrink: 0; padding: 20px; display: flex; flex-direction: column; gap: 14px; border-left: 1px solid #1e293b; position: sticky; top: 57px; align-self: flex-start; max-height: calc(100vh - 57px - 52px); overflow-y: auto; }
.detail-card { background: #1e222d; border: 1px solid #1e293b; border-radius: 8px; }
.card-header-title { font-size: 15px; font-weight: 600; color: #94a3b8; }

.metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.metric-item { display: flex; flex-direction: column; align-items: center; padding: 14px 8px; background: #131720; border-radius: 6px; }
.metric-val { font-size: 24px; font-weight: 700; font-variant-numeric: tabular-nums; }
.metric-key { font-size: 13px; color: #475569; margin-top: 6px; }

.status-dist { display: flex; flex-direction: column; gap: 10px; }
.sd-row { display: flex; align-items: center; gap: 8px; font-size: 14px; }
.sd-bar-wrap { flex: 1; background: #1e293b; border-radius: 3px; height: 7px; overflow: hidden; }
.sd-bar { display: block; height: 100%; background: #38bdf8; border-radius: 3px; transition: width .3s; }
.sd-cnt { min-width: 28px; text-align: right; color: #64748b; }

.stage-list { display: flex; flex-direction: column; gap: 10px; }
.st-row { display: flex; justify-content: space-between; font-size: 15px; padding: 6px 0; border-bottom: 1px solid #1e293b; }
.st-name { color: #64748b; }
.st-val { font-variant-numeric: tabular-nums; font-weight: 600; }
</style>
