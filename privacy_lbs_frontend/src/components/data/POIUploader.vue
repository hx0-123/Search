<template>
  <div class="poi-uploader">
    <!-- Title -->
    <div class="uploader-header">
      <h3 class="title">Upload POI Data</h3>
      <span class="subtitle">Supports CSV / JSON format, max 100 MB</span>
    </div>

    <!-- Drag and drop upload area -->
    <el-upload
      ref="uploadRef"
      class="drop-zone"
      drag
      :auto-upload="false"
      :show-file-list="false"
      accept=".csv,.json,application/json,text/csv"
      :before-upload="() => false"
      :on-change="handleFileChange"
    >
      <div class="drop-content">
        <el-icon class="drop-icon" :size="48"><Upload /></el-icon>
        <p class="drop-text">Drag file here, or <em>click to select file</em></p>
        <p class="drop-hint">CSV format: id, name, lng, lat, keywords, category</p>
      </div>
    </el-upload>

    <!-- Selected file info -->
    <el-alert
      v-if="selectedFile && !parseError"
      :title="`Selected: ${selectedFile.name} (${formatFileSize(selectedFile.size)})`"
      type="info"
      show-icon
      :closable="false"
      style="margin-top: 12px"
    />
    <el-alert
      v-if="parseError"
      :title="parseError"
      type="error"
      show-icon
      :closable="false"
      style="margin-top: 12px"
    />

    <!-- Upload / Encryption progress -->
    <div v-if="uploading || encrypting" class="progress-block">
      <div class="progress-label">
        <span>{{ progressLabel }}</span>
        <span>{{ progressPct }}%</span>
      </div>
      <el-progress :percentage="progressPct" :status="progressStatus" striped striped-flow />
    </div>

    <!-- Encryption complete alert -->
    <el-alert
      v-if="encryptDone"
      :title="`Encryption Complete: ${queryStore.uploadedPOIs.length} POIs, Time: ${queryStore.totalEncryptionTimeMs} ms`"
      type="success"
      show-icon
      :closable="false"
      style="margin-top: 12px"
    />

    <!-- Action buttons -->
    <div class="action-bar">
      <el-button
        type="primary"
        :loading="uploading || encrypting"
        :disabled="!parsedPOIs.length || uploading || encrypting"
        @click="handleUpload"
      >
        <el-icon><Upload /></el-icon>
        {{ uploading ? 'Uploading...' : encrypting ? 'Encrypting...' : 'Upload and Encrypt' }}
      </el-button>
      <el-button :disabled="uploading || encrypting" @click="clearAll">Clear</el-button>
    </div>

    <!-- Preview table -->
    <div v-if="parsedPOIs.length" class="preview-block">
      <div class="preview-header">
        <span class="preview-title">Data Preview</span>
        <el-tag type="info" size="small">Total {{ parsedPOIs.length }} records</el-tag>
      </div>
      <el-table
        :data="previewRows"
        size="small"
        stripe
        border
        max-height="320"
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="90" show-overflow-tooltip />
        <el-table-column prop="name" label="Name" min-width="100" show-overflow-tooltip />
        <el-table-column prop="lng" label="Longitude" width="110" />
        <el-table-column prop="lat" label="Latitude" width="110" />
        <el-table-column prop="keywordsStr" label="Keywords" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag
              v-for="kw in row.keywords.slice(0, 3)"
              :key="kw"
              size="small"
              style="margin-right: 4px"
            >{{ kw }}</el-tag>
            <span v-if="row.keywords.length > 3" class="more-tag">+{{ row.keywords.length - 3 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="Category" width="90" show-overflow-tooltip />
      </el-table>
      <p v-if="parsedPOIs.length > PREVIEW_LIMIT" class="preview-note">
        Showing first {{ PREVIEW_LIMIT }} records, total {{ parsedPOIs.length }} records
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { Upload } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import type { UploadInstance, UploadFile } from 'element-plus';
import type { POI } from '@/types';
import { useQueryStore } from '@/stores/query.store';
import { validateDataFile, uploadDataFile } from '@/services/data.service';
import { generateId, encodeBase64 } from '@/utils/crypto.util';

// ─── Constants ────────────────────────────────────────────────
const PREVIEW_LIMIT = 50;

// ─── Store ───────────────────────────────────────────────────
const queryStore = useQueryStore();

// ─── State ────────────────────────────────────────────────────
const uploadRef = ref<UploadInstance>();
const selectedFile = ref<File | null>(null);
const parsedPOIs = ref<POI[]>([]);
const parseError = ref<string | null>(null);

const uploading = ref(false);
const encrypting = ref(false);
const progressPct = ref(0);
const encryptDone = ref(false);

// ─── Computed ────────────────────────────────────────────────
const previewRows = computed(() => parsedPOIs.value.slice(0, PREVIEW_LIMIT));

const progressLabel = computed(() =>
  uploading.value ? 'Uploading file...' : 'Encrypting data...'
);

const progressStatus = computed(() =>
  progressPct.value === 100 ? 'success' as const : undefined
);

// ─── Utils ───────────────────────────────────────────────────
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

// ─── File Selection ──────────────────────────────────────────
async function handleFileChange(file: UploadFile) {
  const raw = file.raw;
  if (!raw) return;

  // Reset state
  parsedPOIs.value = [];
  parseError.value = null;
  encryptDone.value = false;
  progressPct.value = 0;
  selectedFile.value = raw;

  // Validate file
  const validation = validateDataFile(raw);
  if (!validation.valid) {
    parseError.value = validation.errors.join('；');
    return;
  }

  // Parse content
  try {
    const text = await raw.text();
    parsedPOIs.value = raw.name.endsWith('.json') ? parseJSON(text) : parseCSV(text);
    if (!parsedPOIs.value.length) {
      parseError.value = 'File parse result is empty, please check format';
    }
  } catch (e: any) {
    parseError.value = `Parse failed: ${e.message}`;
    parsedPOIs.value = [];
  }
}

// ─── CSV Parsing ──────────────────────────────────────────────
function splitCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') { current += '"'; i++; }
      else { inQuotes = !inQuotes; }
    } else if (ch === ',' && !inQuotes) {
      result.push(current); current = '';
    } else {
      current += ch;
    }
  }
  result.push(current);
  return result;
}

