<template>
  <span>
    <!-- Trigger button slot -->
    <span @click="openWizard"><slot></slot></span>

    <!-- Step 1: File Selection -->
    <el-dialog
      v-model="step1Visible"
      title="Import CSV Dataset"
      width="520px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div class="wiz-body">
        <el-upload
          class="wiz-uploader"
          drag
          accept=".csv"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleFileSelected"
        >
          <div class="wiz-upload-inner">
            <el-icon class="wiz-upload-icon"><UploadFilled /></el-icon>
            <div class="wiz-upload-text">Drag CSV file here, or <em>click to select</em></div>
            <div class="wiz-upload-hint">Supports any CSV source (Kaggle, local datasets, etc.), max 100MB</div>
          </div>
        </el-upload>

        <div v-if="parsedPreview.length" class="wiz-file-info">
          <el-icon><Document /></el-icon>
          <span class="wiz-fname">{{ selectedFile?.name }}</span>
          <span class="wiz-fsize">{{ fileSizeStr }}</span>
          <el-tag type="info" effect="dark" size="small">{{ totalRows }} rows</el-tag>
          <el-tag type="success" effect="dark" size="small">{{ detectedColumns.length }} columns</el-tag>
        </div>

        <div v-if="parseError" class="wiz-parse-error">
          <el-alert :title="parseError" type="error" show-icon :closable="false" />
        </div>
      </div>

      <template #footer>
        <el-button @click="step1Visible = false">Cancel</el-button>
        <el-button
          type="primary"
          :disabled="!parsedPreview.length"
          @click="goToMapping"
        >
          Next: Field Mapping
          <el-icon class="el-icon--right"><ArrowRight /></el-icon>
        </el-button>
      </template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Document, ArrowRight } from '@element-plus/icons-vue'
import Papa from 'papaparse'
import { uploadCSV } from '@/services/data.service'
import type { UploadFile } from 'element-plus'


const emit = defineEmits<{
  /** Triggered after import completes, with cleaned row count and backend result */
  done: [payload: { cleanedRows: number; uploadResult: any }]
}>()


const step1Visible = ref(false)
const step2Visible = ref(false)
const step3Visible = ref(false)

function openWizard() {
  resetAll()
  step1Visible.value = true
}


const selectedFile  = ref<File | null>(null)
const detectedColumns = ref<string[]>([])
const parsedAllRows   = ref<Record<string, any>[]>([])  // Full dataset (for cleaning)
const parsedPreview   = ref<Record<string, any>[]>([])  // First 5 rows preview
const totalRows       = ref(0)
const parseError      = ref('')

