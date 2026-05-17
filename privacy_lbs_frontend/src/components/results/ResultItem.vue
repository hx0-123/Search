<!--
  Result Item Component
  Directly renders plaintext POI information (Cloud C2 has completed Paillier decryption in backend, frontend requires no decryption)
-->
<template>
  <div
    class="result-item"
    :class="{ selected }"
    @click="$emit('click', result)"
  >
    <div class="item-header">
      <div class="item-rank">#{{ index + 1 }}</div>

      <!-- Plaintext name: direct rendering -->
      <div class="item-title">
        <span v-if="displayName" class="plain-name">{{ displayName }}</span>
        <span v-else class="missing-name">(Missing Name)</span>
      </div>

      <div class="item-score">{{ result.score.toFixed(2) }}</div>
    </div>

    <div class="item-body">
      <div class="item-description" v-if="result.spatialObject.description">
        {{ result.spatialObject.description }}
      </div>

      <div class="item-meta">
        <el-tag size="small" v-if="result.spatialObject.category">
          {{ result.spatialObject.category }}
        </el-tag>
        <el-text type="info" size="small">
          <el-icon><Location /></el-icon>
          {{ formatDistance(result.distance) }}
        </el-text>
      </div>

      <div class="item-scores" v-if="result.textScore !== undefined || result.distanceScore !== undefined">
        <el-text type="info" size="small">
          Text Score: {{ result.textScore?.toFixed(2) || 'N/A' }} |
          Distance Score: {{ result.distanceScore?.toFixed(2) || 'N/A' }}
        </el-text>
      </div>
    </div>

    <div class="item-actions">
      <el-button type="primary" link size="small" @click.stop="handleViewDetails">
        View Details
      </el-button>
      <el-button type="success" link size="small" @click.stop="handlePlanRoute">
        Plan Route
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Location } from '@element-plus/icons-vue';
import type { QueryResult } from '@/types';
import { formatDistance } from '@/utils/coordinate.util';

const props = defineProps<{
  result: QueryResult;
  index: number;
  selected: boolean;
}>();

defineEmits<{
  click: [result: QueryResult];
}>();

// Directly get plaintext name (C2 has decrypted in cloud, frontend receives plaintext)
const displayName = computed(() => {
  const n = (props.result.spatialObject.name ?? '').trim();
  // Filter out possible residual ObjectId format strings
  if (/^[0-9a-f-]{32,}$/i.test(n)) return '';
  return n;
});

function handleViewDetails() {
  // Handled by parent component
}

function handlePlanRoute() {
  // Handled by parent component
}
</script>

<style scoped>
.result-item {
  padding: 12px;
  margin-bottom: 8px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
  flex-shrink: 0;
}
.result-item:last-child  { margin-bottom: 0; }
.result-item:hover        { border-color: #409eff; box-shadow: 0 2px 8px rgba(64,158,255,0.1); }
.result-item.selected     { border-color: #409eff; background: #ecf5ff; }

.item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.item-rank {
  font-weight: bold;
  color: #409eff;
  min-width: 30px;
  flex-shrink: 0;
}
.item-title {
  flex: 1;
  font-size: 14px;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.plain-name   { color: #303133; font-weight: 700; }
.missing-name { color: #e6a23c; font-size: 12px; font-style: italic; font-weight: 500; }

.item-score {
  font-size: 13px;
  font-weight: 600;
  color: #67c23a;
  flex-shrink: 0;
}
.item-body    { margin-bottom: 8px; }
.item-description {
  font-size: 12px;
  color: #606266;
  margin-bottom: 6px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.item-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
  font-size: 12px;
  flex-wrap: wrap;
}
.item-scores { font-size: 11px; color: #909399; }
.item-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-top: 6px;
  border-top: 1px solid #ebeef5;
  flex-wrap: wrap;
}
</style>