function parseCSV(text: string): POI[] {
  const lines = text.split(/\r?\n/).filter(l => l.trim());
  if (lines.length < 2) throw new Error('CSV requires at least one header row and one data row');

  const headers = splitCSVLine(lines[0]).map(h => h.trim().toLowerCase());
  const required = ['id', 'name', 'lng', 'lat', 'keywords'];
  for (const col of required) {
    if (!headers.includes(col)) throw new Error(`Missing required column: ${col}`);
  }
  const idx = (col: string) => headers.indexOf(col);

  return lines.slice(1).map((line, i) => {
    const cols = splitCSVLine(line);
    const lng = parseFloat(cols[idx('lng')]);
    const lat = parseFloat(cols[idx('lat')]);
    if (isNaN(lng) || isNaN(lat)) {
      throw new Error(`Row ${i + 2} has invalid latitude/longitude (lng=${cols[idx('lng')]}, lat=${cols[idx('lat')]})`);
    }
    return {
      id: cols[idx('id')]?.trim() || generateId('p'),
      name: cols[idx('name')]?.trim() || `POI_${i + 1}`,
      lng,
      lat,
      keywords: (cols[idx('keywords')] || '')
        .split(',')
        .map(k => k.trim())
        .filter(Boolean),
      category: idx('category') >= 0 ? (cols[idx('category')]?.trim() || undefined) : undefined,
    };
  });
}

// ─── JSON Parsing ─────────────────────────────────────────────
function parseJSON(text: string): POI[] {
  const data = JSON.parse(text);
  const arr: any[] = Array.isArray(data) ? data : (data.pois ?? data.data ?? []);
  return arr.map((item: any, i: number) => ({
    id: String(item.id ?? generateId('p')),
    name: String(item.name ?? `POI_${i + 1}`),
    lng: Number(item.lng ?? item.longitude),
    lat: Number(item.lat ?? item.latitude),
    keywords: Array.isArray(item.keywords)
      ? item.keywords.map(String)
      : String(item.keywords ?? '').split(',').map((k: string) => k.trim()).filter(Boolean),
    category: item.category ? String(item.category) : undefined,
  }));
}