const fileSizeStr = computed(() => {
  if (!selectedFile.value) return ''
  const kb = selectedFile.value.size / 1024
  return kb > 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${kb.toFixed(1)} KB`
})

function handleFileSelected(file: UploadFile) {
  const raw = file.raw
  if (!raw) return
  selectedFile.value = raw
  parseError.value = ''
  parsedAllRows.value = []
  parsedPreview.value = []
  detectedColumns.value = []

  Papa.parse(raw, {
    header: true,
    skipEmptyLines: true,
    complete(results) {
      if (!results.data.length) {
        parseError.value = 'CSV file is empty or format is incorrect'
        return
      }
      parsedAllRows.value = results.data as Record<string, any>[]
      parsedPreview.value = parsedAllRows.value.slice(0, 5)
      detectedColumns.value = results.meta.fields ?? []
      totalRows.value = parsedAllRows.value.length
      autoDetectMapping()
    },
    error(err) {
      parseError.value = `Parse failed: ${err.message}`
    },
  })
}

function goToMapping() {
  step1Visible.value = false
  step2Visible.value = true
}


type MappingKey = 'id' | 'x' | 'y' | 'keywords' | 'name'

const mapping = reactive<Record<MappingKey, string>>({
  id: '', x: '', y: '', keywords: '', name: '',
})

const mappingFields: { key: MappingKey; label: string; hint: string; required: boolean }[] = [
  { key: 'id',       label: 'Unique ID Column',       hint: 'Numeric type, unique identifier for each row',        required: true  },
  { key: 'x',        label: 'Longitude (X)', hint: 'Floating point number, e.g., 116.397',                  required: true  },
  { key: 'y',        label: 'Latitude (Y)',  hint: 'Floating point number, e.g., 39.908',                   required: true  },
  { key: 'keywords', label: 'Keywords Column',         hint: 'Text labels, separated by comma or semicolon',        required: true  },
  { key: 'name',     label: 'Name Column',        hint: 'POI readable name, e.g., "Quan Jude Store" (optional)', required: false },
]

const mappingError = ref('')

function autoDetectMapping() {
  const cols = detectedColumns.value.map(c => c.toLowerCase())
  const find = (keywords: string[]) =>
    detectedColumns.value.find((_, i) => keywords.some(k => cols[i].includes(k))) ?? ''

  mapping.id       = find(['id', 'index', 'no', 'num', 'objectid'])
  mapping.x        = find(['longitude', 'lng', 'lon', 'long', 'x'])
  mapping.y        = find(['latitude',  'lat', 'y'])
  mapping.keywords = find(['keyword', 'tag', 'category', 'type', 'label'])
  mapping.name     = find(['name', 'title', 'poi_name', 'store_name', 'document', 'desc'])
}


function isMapped(col: string): boolean {
  return Object.values(mapping).includes(col)
}


function mappedAs(col: string): string {
  const labels: Record<MappingKey, string> = { id: 'ID', x: 'Longitude', y: 'Latitude', keywords: 'Keywords', name: 'Name' }
  const key = (Object.keys(mapping) as MappingKey[]).find(k => mapping[k] === col)
  return key ? labels[key] : ''
}


const estimatedRows = computed(() => {
  if (!parsedAllRows.value.length) return 0
  const keys = Object.values(mapping).filter(Boolean)
  if (!keys.length) return parsedAllRows.value.length
  const validSample = parsedPreview.value.filter(row =>
    keys.every(k => row[k] !== null && row[k] !== undefined && String(row[k]).trim() !== '')
  ).length
  const rate = parsedPreview.value.length ? validSample / parsedPreview.value.length : 1
  return Math.round(parsedAllRows.value.length * rate)
})


const importing     = ref(false)
const importDone    = ref(false)
const importError   = ref('')
const uploadPct     = ref(0)
const progressLogs  = ref<{ ts: string; msg: string; type: string }[]>([])
const progressInfo  = reactive({ total: 0, filtered: 0, cleaned: 0, uploaded: 0 })

function addLog(msg: string, type = 'info') {
  const now = new Date()
  const ts = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}`
  progressLogs.value.push({ ts, msg, type })
}

function validateMapping(): boolean {
  mappingError.value = ''
  
  const missing = mappingFields.filter(f => f.required && !mapping[f.key]).map(f => f.label)
  if (missing.length) {
    mappingError.value = `Please complete the following field mappings: ${missing.join(', ')}`
    return false
  }
  const vals = Object.values(mapping).filter(Boolean)
  const unique = new Set(vals)
  if (unique.size !== vals.length) {
    mappingError.value = 'Each standard field must map to a different column. Please check for duplicate mappings.'
    return false
  }
  return true
}


function cleanRows(rows: Record<string, any>[]): {
  id: number; x: number; y: number; keywords: string; name: string
}[] {
  const { id: idCol, x: xCol, y: yCol, keywords: kwCol, name: nameCol } = mapping
  const cleaned: { id: number; x: number; y: number; keywords: string; name: string }[] = []
  let filtered = 0

  for (const row of rows) {
    // 1. Filter null values (required fields)
    const idVal  = row[idCol]
    const xVal   = row[xCol]
    const yVal   = row[yCol]
    const kwVal  = row[kwCol]

    if (
      idVal === null || idVal === undefined || String(idVal).trim() === '' ||
      xVal  === null || xVal  === undefined || String(xVal).trim()  === '' ||
      yVal  === null || yVal  === undefined || String(yVal).trim()  === '' ||
      kwVal === null || kwVal === undefined || String(kwVal).trim() === ''
    ) {
      filtered++
      continue
    }

    // 
    const x = parseFloat(String(xVal))
    const y = parseFloat(String(yVal))
    const id = parseInt(String(idVal), 10)

    if (isNaN(x) || isNaN(y) || isNaN(id)) {
      filtered++
      continue
    }

    
    const keywords = String(kwVal)
      .replace(/,/g, ';')
      .split(';')
      .map(k => k.trim())
      .filter(k => k.length > 0)
      .join(';')

 
    const name = nameCol ? String(row[nameCol] ?? '').trim() : ''

    cleaned.push({ id, x, y, keywords, name })
  }

  progressInfo.filtered = filtered
  progressInfo.cleaned  = cleaned.length
  return cleaned
}

async function startImport() {
  if (!validateMapping()) return

  step2Visible.value = false
  step3Visible.value = true
  importing.value    = true
  importDone.value   = false
  importError.value  = ''
  uploadPct.value    = 0
  progressLogs.value = []
  Object.assign(progressInfo, { total: 0, filtered: 0, cleaned: 0, uploaded: 0 })

  try {
 
    addLog('Starting field mapping parsing...')
    await new Promise(r => setTimeout(r, 80))

    progressInfo.total = parsedAllRows.value.length
    uploadPct.value = 10
    addLog(`Total ${progressInfo.total} rows in raw data, starting cleaning...`)
    await new Promise(r => setTimeout(r, 80))

    const cleaned = cleanRows(parsedAllRows.value)
    uploadPct.value = 30
    addLog(`Filtered invalid rows ${progressInfo.filtered} rows`, progressInfo.filtered > 0 ? 'warn' : 'info')
    addLog(`Cleaning completed, ${cleaned.length} valid rows`, 'success')
    await new Promise(r => setTimeout(r, 80))

    if (!cleaned.length) {
      throw new Error('No valid data after cleaning. Please check field mapping or data format.')
    }

   
    uploadPct.value = 40
    addLog('Generating standard format CSV...')
    await new Promise(r => setTimeout(r, 80))

    // Use PapaParse to output standard CSV (including optional name column)
    const csvColumns = ['id', 'x', 'y', 'keywords', 'name']
    const csvStr = Papa.unparse(cleaned, { header: true, columns: csvColumns })
    const blob   = new Blob([csvStr], { type: 'text/csv;charset=utf-8;' })
    const file   = new File([blob], selectedFile.value?.name ?? 'cleaned.csv', { type: 'text/csv' })

    uploadPct.value = 50
    addLog('Uploading to backend encryption API...')

    const result = await uploadCSV(file, (pct) => {
      // Map upload progress to 50-95%
      uploadPct.value = 50 + Math.round(pct * 0.45)
    })

    progressInfo.uploaded = result.objects_count ?? cleaned.length
    uploadPct.value = 100
    addLog(`Upload completed! Backend has encrypted and stored ${progressInfo.uploaded} records`, 'success')
    if (result.index_built) {
      const m = result.index_metadata
      addLog(`KASTree index built: depth=${m?.ktree_depth}, leaf nodes=${m?.ktree_leaf_count}`, 'success')
    }
    if (result.parse_warnings?.length) {
      result.parse_warnings.forEach(w => addLog(`⚠ Backend warning: ${w}`, 'warn'))
    }

    importDone.value = true
    emit('done', { cleanedRows: cleaned.length, uploadResult: result })

    ElMessage.success(`Successfully imported ${progressInfo.uploaded} POI records!`)
  } catch (e: any) {
    importError.value = e?.message ?? 'Unknown error, please retry'
    addLog(`Error: ${importError.value}`, 'error')
    uploadPct.value = 0
  } finally {
    importing.value  = false
    importDone.value = true
  }
}

function handleDone() {
  step3Visible.value = false
  if (!importError.value) resetAll()
}

function resetAll() {
  selectedFile.value    = null
  detectedColumns.value = []
  parsedAllRows.value   = []
  parsedPreview.value   = []
  totalRows.value       = 0
  parseError.value      = ''
  mappingError.value    = ''
  mapping.id = ''; mapping.x = ''; mapping.y = ''; mapping.keywords = ''; mapping.name = ''
  importing.value    = false
  importDone.value   = false
  importError.value  = ''
  uploadPct.value    = 0
  progressLogs.value = []
  Object.assign(progressInfo, { total: 0, filtered: 0, cleaned: 0, uploaded: 0 })
}
</script>

<style scoped>

.wiz-body { display: flex; flex-direction: column; gap: 14px; }
:deep(.wiz-uploader .el-upload) { width: 100%; }
:deep(.wiz-uploader .el-upload-dragger) {
  background: #131720; border: 1.5px dashed #1e293b; border-radius: 8px;
  height: 140px; display: flex; align-items: center; justify-content: center;
  transition: border-color .2s;
}
:deep(.wiz-uploader .el-upload-dragger:hover) { border-color: #38bdf8; }
.wiz-upload-inner { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.wiz-upload-icon { font-size: 32px; color: #334155; }
.wiz-upload-text { font-size: 14px; color: #64748b; }
.wiz-upload-text em { color: #38bdf8; font-style: normal; cursor: pointer; }
.wiz-upload-hint { font-size: 12px; color: #334155; }

.wiz-file-info {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; background: #1e222d;
  border: 1px solid #1e293b; border-radius: 6px; font-size: 13px; color: #94a3b8;
}
.wiz-fname { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #e2e8f0; }
.wiz-fsize { color: #475569; font-size: 12px; }
.wiz-parse-error { margin-top: 4px; }

/* ── Mapping ── */
.wiz-mapping-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 16px 20px;
}
.wiz-mapping-item { display: flex; flex-direction: column; gap: 5px; }
.wiz-mapping-label { font-size: 13px; font-weight: 600; color: #94a3b8; }
.wiz-mapping-required { color: #f87171; margin-right: 3px; }
.wiz-mapping-optional { color: #475569; font-size: 11px; margin-right: 3px; }
.wiz-mapping-hint { font-size: 11px; color: #475569; }

/* ── Preview Table ── */
.wiz-preview-wrap { overflow-x: auto; border: 1px solid #1e293b; border-radius: 6px; }
.wiz-preview-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.wiz-preview-table th {
  background: #1e222d; color: #64748b; font-weight: 600;
  padding: 7px 10px; text-align: left; white-space: nowrap;
  border-bottom: 1px solid #1e293b;
}
.wiz-preview-table th.col-mapped { background: rgba(56,189,248,.1); color: #38bdf8; }
.wiz-preview-table td {
  padding: 6px 10px; color: #94a3b8;
  border-bottom: 1px solid #0d1117; white-space: nowrap;
}
.wiz-preview-table td.col-mapped { color: #e2e8f0; font-weight: 500; }
.wiz-preview-table tr:last-child td { border-bottom: none; }
.col-mapped-badge {
  display: inline-block; margin-left: 4px; font-size: 10px;
  background: rgba(56,189,248,.2); color: #38bdf8;
  border-radius: 3px; padding: 0 4px;
}

/* ── Cleaning Rules ── */
.wiz-rules {
  background: rgba(52,211,153,.05); border: 1px solid rgba(52,211,153,.15);
  border-radius: 6px; padding: 10px 14px; font-size: 12px;
}
.wiz-rules-title { font-weight: 700; color: #34d399; display: block; margin-bottom: 6px; }
.wiz-rules ul { margin: 0; padding-left: 16px; color: #64748b; }
.wiz-rules li { margin-bottom: 3px; line-height: 1.6; }
.wiz-rules code { background: #1e222d; padding: 1px 4px; border-radius: 3px; color: #fbbf24; }

/* ── Footer Info ── */
.wiz-footer-info { font-size: 12px; color: #475569; flex: 1; text-align: center; }

/* ── Progress ── */
.wiz-progress-body { display: flex; flex-direction: column; gap: 14px; }
.wiz-prog-stats { display: grid; grid-template-columns: repeat(4,1fr); gap: 10px; }
.wiz-prog-stat {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  background: #1e222d; border: 1px solid #1e293b; border-radius: 6px; padding: 10px 8px;
}
.wiz-prog-num { font-size: 24px; font-weight: 700; font-variant-numeric: tabular-nums; }
.wiz-prog-label { font-size: 11px; color: #475569; }
.wiz-prog-bar-wrap { display: flex; flex-direction: column; gap: 5px; }
.wiz-prog-bar-label { display: flex; justify-content: space-between; font-size: 12px; color: #64748b; }

.wiz-prog-log {
  background: #0d1117; border: 1px solid #1e293b; border-radius: 6px;
  padding: 10px 14px; max-height: 180px; overflow-y: auto;
  display: flex; flex-direction: column; gap: 4px;
  font-family: 'JetBrains Mono', monospace; font-size: 12px;
}
.wiz-log-line { display: flex; gap: 10px; line-height: 1.5; }
.wiz-log-ts { color: #334155; flex-shrink: 0; }
.wiz-log-line.info  .span:last-child, .wiz-log-line:not([class*='warn']):not([class*='error']):not([class*='success']) span:last-child { color: #64748b; }
.wiz-log-line.success span:last-child { color: #34d399; }
.wiz-log-line.warn    span:last-child { color: #fbbf24; }
.wiz-log-line.error   span:last-child { color: #f87171; }
</style>
    </el-dialog>

    <!-- Step 2: Field Mapping + Preview -->
    <el-dialog
      v-model="step2Visible"
      title="Field Mapping · Data Preview"
      width="820px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div class="wiz-body">
        <!-- Mapping dropdowns -->
        <div class="wiz-mapping-grid">
          <div class="wiz-mapping-item" v-for="f in mappingFields" :key="f.key">
            <label class="wiz-mapping-label">
              <span v-if="f.required" class="wiz-mapping-required">*</span>
              <span v-else class="wiz-mapping-optional">[Optional]</span>
              {{ f.label }}
            </label>
            <el-select
              v-model="mapping[f.key]"
              :placeholder="f.required ? 'Select corresponding column' : 'Select column (optional)'"
              clearable
              style="width:100%"
            >
              <el-option
                v-for="col in detectedColumns"
                :key="col"
                :label="col"
                :value="col"
              />
            </el-select>
            <div class="wiz-mapping-hint">{{ f.hint }}</div>
          </div>
        </div>

        <el-divider>Data Preview (first 5 rows raw data)</el-divider>

        <!-- Preview table -->
        <div class="wiz-preview-wrap">
          <table class="wiz-preview-table">
            <thead>
              <tr>
                <th v-for="col in detectedColumns" :key="col"
                  :class="{ 'col-mapped': isMapped(col) }">
                  {{ col }}
                  <span v-if="isMapped(col)" class="col-mapped-badge">
                    {{ mappedAs(col) }}
                  </span>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, ri) in parsedPreview" :key="ri">
                <td v-for="col in detectedColumns" :key="col"
                  :class="{ 'col-mapped': isMapped(col) }">
                  {{ row[col] ?? '—' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Cleaning rules description -->
        <div class="wiz-rules">
          <span class="wiz-rules-title">Auto Cleaning Rules</span>
          <ul>
            <li>Filter rows with null values in mapped fields</li>
            <li>Keyword column: comma <code>,</code> → semicolon <code>;</code>, trim whitespace</li>
            <li>Coordinates parsed as float, non-numeric rows filtered</li>
          </ul>
        </div>

        <!-- Mapping validation error -->
        <el-alert
          v-if="mappingError"
          :title="mappingError"
          type="warning"
          show-icon
          :closable="false"
          style="margin-top:12px"
        />
      </div>

      <template #footer>
        <el-button @click="step2Visible = false; step1Visible = true">Back</el-button>
        <span class="wiz-footer-info">
          Estimated remaining after cleaning ≈ {{ estimatedRows }} rows
        </span>
        <el-button
          type="primary"
          :loading="importing"
          @click="startImport"
        >
          <el-icon v-if="!importing"><UploadFilled /></el-icon>
          {{ importing ? 'Cleaning and importing...' : 'Start Import' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Step 3: Progress -->
    <el-dialog
      v-model="step3Visible"
      title="Import Progress"
      width="480px"
      :close-on-click-modal="false"
      :show-close="importDone"
      destroy-on-close
    >
      <div class="wiz-progress-body">
        <div class="wiz-prog-stats">
          <div class="wiz-prog-stat">
            <span class="wiz-prog-num" style="color:#38bdf8">{{ progressInfo.total }}</span>
            <span class="wiz-prog-label">Total Rows</span>
          </div>
          <div class="wiz-prog-stat">
            <span class="wiz-prog-num" style="color:#f87171">{{ progressInfo.filtered }}</span>
            <span class="wiz-prog-label">Filtered</span>
          </div>
          <div class="wiz-prog-stat">
            <span class="wiz-prog-num" style="color:#34d399">{{ progressInfo.cleaned }}</span>
            <span class="wiz-prog-label">Cleaned</span>
          </div>
          <div class="wiz-prog-stat">
            <span class="wiz-prog-num" style="color:#a78bfa">{{ progressInfo.uploaded }}</span>
            <span class="wiz-prog-label">Uploaded</span>
          </div>
        </div>

        <div class="wiz-prog-bar-wrap">
          <div class="wiz-prog-bar-label">
            <span>{{ importDone ? (importError ? 'Import Failed' : 'Import Completed') : 'Processing...' }}</span>
            <span>{{ uploadPct }}%</span>
          </div>
          <el-progress
            :percentage="uploadPct"
            :stroke-width="10"
            :show-text="false"
            :color="importError ? '#f87171' : importDone ? '#34d399' : '#38bdf8'"
          />
        </div>

        <div class="wiz-prog-log">
          <div v-for="(l, i) in progressLogs" :key="i" class="wiz-log-line" :class="l.type">
            <span class="wiz-log-ts">{{ l.ts }}</span>
            <span>{{ l.msg }}</span>
          </div>
        </div>

        <el-alert
          v-if="importError"
          :title="importError"
          type="error"
          show-icon
          :closable="false"
          style="margin-top:12px"
        />
      </div>

      <template #footer>
        <span></span>
        <el-button
          v-if="importDone"
          type="primary"
          @click="handleDone"
        >
          {{ importError ? 'Close' : 'Complete' }}
        </el-button>
      </template>
    </el-dialog>
  </span>
</template>

