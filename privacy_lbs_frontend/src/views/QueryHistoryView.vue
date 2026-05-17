<template>
  <div class="qh-wrap">
    <div class="qh-header">
      <div class="qh-title">Query History</div>
      <div class="qh-sub">Current User Query History · Privacy Protection Mode</div>
    </div>

    <!-- Filter toolbar -->
    <div class="qh-toolbar">
      <el-input v-model="searchKw" placeholder="Search Keywords" :prefix-icon="Search" clearable style="width:220px" />
      <el-select v-model="filterStatus" placeholder="All Status" clearable style="width:140px">
        <el-option label="All Status" value="" />
        <el-option label="Completed" value="completed" />
        <el-option label="Failed" value="failed" />
        <el-option label="Cancelled" value="cancelled" />
        <el-option label="Processing" value="processing" />
      </el-select>
      <el-button :icon="Refresh" @click="loadHistory" :loading="loading" circle />
      <el-button @click="clearAll" :icon="Delete" text type="danger">Clear All</el-button>
    </div>

    <!-- Stats cards -->
    <div class="qh-stats">
      <div class="stat-card" v-for="s in statsCards" :key="s.label">
        <div class="stat-num" :style="{ color: s.color }">{{ s.value }}</div>
        <div class="stat-label">{{ s.label }}</div>
      </div>
    </div>

    <!-- Error alert -->
    <el-alert v-if="errorMsg" :title="errorMsg" type="error" show-icon closable @close="errorMsg=''" style="margin-bottom:12px" />

    <!-- Records table -->
    <div class="qh-table-wrap">
      <el-table
        v-loading="loading"
        :data="filteredRecords"
        stripe
        style="width:100%"
        :header-cell-style="{ background:'#1e222d', color:'#94a3b8', fontSize:'13px', fontWeight:'600' }"
        :row-style="{ background:'#131720' }"
        :cell-style="{ color:'#cbd5e1', fontSize:'13px', borderColor:'#1e293b' }"
        empty-text="No query records"
      >
        <el-table-column type="index" label="#" width="55" />
        <el-table-column prop="query_id" label="Query ID" width="160">
          <template #default="{ row }">
            <span class="mono">{{ row.query_id.slice(0, 16) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="keyword" label="Query Keyword" min-width="160">
          <template #default="{ row }">
            <el-tag size="small" effect="dark" type="info">{{ row.keyword || '—' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="result_count" label="Results" width="90" align="center">
          <template #default="{ row }">
            <span class="result-num">{{ row.result_count ?? '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="Duration (ms)" width="110" align="center">
          <template #default="{ row }">
            <span :style="{ color: row.duration_ms < 1000 ? '#34d399' : row.duration_ms < 5000 ? '#fbbf24' : '#f87171' }">
              {{ row.duration_ms ?? '—' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="Status" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" effect="dark" size="small">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Query Time" width="175">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="Action" width="110" align="center">
          <template #default="{ row }">
            <el-button text size="small" type="danger"
              v-if="row.status === 'processing'"
              @click="cancelRecord(row)">Cancel</el-button>
            <el-button text size="small" type="primary" @click="viewDetail(row)">Details</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="qh-pagination">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          background
          @current-change="loadHistory"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Search, Delete, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/services/api.client'
import { cancelQuery } from '@/services/query.service'
import dayjs from 'dayjs'

interface HistoryRecord {
  id: number
  query_id: string
  keyword: string
  status: string
  is_continuous: boolean
  top_k: number
  text_weight: number
  distance_weight: number
  candidate_count: number
  result_count: number
  duration_ms: number | null
  created_at: string
  completed_at: string | null
}

const searchKw    = ref('')
const filterStatus = ref('')
const currentPage = ref(1)
const pageSize    = ref(10)
const total       = ref(0)
const loading     = ref(false)
const errorMsg    = ref('')
const records     = ref<HistoryRecord[]>([])

async function loadHistory() {
  loading.value = true
  errorMsg.value = ''
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize.value,
    }
    if (filterStatus.value) params.status = filterStatus.value
    const res: any = await api.get('/query/history/', { params })
    const data = res as { total: number; records: HistoryRecord[] }
    total.value   = data.total ?? 0
    records.value = data.records ?? []
  } catch (e: any) {
    errorMsg.value = `Loading failed: ${e?.message ?? 'Network error'}`
    records.value  = []
  } finally {
    loading.value = false
  }
}

const filteredRecords = computed(() => {
  if (!searchKw.value) return records.value
  return records.value.filter(r => r.keyword?.includes(searchKw.value))
})

const statsCards = computed(() => [
  { label: 'Total Queries',    value: total.value,                                                           color: '#38bdf8' },
  { label: 'Successful Queries',      value: records.value.filter(r => r.status === 'completed').length,           color: '#34d399' },
  { label: 'Failed/Cancelled',     value: records.value.filter(r => ['failed','cancelled'].includes(r.status)).length, color: '#f87171' },
  { label: 'Avg Duration(ms)',  value: (() => {
    const valid = records.value.filter(r => r.duration_ms != null)
    if (!valid.length) return '—'
    return Math.round(valid.reduce((s, r) => s + r.duration_ms!, 0) / valid.length)
  })(), color: '#a78bfa' },
])

function statusLabel(s: string) {
  return { completed: 'Completed', failed: 'Failed', cancelled: 'Cancelled', processing: 'Processing', pending: 'Pending' }[s] ?? s
}
function statusTagType(s: string): 'success' | 'danger' | 'warning' | 'info' {
  return { completed: 'success', failed: 'danger', cancelled: 'warning', processing: 'info', pending: 'info' }[s] as any ?? 'info'
}
function formatTime(t: string) {
  return t ? dayjs(t).format('YYYY-MM-DD HH:mm:ss') : '—'
}

function viewDetail(row: HistoryRecord) {
  ElMessage.info(`Query ${row.query_id.slice(0, 16)} — Status: ${statusLabel(row.status)}, Duration: ${row.duration_ms ?? '—'} ms`)
}

async function cancelRecord(row: HistoryRecord) {
  try {
    await cancelQuery(row.query_id)
    ElMessage.success('Query cancelled')
    loadHistory()
  } catch (e: any) {
    ElMessage.error(`Cancel failed: ${e?.message}`)
  }
}

async function clearAll() {
  await ElMessageBox.confirm('Cannot be recovered after clearing, continue?', 'Warning', {
    confirmButtonText: 'Confirm Clear', cancelButtonText: 'Cancel', type: 'warning',
  })
  records.value = []
  total.value   = 0
  ElMessage.success('Current page records cleared (backend data not deleted)')
}

onMounted(loadHistory)
</script>

<style scoped>
.qh-wrap {
  min-height: 100%;
  background: #0d1117;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}
.qh-header { border-left: 3px solid #38bdf8; padding-left: 14px; }
.qh-title { font-size: 20px; font-weight: 700; color: #f1f5f9; letter-spacing: 1px; }
.qh-sub { font-size: 13px; color: #475569; margin-top: 4px; }
.qh-toolbar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.qh-stats { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; }
.stat-card { background: #1e222d; border: 1px solid #1e293b; border-radius: 8px; padding: 16px 20px; display: flex; flex-direction: column; gap: 6px; }
.stat-num { font-size: 28px; font-weight: 700; font-variant-numeric: tabular-nums; line-height: 1; }
.stat-label { font-size: 12px; color: #64748b; letter-spacing: .5px; }
.qh-table-wrap { background: #131720; border: 1px solid #1e293b; border-radius: 8px; overflow: hidden; flex: 1; }
.mono { font-family: 'JetBrains Mono','Courier New',monospace; font-size: 12px; color: #94a3b8; }
.result-num { color: #34d399; font-weight: 600; }
.qh-pagination { padding: 16px 20px; display: flex; justify-content: flex-end; background: #131720; border-top: 1px solid #1e293b; }
</style>