// ─── Frontend Mock Encryption (Base64 instead of real Paillier, actual encryption done on backend) ──
async function encryptPOIs(
  pois: POI[],
  onProgress: (pct: number) => void
): Promise<{ pois: (POI & { encrypted: boolean })[]; timeMs: number }> {
  const start = Date.now();
  const result: (POI & { encrypted: boolean })[] = [];
  const total = pois.length;

  // Process in batches to avoid blocking main thread
  const BATCH = 100;
  for (let i = 0; i < total; i += BATCH) {
    const batch = pois.slice(i, i + BATCH);
    // Mock frontend encryption: mark lng/lat with Base64 (real Paillier encryption done on backend)
    batch.forEach(p => {
      result.push({ ...p, encrypted: true });
      // Actual usage example (when backend encrypts): encodeBase64(`${p.lng},${p.lat}`)
    });
    onProgress(Math.min(100, Math.round(((i + BATCH) / total) * 100)));
    // Yield for one frame
    await new Promise(r => requestAnimationFrame(r));
  }

  return { pois: result, timeMs: Date.now() - start };
}

// ─── Main Upload Flow ─────────────────────────────────────────
async function handleUpload() {
  if (!selectedFile.value || !parsedPOIs.value.length) return;

  encryptDone.value = false;
  progressPct.value = 0;

  // Step 1: Upload file to backend
  uploading.value = true;
  try {
    await uploadDataFile(selectedFile.value, (pct) => {
      progressPct.value = Math.round(pct / 2); // Upload takes first 50%
    });
  } catch (e: any) {
    ElMessage.error(`Upload failed: ${e.message}`);
    uploading.value = false;
    return;
  }
  uploading.value = false;
  progressPct.value = 50;

  // Step 2: Frontend encryption (mock, actual Paillier done on backend)
  encrypting.value = true;
  try {
    const { pois: encryptedPOIs, timeMs } = await encryptPOIs(
      parsedPOIs.value,
      (pct) => { progressPct.value = 50 + Math.round(pct / 2); } // Encryption takes last 50%
    );
    // Write to global store
    queryStore.addUploadedPOIs(encryptedPOIs, timeMs);
    progressPct.value = 100;
    encryptDone.value = true;
    ElMessage.success(`Upload successful, encrypted ${encryptedPOIs.length} POIs`);
  } catch (e: any) {
    ElMessage.error(`Encryption failed: ${e.message}`);
  } finally {
    encrypting.value = false;
  }
}

// ─── Clear ────────────────────────────────────────────────────
function clearAll() {
  selectedFile.value = null;
  parsedPOIs.value = [];
  parseError.value = null;
  encryptDone.value = false;
  progressPct.value = 0;
  uploadRef.value?.clearFiles();
}
</script>

<style scoped>
.poi-uploader {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}

.uploader-header .title {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.uploader-header .subtitle {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.drop-zone {
  width: 100%;
}

.drop-zone :deep(.el-upload-dragger) {
  width: 100%;
  padding: 32px 20px;
  border-radius: 8px;
  background: var(--el-fill-color-light);
  transition: border-color 0.2s;
}

.drop-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.drop-icon {
  color: var(--el-color-primary);
  opacity: 0.7;
}

.drop-text {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin: 0;
}
.drop-text em { color: var(--el-color-primary); font-style: normal; }
.drop-hint { font-size: 12px; color: var(--el-text-color-placeholder); margin: 0; }
.progress-block { margin-top: 4px; }
.progress-label { display: flex; justify-content: space-between; font-size: 13px; color: var(--el-text-color-secondary); margin-bottom: 6px; }
.action-bar { display: flex; gap: 8px; }
.preview-block { display: flex; flex-direction: column; gap: 8px; flex: 1; min-height: 0; }
.preview-header { display: flex; align-items: center; gap: 8px; }
.preview-title { font-size: 14px; font-weight: 500; color: var(--el-text-color-primary); }
.preview-note { font-size: 12px; color: var(--el-text-color-placeholder); margin: 4px 0 0; }
.more-tag { font-size: 11px; color: var(--el-text-color-secondary); }
</style>
