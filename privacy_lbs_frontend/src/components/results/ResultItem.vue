<!--
  结果项组件
  显示单个查询结果
-->
<template>
  <div
    class="result-item"
    :class="{ selected: selected }"
    @click="$emit('click', result)"
  >
    <div class="item-header">
      <div class="item-rank">#{{ index + 1 }}</div>
      <div class="item-title">{{ result.spatialObject.name }}</div>
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
          文本: {{ result.textScore?.toFixed(2) || 'N/A' }} | 
          距离: {{ result.distanceScore?.toFixed(2) || 'N/A' }}
        </el-text>
      </div>
    </div>
    
    <div class="item-actions">
      <el-button
        type="primary"
        link
        size="small"
        @click.stop="handleViewDetails"
      >
        查看详情
      </el-button>
      <el-button
        type="success"
        link
        size="small"
        @click.stop="handlePlanRoute"
      >
        路线规划
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Location } from '@element-plus/icons-vue';
import type { QueryResult } from '@/types';
import { formatDistance } from '@/utils/coordinate.util';

defineProps<{
  result: QueryResult;
  index: number;
  selected: boolean;
}>();

defineEmits<{
  click: [result: QueryResult];
}>();

function handleViewDetails() {
  // 触发查看详情事件，由父组件处理
  // 可以通过事件总线或store来处理
}

function handlePlanRoute() {
  // 触发路线规划事件，由父组件处理
}
</script>

<style scoped>
.result-item {
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  background: white;
}

.result-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.result-item.selected {
  border-color: #409eff;
  background: #ecf5ff;
}

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
}

.item-title {
  flex: 1;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.item-score {
  font-size: 14px;
  font-weight: 600;
  color: #67c23a;
}

.item-body {
  margin-bottom: 8px;
}

.item-description {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.item-scores {
  font-size: 12px;
}

.item-actions {
  display: flex;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid #ebeef5;
}
</style>

