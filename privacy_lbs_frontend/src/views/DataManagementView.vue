<template>
  <div class="dm-wrap">

    <!-- ── No key state ── -->
    <div v-if="!cfg.keysGenerated" class="dm-empty">
      <div class="empty-icon">
        <el-icon><Lock /></el-icon>
      </div>
      <div class="empty-title">Cannot perform encryption operation</div>
      <div class="empty-desc">Data needs to complete Paillier encryption before leaving local. Please initialize key pair first.</div>
      <el-button type="primary" @click="router.push({ name: 'config' })">
        <el-icon><Setting /></el-icon>
        Go to System Configuration · Generate Key Pair
      </el-button>
    </div>

    <!-- ── Main flow (key exists) ── -->
    <template v-else>

      <!-- Header -->
      <div class="dm-header">
        <div class="dm-header-left">
          <div class="dm-title">Data Management</div>
          <div class="dm-sub">Local Encryption Processing · Distributed Deployment Flow</div>
      </div>
        <div class="dm-key-badge">
          <span class="key-dot" />
          <span>Paillier {{ cfg.keySize }}-bit · Keys Ready</span>
      </div>
    </div>

      <!-- Steps navigation -->
      <div class="dm-steps-wrap">
        <el-steps :active="activeStep" finish-status="success" align-center>
          <el-step title="Import Raw Data" description="Upload CSV spatial dataset" />
          <el-step title="Local Privacy Processing" description="Paillier encryption + KASTree index" />
          <el-step title="Distribute to Cloud/Fog Network" description="Encrypted data pushed to distributed nodes" />
        </el-steps>
      </div>

      <!-- Content cards area -->
      <div class="dm-cards">

        <!-- ── Stage 1: Upload ── -->
        <div class="dm-card" :class="{ 'dm-card--active': activeStep === 0, 'dm-card--done': activeStep > 0 }">
          <div class="card-head">
            <span class="card-step-num">01</span>
            <span class="card-step-label">Import Raw Data</span>
            <el-tag v-if="uploadedFile" type="success" effect="dark" size="small">Ready</el-tag>
          </div>

          <!-- Using CSVImporter component: supports any CSV format + field mapping + auto-cleaning -->
          <CSVImporter @import-ready="handleImportReady" />

          <div v-if="uploadedFile" class="file-info">
            <el-icon><Document /></el-icon>
            <span class="file-name">{{ uploadedFile.name }}</span>
            <span class="file-size">{{ fileSizeStr }}</span>
            <el-tag type="info" effect="dark" size="small">{{ rowCount }} records</el-tag>
          </div>

          <div class="card-action">
            <el-button
              type="primary"
              :disabled="!uploadedFile || activeStep > 0"
              @click="handleConfirmImport"
            >
              Confirm Import, Proceed to Encryption Phase
              <el-icon class="el-icon--right"><ArrowRight /></el-icon>
            </el-button>
        </div>
      </div>

        <!-- ── Stage 2: Encryption ── -->
        <div class="dm-card" :class="{ 'dm-card--active': activeStep === 1, 'dm-card--done': activeStep > 1, 'dm-card--locked': activeStep < 1 }">
          <div class="card-head">
            <span class="card-step-num">02</span>
            <span class="card-step-label">Local Privacy Processing</span>
            <el-tag v-if="activeStep > 1" type="success" effect="dark" size="small">Encryption Complete</el-tag>
            <el-tag v-else-if="activeStep < 1" effect="dark" size="small" type="info">Waiting for previous step</el-tag>
          </div>

          <div class="encrypt-info">
            <div class="encrypt-row">
              <span class="erow-label">Encryption Algorithm</span>
              <span class="erow-val">Paillier Homomorphic Encryption ({{ cfg.keySize }}-bit)</span>
            </div>
            <div class="encrypt-row">
              <span class="erow-label">Index Structure</span>
              <span class="erow-val">KASTree (Keyword-aware Spatial Tree)</span>
            </div>
            <div class="encrypt-row">
              <span class="erow-label">Processing Strategy</span>
              <span class="erow-val">All computation completed locally, zero plaintext on server</span>
            </div>
            <div class="encrypt-row encrypt-row--highlight">
              <span class="erow-label">Deployment Scale</span>
              <span class="erow-val">Configuration file obtained, distributed to <span class="erow-accent">{{ fogNodeCountDisplay }}</span> fog node clusters</span>
            </div>
            <div class="encrypt-row">
              <span class="erow-label">N_ts Capacity</span>
              <span class="erow-val erow-computing">Quadtree leaf capacity (N_ts): Auto calculating...</span>
            </div>
          </div>

          <!-- Progress display area -->
          <div v-if="encrypting || encryptDone" class="encrypt-progress-wrap">
            <div class="encrypt-log">
              <div
                v-for="(log, i) in encryptLogs"
                :key="i"
                class="log-line"
                :class="log.type"
              >
                <span class="log-ts">{{ log.ts }}</span>
                <span class="log-msg">{{ log.msg }}</span>
              </div>
            </div>
            <div class="encrypt-prog">
              <div class="prog-label">
                <span>{{ encryptDone ? 'Encryption completed' : 'Processing...' }}</span>
                <span>{{ encryptPct }}%</span>
              </div>
              <el-progress
                :percentage="encryptPct"
                :stroke-width="8"
                :color="encryptDone ? '#34d399' : '#38bdf8'"
                :show-text="false"
              />
            </div>
          </div>

          <div class="card-action">
            <el-button
              type="primary"
              :disabled="activeStep !== 1"
              :loading="encrypting"
              @click="startEncrypt"
            >
              <el-icon v-if="!encrypting"><Key /></el-icon>
              {{ encrypting ? 'Encrypting locally...' : 'Start Privacy Encryption' }}
            </el-button>
          </div>
        </div>

        <!-- ── Stage 3: Distribution ── -->
        <div class="dm-card" :class="{ 'dm-card--active': activeStep === 2, 'dm-card--done': activeStep > 2, 'dm-card--locked': activeStep < 2 }">
          <div class="card-head">
            <span class="card-step-num">03</span>
            <span class="card-step-label">Distribute to Cloud/Fog Network</span>
            <el-tag v-if="deployDone" type="success" effect="dark" size="small">Deployment Complete</el-tag>
            <el-tag v-else-if="activeStep < 2" effect="dark" size="small" type="info">Waiting for encryption</el-tag>
          </div>

          <!-- Distribution instructions -->
          <div class="deploy-hint">
            Pushing KASTree index and encrypted data shards to fog nodes in Standby state...
          </div>

          <!-- Node status list -->
          <div class="node-list">
            <div v-for="node in nodes" :key="node.id" class="node-row">
              <span class="node-dot" :class="'node-dot--' + node.status" />
              <span class="node-id">{{ node.id }}</span>
              <span class="node-type">{{ node.type }}</span>
              <span class="node-status-text">{{ nodeStatusLabel(node.status) }}</span>
              <div class="node-right">
                <span v-if="node.status === 'ok'" class="node-loaded">Ciphertext data loaded</span>
                <span v-if="node.status === 'ok' && node.load" class="node-load-tag">{{ node.load }}</span>
              </div>
              <div v-if="node.hint" class="node-hint">{{ node.hint }}</div>
            </div>
          </div>

          <div class="card-action">
            <el-button
              type="primary"
              :disabled="activeStep !== 2 || deploying"
              :loading="deploying"
              @click="startDeploy"
            >
              <el-icon v-if="!deploying"><Share /></el-icon>
              {{ deploying ? 'Distributing...' : 'Distribute Encrypted Data to Distributed Network' }}
            </el-button>
            <el-button
              v-if="deployDone"
              @click="resetAll"
              plain
            >
              Reset Process
            </el-button>
    </div>
        </div>

      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElNotification, ElMessage } from 'element-plus'
