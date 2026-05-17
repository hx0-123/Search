<!--
  Route Details Drawer Component
  Displays detailed route planning information
-->
<template>
  <el-drawer
    v-model="visible"
    title="Route Planning Details"
    :size="400"
    direction="rtl"
  >
    <div v-if="routePlan" class="route-details">
      <!-- Route Overview -->
      <el-card class="route-overview">
        <template #header>
          <span>Route Overview</span>
        </template>
        <div class="overview-item">
          <el-icon><Location /></el-icon>
          <span>Total Distance: {{ formatDistance(routePlan.totalDistance) }}</span>
        </div>
        <div class="overview-item">
          <el-icon><Clock /></el-icon>
          <span>Estimated Time: {{ formatTime(routePlan.totalTime) }}</span>
        </div>
        <div class="overview-item">
          <el-icon><Guide /></el-icon>
          <span>Waypoints: {{ routePlan.waypoints.length }}</span>
        </div>
      </el-card>
      
      <!-- Waypoints List -->
      <el-card class="waypoints-list">
        <template #header>
          <span>Waypoints</span>
        </template>
        <el-timeline>
          <el-timeline-item
            v-for="(waypoint, index) in routePlan.waypoints"
            :key="waypoint.id"
            :timestamp="`Stop ${index + 1}`"
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
      
      <!-- Detailed Steps -->
      <el-card class="route-steps" v-if="routePlan.steps && routePlan.steps.length > 0">
        <template #header>
          <span>Detailed Steps</span>
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
                  Distance: {{ formatDistance(step.distance) }} | 
                  Time: {{ formatTime(step.duration) }}
                </el-text>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </el-card>
      
      <!-- Action Buttons -->
      <div class="route-actions">
        <el-button type="primary" @click="handleShowOnMap" style="width: 100%">
          Show on Map
        </el-button>
        <el-button @click="handleExport" style="width: 100%; margin-top: 8px">
          Export Route
        </el-button>
      </div>
    </div>
    
    <div v-else class="empty-route">
      <el-empty description="No route plan available" />
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { Location, Clock, Guide } from '@element-plus/icons-vue';
import { useResultStore } from '@/stores/result.store';
import { useMapStore } from '@/stores/map.store';
import type { RoutePlan } from '@/types';
import { formatDistance } from '@/utils/coordinate.util';

const resultStore = useResultStore();
const mapStore = useMapStore();

const visible = ref(false);

// Use computed instead of watch to avoid blocking
const routePlan = computed(() => resultStore.routePlan);

// Listen for routePlan changes asynchronously
let checkTimer: number | null = null;

function checkRoutePlan() {
  if (checkTimer) {
    clearTimeout(checkTimer);
  }
  
  checkTimer = window.setTimeout(() => {
    if (routePlan.value) {
      visible.value = true;
    }
    checkTimer = null;
  }, 100);
}

onMounted(() => {
  console.log('[RouteDetails] Component mounted');
  
  // Periodically check routePlan (lightweight polling to avoid watch blocking)
  const pollInterval = setInterval(() => {
    if (routePlan.value && !visible.value) {
      checkRoutePlan();
    }
  }, 500);
  
  // Save interval ID for cleanup
  (onUnmounted as any).pollInterval = pollInterval;
});

onUnmounted(() => {
  console.log('[RouteDetails] Component unmounting');
  
  if (checkTimer) {
    clearTimeout(checkTimer);
    checkTimer = null;
  }
  
  // Cleanup polling
  const pollInterval = (onUnmounted as any).pollInterval;
  if (pollInterval) {
    clearInterval(pollInterval);
  }
});

function formatTime(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (hours > 0) {
    return `${hours} hours ${minutes} minutes`;
  } else {
    return `${minutes} minutes`;
  }
}

function handleShowOnMap() {
  if (!routePlan.value || !routePlan.value.polyline || routePlan.value.polyline.length === 0) {
    ElMessage.warning('No route data available');
    return;
  }
  
  // Execute map operations asynchronously to avoid blocking
  setTimeout(() => {
    try {
      const center = routePlan.value!.polyline[Math.floor(routePlan.value!.polyline.length / 2)];
    mapStore.setCenter(center[0], center[1]);
      
      setTimeout(() => {
    mapStore.setZoom(13);
    ElMessage.success('Route displayed on map');
      }, 100);
    } catch (error) {
      console.error('[RouteDetails] Failed to show route:', error);
      ElMessage.error('Failed to display route on map');
  }
  }, 100);
}

function handleExport() {
  if (!routePlan.value) {
    ElMessage.warning('No route data available for export');
    return;
  }
  
  try {
  // Export route as JSON
  const dataStr = JSON.stringify(routePlan.value, null, 2);
  const dataBlob = new Blob([dataStr], { type: 'application/json' });
  const url = URL.createObjectURL(dataBlob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `route_${Date.now()}.json`;
  link.click();
  URL.revokeObjectURL(url);
  
  ElMessage.success('Route exported successfully');
  } catch (error) {
    console.error('[RouteDetails] Failed to export route:', error);
      ElMessage.error('Failed to export route');
  }
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

