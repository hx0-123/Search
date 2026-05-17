/**
 * Metrics Service
 * Node monitoring and query performance statistics API
 */
import { api } from './api.client'

// ── Node Monitoring Types ────────────────────────────────────
export interface NodeInfo {
  node_id: string
  node_name: string
  node_type: 'cloud' | 'fog'
  status: 'active' | 'inactive' | 'maintenance' | 'error'
  host: string
  port: number
  cpu_percent: number
  memory_percent: number
  active_tasks: number
  reserved_tasks?: number
  total_tasks_processed: number
  average_processing_ms?: number
  last_heartbeat: string
  uptime_seconds?: number
}

export interface NodeStatusResponse {
  timestamp: string
  celery_online: boolean
  summary: {
    total_nodes: number
    active_fog_nodes: number
    total_fog_nodes: number
    active_tasks: number
    completed_24h: number
  }
  cloud_node: NodeInfo
  fog_nodes: NodeInfo[]
}

// ── Performance Statistics Types ─────────────────────────────
export interface LatencyPoint { hour: string; count: number }
export interface DailyCount   { date: string; count: number }
export interface HitRatePoint { date: string; hits: number; updates: number; hit_rate: number }
export interface StageCost    { name: string; value: number; percent: number }

export interface QueryStatsResponse {
  period_days: number
  total_queries: number
  avg_latency_ms: number
  statusSummary: Record<string, number>
  dailyQueryCount: DailyCount[]
  latencyDistribution: LatencyPoint[]
  stageCostBreakdown: StageCost[]
  hitRateTrend: HitRatePoint[]
  stageAvgMs: {
    encrypt: number
    pruning: number
    dispatch: number
    fog_calc: number
  }
}

/**
 * Get node monitoring status
 * GET /api/nodes/status/
 */
export async function getDashboardStats(): Promise<NodeStatusResponse> {
  const res = await api.get<NodeStatusResponse>('/nodes/status/')
  return res as unknown as NodeStatusResponse
}

/**
 * Get query performance statistics
 * GET /api/query/stats/?days=N
 */
export async function getPerformanceAnalysis(days = 7): Promise<QueryStatsResponse> {
  const res = await api.get<QueryStatsResponse>(`/query/stats/?days=${days}`)
  return res as unknown as QueryStatsResponse
}

// ── ECharts Data Conversion Utilities ────────────────────────

/** Latency distribution → ECharts bar option */
export function toLatencyBarOption(data: LatencyPoint[]) {
  return {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.map(d => d.hour), axisLabel: { rotate: 30, fontSize: 11 } },
    yAxis: { type: 'value', name: 'Queries' },
    series: [{ type: 'bar', data: data.map(d => d.count), itemStyle: { color: '#38bdf8' }, barMaxWidth: 40 }],
  }
}

/** Hit rate trend → ECharts line option */
export function toHitRateLineOption(data: HitRatePoint[]) {
  return {
    tooltip: { trigger: 'axis', formatter: (p: any[]) => `${p[0].axisValue}<br/>Hit Rate: ${p[0].value}%` },
    xAxis: { type: 'category', data: data.map(d => d.date) },
    yAxis: { type: 'value', min: 0, max: 100, name: 'Hit Rate (%)' },
    series: [{
      type: 'line', smooth: true,
      data: data.map(d => d.hit_rate),
      areaStyle: { color: 'rgba(52,211,153,0.15)' },
      lineStyle: { color: '#34d399' },
      itemStyle: { color: '#34d399' },
    }],
  }
}

/** Stage cost → ECharts pie option */
export function toStagePieOption(data: StageCost[]) {
  const colors = ['#38bdf8', '#34d399', '#a78bfa', '#fbbf24']
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ms ({d}%)' },
    legend: {
      orient: 'horizontal',
      bottom: 4,
      left: 'center',
      textStyle: { fontSize: 11, color: '#94a3b8' },
      itemWidth: 12,
      itemHeight: 12,
      itemGap: 12,
    },
    series: [{
      type: 'pie',
      radius: ['35%', '60%'],
      center: ['50%', '44%'],   // Move center up to leave space for bottom legend
      data: data.map((d, i) => ({
        name: d.name,
        value: d.value,
        itemStyle: { color: colors[i % colors.length] },
      })),
      label: {
        show: true,
        fontSize: 11,
        formatter: '{d}%',
      },
      labelLine: { length: 8, length2: 6 },
    }],
  }
}

/** Daily queries → ECharts bar option */
export function toDailyBarOption(data: DailyCount[]) {
  return {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.map(d => d.date) },
    yAxis: { type: 'value', name: 'Queries' },
    series: [{ type: 'bar', data: data.map(d => d.count), itemStyle: { color: '#818cf8' }, barMaxWidth: 48 }],
  }
}