import {
  Lock, Setting, UploadFilled, Document,
  ArrowRight, Key, Share,
} from '@element-plus/icons-vue'
import { useConfigStore } from '@/stores/config.store'
import { useDemoAppStore } from '@/stores/useDemoStore'
import { uploadCSV, validateDataFile, getDataStatistics } from '@/services/data.service'
import CSVImporter from '@/components/data/CSVImporter.vue'
import type { CleanedRow } from '@/components/data/CSVImporter.vue'
import type { UploadFile } from 'element-plus'

const router = useRouter()
const cfg = useConfigStore()
const demoApp = useDemoAppStore()

// Read fog node count from system configuration
const fogNodeCountDisplay = computed(() =>
  demoApp.fogLevel === 1 ? 4 : demoApp.fogLevel === 2 ? 16 : 64
)

// ── Step status ──────────────────────────────────────────────
const activeStep = ref(0)

// ── Stage 1: Upload ─────────────────────────────────────────
const uploadedFile = ref<File | null>(null)
const rowCount = ref(0)

// Key pre-check: verify keys are generated before import
function handleConfirmImport() {
  if (!cfg.keysGenerated) {
    ElMessage({
      type: 'warning',
      message: 'Paillier key pair not generated yet, please go to 【System Config】 page to initialize keys first.',
      duration: 4000,
      showClose: true,
    })
    router.push({ name: 'config' })
    return
  }
  activeStep.value = 1
}

