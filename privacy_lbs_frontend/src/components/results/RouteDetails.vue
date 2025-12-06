<!--
  路线详情抽屉组件
  显示路线规划的详细信息
-->
<template>
  <el-drawer
    v-model="visible"
    title="路线规划详情"
    :size="400"
    direction="rtl"
  >
    <div v-if="routePlan" class="route-details">
      <!-- 路线概览 -->
      <el-card class="route-overview">
        <template #header>
          <span>路线概览</span>
        </template>
        <div class="overview-item">
          <el-icon><Location /></el-icon>
          <span>总距离: {{ formatDistance(routePlan.totalDistance) }}</span>
        </div>
        <div class="overview-item">
          <el-icon><Clock /></el-icon>
          <span>预计时间: {{ formatTime(routePlan.totalTime) }}</span>
        </div>
        <div class="overview-item">
          <el-icon><Guide /></el-icon>
          <span>途经点: {{ routePlan.waypoints.length }} 个</span>
        </div>
      </el-card>
      
      <!-- 途经点列表 -->
      <el-card class="waypoints-list">
        <template #header>
          <span>途经点</span>
        </template>
        <el-timeline>
          <el-timeline-item
            v-for="(waypoint, index) in routePlan.waypoints"
            :key="waypoint.id"
            :timestamp="`第 ${index + 1} 站`"
            placement="top"
          >
            <div class="waypoint-item">
              <div class="waypoint-name">{{ waypoint.name }}</div>
              <div class="waypoint-description" v-if="waypoint.description">
                {{ waypoint.description }}
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </el-card>
      
      <!-- 路线步骤 -->
      <el-card class="route-steps" v-if="routePlan.steps && routePlan.steps.length > 0">
        <template #header>
          <span>详细步骤</span>
        </template>
        <el-collapse>
          <el-collapse-item
            v-for="(step, index) in routePlan.steps"
            :key="index"
            :title="step.instruction"
            :name="index"
          >
            <div class="step-details">
              <div class="step-info">
                <el-text type="info" size="small">
                  距离: {{ formatDistance(step.distance) }} | 
                  时间: {{ formatTime(step.duration) }}
                </el-text>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-card>
      
      <!-- 操作按钮 -->
      <div class="route-actions">
        <el-button type="primary" @click="handleShowOnMap" style="width: 100%">
          在地图上显示
        </el-button>
        <el-button @click="handleExport" style="width: 100%; margin-top: 8px">
          导出路线
        </el-button>
      </div>
    </div>
    
    <div v-else class="empty-route">
      <el-empty description="暂无路线规划" />
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { Location, Clock, Guide } from '@element-plus/icons-vue';
import { useResultStore } from '@/stores/result.store';
import { useMapStore } from '@/stores/map.store';
import type { RoutePlan } from '@/types';
import { formatDistance } from '@/utils/coordinate.util';

const resultStore = useResultStore();
const mapStore = useMapStore();

const visible = ref(false);
const routePlan = ref<RoutePlan | null>(null);

// 监听store中的路线规划
watch(
  () => resultStore.routePlan,
  (plan) => {
    routePlan.value = plan;
    if (plan) {
      visible.value = true;
    }
  }
);

function formatTime(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`;
  } else {
    return `${minutes}分钟`;
  }
}

function handleShowOnMap() {
  if (routePlan.value && routePlan.value.polyline.length > 0) {
    // 在地图上显示路线
    // 这里可以调用地图store的方法来显示路线
    const center = routePlan.value.polyline[Math.floor(routePlan.value.polyline.length / 2)];
    mapStore.setCenter(center[0], center[1]);
    mapStore.setZoom(13);
    
    // TODO: 在地图上绘制路线折线
    ElMessage.success('路线已显示在地图上');
  }
}

function handleExport() {
  if (!routePlan.value) return;
  
  // 导出路线为JSON
  const dataStr = JSON.stringify(routePlan.value, null, 2);
  const dataBlob = new Blob([dataStr], { type: 'application/json' });
  const url = URL.createObjectURL(dataBlob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `route_${Date.now()}.json`;
  link.click();
  URL.revokeObjectURL(url);
  
  ElMessage.success('路线已导出');
}
</script>

<style scoped>
.route-details {
  padding: 0;
}

.route-overview,
.waypoints-list,
.route-steps {
  margin-bottom: 16px;
}

.overview-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
}

.overview-item:last-child {
  margin-bottom: 0;
}

.waypoint-item {
  padding: 8px 0;
}

.waypoint-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}

.waypoint-description {
  font-size: 12px;
  color: #909399;
}

.step-details {
  padding: 8px 0;
}

.step-info {
  margin-top: 8px;
}

.route-actions {
  margin-top: 24px;
}

.empty-route {
  padding: 40px 0;
  text-align: center;
}
</style>

