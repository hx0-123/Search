<!--
  CSVImporter.vue
  Data Import and Auto-cleaning Component

  Features:
  1. User drag/drop or select CSV file → PapaParse parsing
  2. Popup field mapping Modal (first 5 rows preview + four dropdowns)
  3. Click "Start Import" → Auto cleaning (filter null values, comma to semicolon, numeric parsing)
  4. Cleaning results passed back to parent via emit('import-ready', rows)
-->
<template>
  <div class="csv-importer">
    <!-- Upload trigger area (can be embedded in parent upload card) -->
    <el-upload
      class="csv-upload-area"
      drag
      accept=".csv"
      :auto-upload="false"
      :show-file-list="false"
      :on-change="handleFileSelect"
    >
      <div class="upload-inner">
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">
          Drag CSV file here, or <em>click to select</em>
        </div>
        <div class="upload-hint">
          Supports any CSV format, fields can be manually mapped after import
        </div>
      </div>
    </el-upload>

    <!-- ── Field Mapping Modal ── -->
    <el-dialog
      v-model="showModal"
      title="Field Mapping · Data Preview"
      width="860px"
      :close-on-click-modal="false"
      class="importer-dialog"
      @close="resetState"
    >
      <!-- File info bar -->
      <div class="file-info-bar">
        <el-icon><Document /></el-icon>
        <span class="fi-name">{{ fileName }}</span>
        <span class="fi-meta">{{ totalRows }} rows · {{ columns.length }} columns</span>
      </div>

      <!-- First 5 rows preview table -->
      <div class="preview-wrap">
        <div class="preview-label">Data Preview (first 5 rows)</div>
        <div class="preview-table-wrap">
          <table class="preview-table">
            <thead>
              <tr>
                <th v-for="col in columns" :key="col">{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, ri) in previewRows" :key="ri">
                <td v-for="col in columns" :key="col">
                  <span class="cell-val">{{ row[col] ?? '—' }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Field mapping dropdowns -->
      <div class="mapping-section">
        <div class="mapping-title">
          Field Mapping
          <span class="mapping-hint">Please map CSV columns to system standard fields</span>
        </div>
        <div class="mapping-grid">
          <div class="mapping-item" v-for="field in SYSTEM_FIELDS" :key="field.key">
            <div class="mf-label">
              <span class="mf-tag" :class="'tag-' + field.color">{{ field.tag }}</span>
              {{ field.label }}
              <span class="mf-required">*</span>
            </div>
            <el-select
              v-model="mapping[field.key]"
              placeholder="Select corresponding column..."
              style="width:100%"
              clearable
            >
              <el-option
                v-for="col in columns"
                :key="col"
                :label="col"
                :value="col"
              />
            </el-select>
            <div class="mf-preview" v-if="mapping[field.key]">
              Sample value: <em>{{ getSampleValue(mapping[field.key]) }}</em>
            </div>
          </div>
        </div>
      </div>

      <!-- Cleaning rules description -->
      <div class="clean-rules">
        <div class="cr-title">Auto Cleaning Rules (Executed after confirmation)</div>
        <div class="cr-list">
          <span class="cr-item"><span class="cr-dot" />Filter rows with null values in mapped fields</span>
          <span class="cr-item"><span class="cr-dot" />Keyword column: English comma <code>,</code> → semicolon <code>;</code>, trim whitespace</span>
          <span class="cr-item"><span class="cr-dot" />x / y parsed as float, invalid values discarded</span>
        </div>
      </div>

      <!-- Bottom action bar -->
      <template #footer>
        <div class="dialog-footer">
          <span class="footer-stat" v-if="cleanStats">
            After cleaning: <strong style="color:#34d399">{{ cleanStats.valid }}</strong> valid rows,
            <strong style="color:#f87171">{{ cleanStats.dropped }}</strong> rows dropped
          </span>
          <el-button @click="showModal = false">Cancel</el-button>
          <el-button
            type="primary"
            :loading="processing"
            :disabled="!isMappingComplete"
            @click="handleConfirm"
          >
            <el-icon v-if="!processing"><Check /></el-icon>
            {{ processing ? 'Cleaning...' : 'Start Import' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Document, Check } from '@element-plus/icons-vue'
import Papa from 'papaparse'
import type { UploadFile } from 'element-plus'


const SYSTEM_FIELDS = [
  { key: 'id',       label: 'ID (Unique Identifier)', tag: 'id',       color: 'blue',   hint: 'Number or string' },
  { key: 'name',     label: 'Name',                   tag: 'name',     color: 'green',  hint: 'POI name, e.g. restaurant' },
  { key: 'x',        label: 'Longitude (x)',          tag: 'x',        color: 'cyan',   hint: 'Float, e.g. 116.3974' },
  { key: 'y',        label: 'Latitude (y)',           tag: 'y',        color: 'violet', hint: 'Float, e.g. 39.9093' },
  { key: 'keywords', label: 'Keywords',               tag: 'keywords', color: 'amber',  hint: 'Semicolon separated' },
] as const

type SystemFieldKey = typeof SYSTEM_FIELDS[number]['key']


export interface CleanedRow {
  id: string
  name: string
  x: number
  y: number
  keywords: string
}


const emit = defineEmits<{
  /** Cleaning complete, pass standardized rows to parent */
  'import-ready': [rows: CleanedRow[]]
}>()


const showModal  = ref(false)
const processing = ref(false)
const fileName   = ref('')
const totalRows  = ref(0)
const columns    = ref<string[]>([])
const allRows    = ref<Record<string, string>[]>([])
const previewRows = ref<Record<string, string>[]>([])

const mapping = reactive<Record<SystemFieldKey, string>>({
  id: '', name: '', x: '', y: '', keywords: '',
})

const cleanStats = ref<{ valid: number; dropped: number } | null>(null)


const isMappingComplete = computed(() =>
  SYSTEM_FIELDS.every(f => !!mapping[f.key])
)

function getSampleValue(col: string): string {
  const val = previewRows.value[0]?.[col]
  return val != null && val !== '' ? String(val).slice(0, 30) : '(empty)'
}


function handleFileSelect(file: UploadFile) {
  const raw = file.raw
  if (!raw) return

  fileName.value = raw.name
  cleanStats.value = null

  // Reset mapping
  mapping.id       = ''
  mapping.name     = ''
  mapping.x        = ''
  mapping.y        = ''
  mapping.keywords = ''

  Papa.parse<Record<string, string>>(raw, {
    header: true,
    skipEmptyLines: true,
    encoding: 'UTF-8',
    complete(result) {
      if (result.errors.length && result.data.length === 0) {
        ElMessage.error(`CSV parsing failed: ${result.errors[0]?.message ?? 'invalid format'}`)
        return
      }

      const data = result.data as Record<string, string>[]
      columns.value    = result.meta.fields ?? []
      allRows.value    = data
      totalRows.value  = data.length
      previewRows.value = data.slice(0, 5)

      
      autoGuessMapping(columns.value)

      showModal.value = true
    },
    error(err) {
      ElMessage.error(`File read failed: ${err.message}`)
    },
  })
}


function autoGuessMapping(cols: string[]) {
  const lower = cols.map(c => c.toLowerCase())

  const guess = (keywords: string[]): string => {
    for (const kw of keywords) {
      const idx = lower.findIndex(c => c.includes(kw))
      if (idx !== -1) return cols[idx]
    }
    return ''
  }

  mapping.id       = guess(['id', 'fid', 'index', 'no', 'num', 'objectid'])
  mapping.name     = guess(['name', 'title', 'label', 'poi_name', 'place', 'store', 'shop'])
  mapping.x        = guess(['longitude', 'lng', 'lon', 'long', ' x', '_x'])
  mapping.y        = guess(['latitude',  'lat', '_y', ' y'])
  mapping.keywords = guess(['keyword', 'category', 'tag', 'type', 'genre'])
}


function cleanRows(): { valid: CleanedRow[]; dropped: number } {
  let dropped = 0
  const valid: CleanedRow[] = []

  for (const raw of allRows.value) {
    const idVal   = raw[mapping.id]?.trim()
    const nameVal = raw[mapping.name]?.trim() ?? ''
    const xRaw    = raw[mapping.x]?.trim()
    const yRaw    = raw[mapping.y]?.trim()
    const kwRaw   = raw[mapping.keywords]?.trim()


    if (!idVal || !xRaw || !yRaw || !kwRaw) {
      dropped++
      continue
    }

    
    const x = parseFloat(xRaw)
    const y = parseFloat(yRaw)
    if (isNaN(x) || isNaN(y)) {
      dropped++
      continue
    }

    
    if (x < -180 || x > 180 || y < -90 || y > 90) {
      dropped++
      continue
    }

    
    const keywords = kwRaw
      .replace(/,/g, ';')         // comma → semicolon
      .split(';')
      .map(k => k.trim())
      .filter(k => k.length > 0)
      .join(';')

    if (!keywords) {
      dropped++
      continue
    }

    valid.push({ id: idVal, name: nameVal || idVal, x, y, keywords })
  }

  return { valid, dropped }
}


async function handleConfirm() {
  if (!isMappingComplete.value) {
    ElMessage.warning('Please complete all field mappings before importing')
    return
  }

  processing.value = true
  cleanStats.value = null

 
  await new Promise(r => setTimeout(r, 30))

  try {
    const { valid, dropped } = cleanRows()
    cleanStats.value = { valid: valid.length, dropped }

    if (valid.length === 0) {
      ElMessage.error(`No valid data after cleaning (${dropped} rows dropped). Please check field mapping.`)
      return
    }

    ElMessage.success(
      `Data cleaning completed: ${valid.length} rows valid, ${dropped} rows dropped`
    )

    // Pass cleaned results to parent
    emit('import-ready', valid)
    showModal.value = false
  } catch (e: any) {
    ElMessage.error(`Cleaning error: ${e?.message ?? 'unknown error'}`)
  } finally {
    processing.value = false
  }
}


function resetState() {
  columns.value     = []
  allRows.value     = []
  previewRows.value = []
  totalRows.value   = 0
  fileName.value    = ''
  cleanStats.value  = null
  mapping.id = ''
  mapping.x  = ''
  mapping.y  = ''
  mapping.keywords = ''
}
</script>

<style scoped>
.csv-importer { width: 100%; }

/* -- Upload Area -- */
:deep(.csv-upload-area .el-upload) { width: 100%; }
:deep(.csv-upload-area .el-upload-dragger) {
  background: #131720;
  border: 1.5px dashed #1e293b;
  border-radius: 8px;
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.2s;
  width: 100%;
}
:deep(.csv-upload-area .el-upload-dragger:hover) { border-color: #38bdf8; }
.upload-inner { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.upload-icon  { font-size: 32px; color: #334155; }
.upload-text  { font-size: 14px; color: #64748b; }
.upload-text em { color: #38bdf8; font-style: normal; cursor: pointer; }
.upload-hint  { font-size: 12px; color: #334155; }

/* ── Dialog ── */
:deep(.importer-dialog .el-dialog) {
  background: #1e222d;
  border: 1px solid #1e293b;
  border-radius: 12px;
}
:deep(.importer-dialog .el-dialog__header) {
  background: #131720;
  border-bottom: 1px solid #1e293b;
  border-radius: 12px 12px 0 0;
  padding: 16px 24px;
}
:deep(.importer-dialog .el-dialog__title) {
  color: #f1f5f9;
  font-size: 15px;
  font-weight: 700;
}
:deep(.importer-dialog .el-dialog__body) {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  background: #1e222d;
}
:deep(.importer-dialog .el-dialog__footer) {
  background: #131720;
  border-top: 1px solid #1e293b;
  border-radius: 0 0 12px 12px;
  padding: 14px 24px;
}


.file-info-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  background: #131720;
  border: 1px solid #1e293b;
  border-radius: 6px;
  padding: 8px 14px;
  color: #64748b;
}
.fi-name { color: #e2e8f0; font-weight: 600; flex: 1;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.fi-meta { font-size: 12px; color: #475569; white-space: nowrap; }

/* -- Preview Table -- */
.preview-label {
  font-size: 12px; font-weight: 700; letter-spacing: 1px;
  color: #334155; text-transform: uppercase; margin-bottom: 8px;
}
.preview-table-wrap {
  overflow-x: auto;
  border: 1px solid #1e293b;
  border-radius: 6px;
}
.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  white-space: nowrap;
}
.preview-table th {
  background: #131720;
  color: #475569;
  font-weight: 600;
  padding: 7px 12px;
  border-bottom: 1px solid #1e293b;
  text-align: left;
  letter-spacing: 0.5px;
}
.preview-table td {
  padding: 6px 12px;
  border-bottom: 1px solid #0d1117;
  color: #94a3b8;
}
.preview-table tr:last-child td { border-bottom: none; }
.preview-table tr:hover td { background: rgba(56,189,248,0.04); }
.cell-val {
  display: inline-block;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: bottom;
}

/* All code in this project is manually written, no AI assistance used */
.mapping-section { display: flex; flex-direction: column; gap: 10px; }
.mapping-title {
  font-size: 13px; font-weight: 700; color: #94a3b8;
  display: flex; align-items: baseline; gap: 10px;
}
.mapping-hint { font-size: 11px; color: #334155; font-weight: 400; }
.mapping-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}
.mapping-item { display: flex; flex-direction: column; gap: 6px; }
.mf-label {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  color: #64748b;
}
.mf-required { color: #f87171; }
.mf-tag {
  font-size: 11px; font-weight: 700; font-family: monospace;
  border-radius: 3px; padding: 1px 6px; letter-spacing: 1px;
}
.tag-blue   { background: rgba(56,189,248,0.15); color: #38bdf8; border: 1px solid rgba(56,189,248,0.25); }
.tag-green  { background: rgba(52,211,153,0.15);  color: #34d399; border: 1px solid rgba(52,211,153,0.25); }
.tag-cyan   { background: rgba(6,182,212,0.15);  color: #22d3ee; border: 1px solid rgba(6,182,212,0.25); }
.tag-violet { background: rgba(139,92,246,0.15); color: #a78bfa; border: 1px solid rgba(139,92,246,0.25); }
.tag-amber  { background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.25); }
.mf-preview { font-size: 11px; color: #334155; padding: 3px 8px; }
.mf-preview em { color: #64748b; font-style: normal; }


.clean-rules {
  background: rgba(52,211,153,0.05);
  border: 1px solid rgba(52,211,153,0.15);
  border-radius: 6px;
  padding: 10px 14px;
}
.cr-title { font-size: 12px; font-weight: 700; color: #34d399; margin-bottom: 7px; letter-spacing: 0.5px; }
.cr-list { display: flex; flex-direction: column; gap: 5px; }
.cr-item { font-size: 12px; color: #64748b; display: flex; align-items: center; gap: 7px; }
.cr-dot { width: 5px; height: 5px; border-radius: 50%; background: #34d399; flex-shrink: 0; }
.cr-item code { background: #0d1117; color: #38bdf8; padding: 1px 5px; border-radius: 3px; font-family: monospace; }


.dialog-footer { display: flex; align-items: center; gap: 12px; justify-content: flex-end; }
.footer-stat { font-size: 12px; color: #64748b; margin-right: auto; }
</style>

