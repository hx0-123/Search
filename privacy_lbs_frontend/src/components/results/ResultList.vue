<!--
  Result List Component
  Directly renders plaintext query results returned from backend (C2 has completed decryption in cloud)
-->
<template>
  <el-card class="result-list-card">
    <template #header>
      <div class="card-header">
        <span>Query Results ({{ dedupedResults.length }}{{ dedupedResults.length < resultStore.resultCount ? ' · deduplicated' : '' }})</span>
        <div class="header-actions">
          <el-button
            type="danger"
            link
            size="small"
            :loading="clearing"
            @click="handleClearDB"
          >
            Clear Database
          </el-button>
          <el-button
            type="primary"
            link
            size="small"
            @click="handleClear"
            v-if="resultStore.hasResults"
          >
            Clear Results
          </el-button>
        </div>
      </div>
    </template>

    <div v-if="!resultStore.hasResults" class="empty-state">
      <el-empty description="No query results" />
    </div>

    <template v-else>
      <!-- Sort and Filter -->
      <div class="toolbar">
        <el-select
          v-model="sortField"
          placeholder="Sort by"
          size="small"
          style="width: 120px"
          @change="handleSortChange"
        >
          <el-option label="By Score" value="score" />
          <el-option label="By Distance" value="distance" />
          <el-option label="By Name" value="name" />
        </el-select>

        <el-button-group style="margin-left: 8px">
          <el-button
            size="small"
            :type="sortOrder === 'asc' ? 'primary' : 'default'"
            @click="handleToggleOrder"
          >
            <el-icon><ArrowUp /></el-icon>
          </el-button>
          <el-button
            size="small"
            :type="sortOrder === 'desc' ? 'primary' : 'default'"
            @click="handleToggleOrder"
          >
            <el-icon><ArrowDown /></el-icon>
          </el-button>
        </el-button-group>

        <el-input
          v-model="filterKeyword"
          placeholder="Filter results..."
          size="small"
          clearable
          style="width: 150px; margin-left: 8px"
          @input="handleFilterChange"
        />
      </div>

      <!-- Result List -->
      <div class="result-list">
        <ResultItem
          v-for="(result, index) in visibleResults"
          :key="result.id"
          :result="result"
          :index="index"
          :selected="result.id === resultStore.selectedResult?.id"
          @click="handleSelectResult(result)"
        />
      </div>
    </template>
  </el-card>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { ArrowUp, ArrowDown } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useResultStore } from '@/stores/result.store';
import { useMapStore } from '@/stores/map.store';
import ResultItem from './ResultItem.vue';
import type { QueryResult } from '@/types';
import { api } from '@/services/api.client';

const resultStore = useResultStore();
const mapStore = useMapStore();
const clearing = ref(false);

// -- Frontend deduplication: deduplicate by name + coordinates (2 decimal places) --
const dedupedResults = computed(() => {
  const seen = new Set<string>();
  return resultStore.sortedResults.filter(r => {
    const lon  = r.spatialObject.location.longitude.toFixed(2);
    const lat  = r.spatialObject.location.latitude.toFixed(2);
    const name = (r.spatialObject.name ?? '').trim().toLowerCase();
    const key  = `${name}|${lon}|${lat}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
});

async function handleClearDB() {
  try {
    await ElMessageBox.confirm(
      'This operation will clear all POI ciphertext data from the database and cannot be undone. Continue?',
      'Clear Database',
      { confirmButtonText: 'Confirm Clear', cancelButtonText: 'Cancel', type: 'warning' }
    );
  } catch {
    return;
  }
  clearing.value = true;
  try {
    const res = await api.post('/data/clear/');
    ElMessage.success(res.data?.message ?? 'Database cleared successfully, please re-upload data');
    resultStore.clearResults();
  } catch (e: any) {
    const msg = e?.response?.data?.message ?? e?.message ?? 'Request failed';
    ElMessage.error(`Clear failed: ${msg}`);
  } finally {
    clearing.value = false;
  }
}

const sortField    = ref<'score' | 'distance' | 'name'>('score');
const sortOrder    = ref<'asc' | 'desc'>('desc');
const filterKeyword = ref('');

const MAX_VISIBLE_RESULTS = 20;
const visibleResults = computed(() =>
  dedupedResults.value.slice(0, MAX_VISIBLE_RESULTS)
);

watch(() => resultStore.sortField,   v => { sortField.value    = v; }, { immediate: false });
watch(() => resultStore.sortOrder,   v => { sortOrder.value    = v; }, { immediate: false });
watch(() => resultStore.filterKeyword, v => { filterKeyword.value = v; }, { immediate: false });

function handleSortChange(field: 'score' | 'distance' | 'name') {
  resultStore.setSort(field, sortOrder.value);
}
function handleToggleOrder() {
  const newOrder = sortOrder.value === 'asc' ? 'desc' : 'asc';
  sortOrder.value = newOrder;
  resultStore.setSort(sortField.value, newOrder);
}
function handleFilterChange(value: string) {
  resultStore.setFilterKeyword(value);
}
function handleSelectResult(result: QueryResult) {
  resultStore.setSelectedResult(result);
  if (mapStore.mapInstance && mapStore.isMapLoaded) {
    const { longitude, latitude } = result.spatialObject.location;
    mapStore.setCenter(longitude, latitude);
    mapStore.setZoom(Math.max(mapStore.zoom, 14));
  }
}
function handleClear() {
  resultStore.clearResults();
}
</script>

<style scoped>
.result-list-card {
  flex-shrink: 0;
  max-height: 520px;
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background: white;
}
:deep(.el-card__header) {
  flex-shrink: 0;
  padding: 12px;
  border-bottom: 1px solid #ebeef5;
  background: white;
}
:deep(.el-card__body) {
  flex: 1 !important;
  min-height: 0 !important;
  display: flex !important;
  flex-direction: column !important;
  padding: 0 !important;
  overflow: hidden !important;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  padding: 12px;
}
.toolbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid #ebeef5;
  gap: 8px;
  flex-wrap: wrap;
  background: white;
}
.result-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px 12px;
}
.result-list::-webkit-scrollbar        { width: 5px; }
.result-list::-webkit-scrollbar-track  { background: transparent; }
.result-list::-webkit-scrollbar-thumb  { background: #c1c1c1; border-radius: 3px; }
.result-list::-webkit-scrollbar-thumb:hover { background: #909399; }
</style>
