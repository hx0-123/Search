<!--
  结果列表组件
  显示查询结果列表和处理排序
-->
<template>
  <el-card class="result-list-card">
    <template #header>
      <div class="card-header">
        <span>查询结果 ({{ resultStore.resultCount }})</span>
        <el-button
          type="primary"
          link
          size="small"
          @click="handleClear"
          v-if="resultStore.hasResults"
        >
          清空
        </el-button>
      </div>
    </template>
    
    <div v-if="!resultStore.hasResults" class="empty-state">
      <el-empty description="暂无查询结果" />
    </div>
    
    <div v-else>
      <!-- 排序和筛选 -->
      <div class="toolbar">
        <el-select
          v-model="sortField"
          placeholder="排序方式"
          size="small"
          style="width: 120px"
          @change="handleSortChange"
        >
          <el-option label="按评分" value="score" />
          <el-option label="按距离" value="distance" />
          <el-option label="按名称" value="name" />
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
          placeholder="筛选结果..."
          size="small"
          clearable
          style="width: 150px; margin-left: 8px"
          @input="handleFilterChange"
        />
      </div>
      
      <!-- 结果列表 -->
      <div class="result-list">
        <ResultItem
          v-for="(result, index) in resultStore.sortedResults"
          :key="result.id"
          :result="result"
          :index="index"
          :selected="result.id === resultStore.selectedResult?.id"
          @click="handleSelectResult(result)"
        />
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { ArrowUp, ArrowDown } from '@element-plus/icons-vue';
import { useResultStore } from '@/stores/result.store';
import { useMapStore } from '@/stores/map.store';
import ResultItem from './ResultItem.vue';
import type { QueryResult } from '@/types';

const resultStore = useResultStore();
const mapStore = useMapStore();

const sortField = ref<'score' | 'distance' | 'name'>('score');
const sortOrder = ref<'asc' | 'desc'>('desc');
const filterKeyword = ref('');

// 初始化
watch(
  () => resultStore.sortField,
  (value) => {
    sortField.value = value;
  },
  { immediate: true }
);

watch(
  () => resultStore.sortOrder,
  (value) => {
    sortOrder.value = value;
  },
  { immediate: true }
);

watch(
  () => resultStore.filterKeyword,
  (value) => {
    filterKeyword.value = value;
  },
  { immediate: true }
);

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
  
  // 移动地图到选中结果的位置
  const mapStore = useMapStore();
  if (mapStore.mapInstance && mapStore.isMapLoaded) {
    const location = result.spatialObject.location;
    mapStore.setCenter(location.longitude, location.latitude);
    mapStore.setZoom(Math.max(mapStore.zoom, 14));
  }
}

function handleClear() {
  resultStore.clearResults();
}
</script>

<style scoped>
.result-list-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-state {
  padding: 40px 0;
}

.toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.result-list {
  max-height: 600px;
  overflow-y: auto;
}

.result-list::-webkit-scrollbar {
  width: 6px;
}

.result-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.result-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.result-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>

