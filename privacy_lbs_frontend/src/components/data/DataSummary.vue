<template>
  <div class="data-summary">
    <div class="summary-header">
      <h3 class="title">Data Overview</h3>
      <div class="header-actions">
        <el-button size="small" @click="handleExport" :disabled="!queryStore.uploadedPOIs.length">
          <el-icon><Download /></el-icon> Export encrypted data
        </el-button>
        <el-button size="small" type="danger" plain @click="handleClear" :disabled="!queryStore.uploadedPOIs.length">
          <el-icon><Delete /></el-icon> Clear data
        </el-button>
      </div>
    </div>
    <div class="stat-cards">
      <div class="stat-card">
        <el-statistic title="Total POI count" :value="queryStore.uploadedPOIs.length">
          <template #prefix><el-icon><Location /></el-icon></template>
        </el-statistic>
      </div>
      <div class="stat-card">
        <el-statistic title="Encrypted POI count" :value="queryStore.encryptedPOICount" />  
        <el-tag :type="allEncrypted ? 'success' : 'warning'" size="small" style="margin-top:8px">
          {{ allEncrypted ? '✅ All encrypted completed' : '⚠️ Partial encrypted pending' }}
        </el-tag>
      </div>
      <div class="stat-card"><el-statistic title="Category count" :value="categoryCount" /></div>
      <div class="stat-card"><el-statistic title="Encryption time" :value="queryStore.totalEncryptionTimeMs" suffix=" ms" /></div>  
    </div>
    <el-empty v-if="!queryStore.uploadedPOIs.length" description="No data available, please upload POI file first" :image-size="80" />
    <template v-else>
      <div class="section">
        <div class="section-title">Category statistics</div>
        <div class="category-list">
          <div v-for="(count, cat) in queryStore.poiCategoryStats" :key="cat" class="category-item">
            <span class="cat-name">{{ cat }}</span>
            <el-progress :percentage="Math.round((count/queryStore.uploadedPOIs.length)*100)" :stroke-width="10" style="flex:1;margin:0 12px" />
            <span class="cat-count">{{ count }}</span>
          </div>
        </div>
      </div>
      <div class="section">
        <div class="section-title">Recent uploads records</div>
        <el-table :data="recentPOIs" size="small" max-height="200" style="width:100%">
          <el-table-column prop="id" label="ID" width="100" show-overflow-tooltip />
          <el-table-column prop="name" label="Name" min-width="120" show-overflow-tooltip />
          <el-table-column prop="category" label="Category" width="90" show-overflow-tooltip />
          <el-table-column label="Encryption status" width="90">
            <template #default="{ row }">
              <el-tag :type="row.encrypted ? 'success' : 'warning'" size="small">
                {{ row.encrypted ? 'Encrypted' : 'Not encrypted' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Download, Delete, Location } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useQueryStore } from '@/stores/query.store';

const queryStore = useQueryStore();

const allEncrypted = computed(() =>
  queryStore.uploadedPOIs.length > 0 &&
  queryStore.encryptedPOICount === queryStore.uploadedPOIs.length
);
const categoryCount = computed(() => Object.keys(queryStore.poiCategoryStats).length);
const recentPOIs = computed(() => [...queryStore.uploadedPOIs].slice(0, 20));

function handleExport() {
  const data = queryStore.uploadedPOIs.map(p => ({ ...p }));
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'encrypted_pois_' + Date.now() + '.json';
  a.click();
  URL.revokeObjectURL(url);
  ElMessage.success('Export successful');
}

async function handleClear() {
  try {
    await ElMessageBox.confirm('Are you sure to want to clear all POI data?', 'Clear data', { type: 'warning' });
    queryStore.clearData();
    ElMessage.success('Data cleared');
  } catch { /* cancelled */ }
}
</script>

<style scoped>
.data-summary { display: flex; flex-direction: column; gap: 20px; height: 100%; overflow-y: auto; }
.summary-header { display: flex; align-items: center; justify-content: space-between; }
.summary-header .title { margin: 0; font-size: 16px; font-weight: 600; color: var(--el-text-color-primary); }
.header-actions { display: flex; gap: 8px; }
.stat-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.stat-card { background: var(--el-fill-color-light); border-radius: 8px; padding: 16px; }
.section { background: var(--el-fill-color-light); border-radius: 8px; padding: 16px; }
.section-title { font-size: 14px; font-weight: 500; color: var(--el-text-color-primary); margin-bottom: 12px; }
.category-list { display: flex; flex-direction: column; gap: 8px; }
.category-item { display: flex; align-items: center; }
.cat-name { width: 80px; font-size: 13px; color: var(--el-text-color-regular); flex-shrink: 0; }
.cat-count { width: 40px; text-align: right; font-size: 13px; color: var(--el-text-color-secondary); }
</style>