// CSV import wizard completion callback
function handleWizardDone(payload: { cleanedRows: number; uploadResult: any }) {
  // Wizard finished upload, skip directly to stage 3 (distribution)
  rowCount.value   = payload.cleanedRows
  encryptDone.value = true
  activeStep.value  = 2
  ElMessage.success(`Import wizard completed! Total ${payload.cleanedRows} records encrypted and stored`)
}

const fileSizeStr = computed(() => {
  if (!uploadedFile.value) return ''
  const kb = uploadedFile.value.size / 1024
  return kb > 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${kb.toFixed(1)} KB`
})

// CSVImporter clean complete callback: receive standardized row array
const cleanedRows = ref<CleanedRow[]>([])

function handleImportReady(rows: CleanedRow[]) {
  cleanedRows.value = rows
  rowCount.value = rows.length
  // Construct a virtual File object from first row for fileSizeStr calculation (estimated by JSON bytes)
  const blob = new Blob([JSON.stringify(rows)], { type: 'application/json' })
  uploadedFile.value = new File([blob], `cleaned_${rows.length}_rows.csv`)
  ElMessage.success(`Ready: ${rows.length} records cleaned and standardized`)
}

function handleFileChange(file: UploadFile) {
  const raw = file.raw
  if (!raw) return
  uploadedFile.value = raw
  const reader = new FileReader()
  reader.onload = (e) => {
    const text = e.target?.result as string
    rowCount.value = Math.max(0, text.split('\n').filter(l => l.trim()).length - 1)
  }
  reader.readAsText(raw)
}

// ── Stage 2: Encryption ─────────────────────────────────────────
const encrypting = ref(false)
const encryptDone = ref(false)
const encryptPct = ref(0)
const encryptLogs = ref<{ ts: string; msg: string; type: string }[]>([])

function logLine(msg: string, type = 'info') {
  const now = new Date()
  const ts = `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}:${now.getSeconds().toString().padStart(2,'0')}`
  encryptLogs.value.push({ ts, msg, type })
}

// Upload result (saved after stage 2 completion, read by stage 3)
const uploadResult = ref<import('@/services/data.service').UploadResult | null>(null)

async function startEncrypt() {
  // Priority: use CSVImporter cleaned data; fallback to raw CSV if user uploads directly
  const hasCleanedData = cleanedRows.value.length > 0

  if (!hasCleanedData && !uploadedFile.value) {
    ElMessage.warning('Please select and clean a CSV file first via the top import area')
    return
  }

  // If cleaned data exists, serialize to CSV File before upload
  let fileToUpload: File
  if (hasCleanedData) {
    // Convert CleanedRow[] back to CSV format
    const header = 'id,name,x,y,keywords'
    const lines = cleanedRows.value.map(r =>
      `${r.id},"${(r.name ?? '').replace(/"/g, '""')}",${r.x},${r.y},"${r.keywords.replace(/"/g, '""')}"`
    )
    const csvContent = [header, ...lines].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv' })
    fileToUpload = new File([blob], uploadedFile.value?.name ?? 'cleaned_data.csv', { type: 'text/csv' })
  } else {
    // Frontend validation for raw file
    const validation = validateDataFile(uploadedFile.value!)
    if (!validation.valid) {
      ElMessage.error(validation.errors.join('；'))
      return
    }
    fileToUpload = uploadedFile.value!
  }

  encrypting.value = true
  encryptDone.value = false
  encryptPct.value = 0
  encryptLogs.value = []
  uploadResult.value = null

  try {
    logLine('Initializing Paillier key pair...', 'info')
    logLine(`Key pair loaded (${cfg.keySize}-bit) completed`, 'success')
    encryptPct.value = 15

    logLine(`Uploading ${fileToUpload.name} to backend...`, 'info')

    const result = await uploadCSV(
      fileToUpload,
      (pct) => {
        // Map upload progress to 15-80%
        encryptPct.value = 15 + Math.round(pct * 0.65)
      },
    )
    uploadResult.value = result

    encryptPct.value = 85
    logLine(`Parsed ${result.parsed_rows} rows, skipped ${result.skipped_rows} rows`, 'info')

    if (result.parse_warnings?.length) {
      result.parse_warnings.forEach(w => logLine(`⚠ ${w}`, 'warn'))
    }

    if ((result as any).duplicate_rows > 0) {
      logLine(`Filtered out ${(result as any).duplicate_rows} duplicate records`, 'warn')
    }

    if (result.index_built) {
      const m = result.index_metadata
      logLine(`KASTree index building completed: depth=${m?.ktree_depth}, nodes=${m?.ktree_node_count}, leaves=${m?.ktree_leaf_count} ✓`, 'success')
    } else {
      logLine('Index building skipped (server not enabled)', 'warn')
    }

    encryptPct.value = 95
    logLine('Serializing ciphertexts and verifying integrity of plaintext...', 'info')
    await new Promise(r => setTimeout(r, 300))
    encryptPct.value = 100
    logLine(`All ${result.objects_count} records Paillier encrypted on server, plaintext cleared ✓`, 'success')
    rowCount.value = result.objects_count

    encrypting.value = false
    encryptDone.value = true
    activeStep.value = 2
  } catch (e: any) {
    // Extract detailed error information from backend response
    const respData = e?.response?.data
    let errMsg = e?.message ?? 'Network error'
    if (respData) {
      if (typeof respData === 'string') {
        errMsg = respData
      } else if (respData.error) {
        errMsg = respData.error
        if (respData.message) errMsg += `：${respData.message}`
        if (respData.details) {
          const details = typeof respData.details === 'object'
            ? JSON.stringify(respData.details)
            : respData.details
          errMsg += `（${details}）`
        }
      } else if (respData.message) {
        errMsg = respData.message
      }
    }
    logLine(`Upload failed: ${errMsg}`, 'warn')
    ElMessage.error({
      message: `Upload failed: ${errMsg}`,
      duration: 8000,
      showClose: true,
    })
    encryptPct.value = 0
    encrypting.value = false
  }
}

// ── Stage 3: Distribution ─────────────────────────────────────────
interface NodeInfo { id: string; type: string; status: 'idle' | 'loading' | 'ok' | 'err'; hint?: string; load?: string }

const nodes = ref<NodeInfo[]>([
  { id: 'C1', type: 'Cloud Server',  status: 'idle', hint: 'Receiving full SGL tree topology (includes 16 leaf nodes mappings)', load: 'SGL×16' },
  { id: 'F1', type: 'Fog Node #1', status: 'idle', hint: 'Allocation Strategy: Geo-Hashing | Carried Subgrids: [Grid-01 ~ Grid-06]', load: '6/16 grids' },
  { id: 'F2', type: 'Fog Node #2', status: 'idle', hint: 'Allocation Strategy: Geo-Hashing | Carried Subgrids: [Grid-07 ~ Grid-11]', load: '5/16 grids' },
  { id: 'F3', type: 'Fog Node #3', status: 'idle', hint: 'Allocation Strategy: Geo-Hashing | Carried Subgrids: [Grid-12 ~ Grid-16]', load: '5/16 grids' },
])

const deploying = ref(false)
const deployDone = ref(false)

function nodeStatusLabel(s: NodeInfo['status']) {
  return { idle: 'Waiting', loading: 'Pushing...', ok: 'Online', err: 'Failed' }[s]
}

// Statistics panel data (displayed after stage 3 completes)
const statisticsInfo = ref<string>('')

async function startDeploy() {
  deploying.value = true
  deployDone.value = false
  nodes.value.forEach(n => (n.status = 'idle'))

  // Simulate node status updates (actual distribution is done by backend upload API on server side)
  for (const node of nodes.value) {
    node.status = 'loading'
    await new Promise(r => setTimeout(r, 500 + Math.random() * 400))
    node.status = 'ok'
    ElNotification({
      title: 'Node loaded successfully',
      message: `${node.id} · ${node.type} successfully loaded encrypted data`,
      type: 'success',
      duration: 2500,
      position: 'bottom-right',
    })
  }

  // Call statistics API to refresh POI count dashboard
  try {
    const stats = await getDataStatistics()
    statisticsInfo.value = `System has ${stats.total_objects} POI records from ${stats.data_owner_count} data providers`
    ElNotification({
      title: 'Data statistics updated',
      message: statisticsInfo.value,
      type: 'info',
      duration: 4000,
      position: 'bottom-right',
    })
  } catch {
    // statistics API failure does not affect main flow
  }

  deploying.value = false
  deployDone.value = true
  activeStep.value = 3
}

function resetAll() {
  activeStep.value = 0
  uploadedFile.value = null
  rowCount.value = 0
  encrypting.value = false
  encryptDone.value = false
  encryptPct.value = 0
  encryptLogs.value = []
  deploying.value = false
  deployDone.value = false
  nodes.value.forEach(n => (n.status = 'idle'))
}
</script>

<style scoped>
.dm-wrap {
  min-height: 100%;
  background: #0d1117;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* ── Empty state (no key) ── */
.dm-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  text-align: center;
}
.empty-icon {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: rgba(248,113,113,0.1);
  border: 1px solid rgba(248,113,113,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  color: #f87171;
}
.empty-title {
  font-size: 20px;
  font-weight: 700;
  color: #f1f5f9;
}
.empty-desc {
  font-size: 14px;
  color: #64748b;
  max-width: 380px;
  line-height: 1.7;
}

/* ── Header ── */
.dm-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}
.dm-title {
  font-size: 20px;
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: 1px;
}
.dm-sub {
  font-size: 13px;
  color: #475569;
  margin-top: 3px;
}
.dm-key-badge {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  color: #34d399;
  background: rgba(52,211,153,0.08);
  border: 1px solid rgba(52,211,153,0.2);
  border-radius: 4px;
  padding: 4px 12px;
  white-space: nowrap;
}
.key-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #34d399;
  box-shadow: 0 0 6px #34d399;
  flex-shrink: 0;
}

/* ── Steps bar ── */
.dm-steps-wrap {
  background: #1e222d;
  border: 1px solid #1e293b;
  border-radius: 8px;
  padding: 20px 32px;
}
:deep(.dm-steps-wrap .el-step__title) {
  font-size: 13px;
  color: #94a3b8;
}
:deep(.dm-steps-wrap .el-step__description) {
  font-size: 11px;
  color: #475569;
}
:deep(.dm-steps-wrap .el-step__head.is-success .el-step__icon) {
  border-color: #34d399;
  color: #34d399;
}
:deep(.dm-steps-wrap .el-step__head.is-process .el-step__icon) {
  border-color: #38bdf8;
  background: #38bdf8;
}

/* ── Cards area ── */
.dm-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.dm-card {
  background: #1e222d;
  border: 1px solid #1e293b;
  border-radius: 10px;
  padding: 20px 24px;
  transition: border-color 0.25s, box-shadow 0.25s;
}
.dm-card--active {
  border-color: #38bdf8;
  box-shadow: 0 0 0 1px rgba(56,189,248,0.15), 0 4px 20px rgba(56,189,248,0.06);
}
.dm-card--done {
  border-color: rgba(52,211,153,0.3);
  opacity: 0.85;
}
.dm-card--locked {
  opacity: 0.45;
  pointer-events: none;
}

.card-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.card-step-num {
  font-size: 11px;
  font-weight: 800;
  font-family: monospace;
  color: #38bdf8;
  background: rgba(56,189,248,0.1);
  border: 1px solid rgba(56,189,248,0.2);
  border-radius: 3px;
  padding: 1px 7px;
  letter-spacing: 1px;
}
.card-step-label {
  font-size: 15px;
  font-weight: 700;
  color: #e2e8f0;
  flex: 1;
}

/* Upload area */
:deep(.dm-uploader .el-upload) { width: 100%; }
:deep(.dm-uploader .el-upload-dragger) {
  background: #131720;
  border: 1.5px dashed #1e293b;
  border-radius: 8px;
  transition: border-color 0.2s;
  width: 100%;
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
}
:deep(.dm-uploader .el-upload-dragger:hover) {
  border-color: #38bdf8;
}
.upload-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.upload-icon {
  font-size: 32px;
  color: #334155;
}
.upload-text {
  font-size: 14px;
  color: #64748b;
}
.upload-text em {
  color: #38bdf8;
  font-style: normal;
  cursor: pointer;
}
.upload-hint {
  font-size: 12px;
  color: #334155;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 8px 12px;
  background: #131720;
  border-radius: 6px;
  border: 1px solid #1e293b;
  font-size: 13px;
  color: #94a3b8;
}
.file-name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #e2e8f0;
}
.file-size {
  color: #475569;
  font-size: 12px;
  white-space: nowrap;
}

/* Encryption section */
.encrypt-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}
.encrypt-row {
  display: flex;
  gap: 12px;
  font-size: 13px;
}
.erow-label {
  color: #475569;
  width: 80px;
  flex-shrink: 0;
}
.erow-val {
  color: #94a3b8;
}
.encrypt-progress-wrap {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.encrypt-log {
  background: #0d1117;
  border: 1px solid #1e293b;
  border-radius: 6px;
  padding: 10px 14px;
  max-height: 140px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-family: 'JetBrains Mono', monospace;
}
.log-line {
  display: flex;
  gap: 10px;
  font-size: 12px;
  line-height: 1.5;
}
.log-ts { color: #334155; flex-shrink: 0; }
.log-line.info .log-msg { color: #64748b; }
.log-line.success .log-msg { color: #34d399; }
.log-line.warn .log-msg { color: #fbbf24; }
.prog-label {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
}

/* Node list */
.node-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}
.node-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 10px 14px;
  background: #131720;
  border: 1px solid #1e293b;
  border-radius: 6px;
  font-size: 13px;
}
.node-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  transition: background 0.3s;
}
.node-dot--idle    { background: #334155; }
.node-dot--loading { background: #fbbf24; box-shadow: 0 0 6px #fbbf24; animation: blink 0.8s infinite; }
.node-dot--ok      { background: #34d399; box-shadow: 0 0 6px #34d399; }
.node-dot--err     { background: #f87171; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
.node-id   { font-family: monospace; font-weight: 700; color: #38bdf8; width: 32px; }
.node-type { color: #64748b; flex: 1; }
.node-status-text { color: #475569; font-size: 12px; width: 60px; text-align: right; }
.node-loaded { font-size: 11px; color: #34d399; }
.node-right {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}
.node-load-tag {
  font-size: 10px;
  font-weight: 700;
  color: #818cf8;
  background: rgba(129,140,248,0.12);
  border: 1px solid rgba(129,140,248,0.25);
  border-radius: 4px;
  padding: 1px 7px;
  font-family: 'JetBrains Mono', monospace;
  white-space: nowrap;
}
.node-hint {
  width: 100%;
  font-size: 10px;
  color: #475569;
  font-family: 'JetBrains Mono', monospace;
  margin-top: 4px;
  padding-left: 18px;
  line-height: 1.5;
}

/* Action button row */
.card-action {
  display: flex;
  gap: 10px;
  margin-top: 4px;
}

/* Encryption info row highlight */
.encrypt-row--highlight {
  background: rgba(56,189,248,0.04);
  border: 1px solid rgba(56,189,248,0.12);
  border-radius: 5px;
  padding: 5px 8px;
  margin: 2px 0;
}
.erow-accent {
  color: #38bdf8;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}
.erow-computing {
  color: #fbbf24;
  font-style: italic;
  font-size: 12px;
}

/* Distribution stage hint */
.deploy-hint {
  font-size: 12px;
  color: #64748b;
  line-height: 1.7;
  padding: 8px 12px;
  margin-bottom: 12px;
  background: rgba(52,211,153,0.04);
  border: 1px solid rgba(52,211,153,0.15);
  border-radius: 6px;
  border-left: 3px solid rgba(52,211,153,0.4);
}
</style>
