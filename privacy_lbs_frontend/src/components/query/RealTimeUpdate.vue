<!--
  实时更新组件
  处理实时位置更新
-->
<template>
  <el-card class="realtime-update-card">
    <template #header>
      <div class="card-header">
        <span>实时位置更新</span>
        <el-switch
          v-model="enabled"
          @change="handleToggle"
          :disabled="!queryStore.queryId"
        />
      </div>
    </template>
    
    <div v-if="!queryStore.queryId" class="no-query-hint">
      <el-text type="info">请先发起查询</el-text>
    </div>
    
    <div v-else>
      <el-form label-width="100px">
        <el-form-item label="更新间隔">
          <el-input-number
            v-model="interval"
            :min="1000"
            :max="60000"
            :step="1000"
            :precision="0"
            @change="handleIntervalChange"
          />
          <el-text type="info" size="small" style="margin-left: 8px;">
            毫秒
          </el-text>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-tag :type="enabled ? 'success' : 'info'">
            {{ enabled ? '已启用' : '已禁用' }}
          </el-tag>
        </el-form-item>
        
        <el-form-item label="更新次数">
          <el-text>{{ updateCount }}</el-text>
        </el-form-item>
        
        <el-form-item label="最后更新">
          <el-text type="info" size="small">
            {{ lastUpdateTime || '暂无' }}
          </el-text>
        </el-form-item>
      </el-form>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { useQueryStore } from '@/stores/query.store';
import { useResultStore } from '@/stores/result.store';
import { useMapStore } from '@/stores/map.store';
import { debounce } from '@/utils/debounce.util';
import dayjs from 'dayjs';

const queryStore = useQueryStore();
const resultStore = useResultStore();
const mapStore = useMapStore();

const enabled = ref(false);
const interval = ref(5000);
const updateCount = ref(0);
const lastUpdateTime = ref<string>(''); // 用于显示的格式化时间字符串

let updateTimer: number | null = null;
let lastUpdateTimestamp: number = 0; // 用于防抖检查的时间戳
const DEBOUNCE_DELAY = 1000; // 防抖延迟1秒

// 创建防抖的更新函数
const debouncedUpdate = debounce(async () => {
  await performUpdate();
}, DEBOUNCE_DELAY);

watch(
  () => queryStore.queryId,
  (newId) => {
    if (!newId) {
      stopUpdate();
    }
  }
);

function handleToggle(value: boolean) {
  if (value) {
    startUpdate();
  } else {
    stopUpdate();
  }
  queryStore.setRealTimeUpdate(value);
}

function handleIntervalChange(value: number) {
  queryStore.updateInterval = value;
  if (enabled.value) {
    stopUpdate();
    startUpdate();
  }
}

async function performUpdate() {
  if (!queryStore.queryId) {
    stopUpdate();
    return;
  }
  
  // 检查距离上次更新的时间，避免过于频繁的请求
  const now = Date.now();
  if (now - lastUpdateTimestamp < DEBOUNCE_DELAY) {
    return;
  }
  lastUpdateTimestamp = now;
  
  try {
    // 获取当前位置
    const location = queryStore.currentLocation;
    
    // 调用更新API（使用防抖）
    const results = await queryStore.update({
      longitude: location.longitude,
      latitude: location.latitude,
      timestamp: now,
    });
    
    // 更新结果
    if (results) {
      resultStore.updateResults(results);
    }
    
    // 更新统计
    updateCount.value++;
    lastUpdateTime.value = dayjs().format('HH:mm:ss');
    
    // 添加轨迹点
    mapStore.addTrajectoryPoint({
      longitude: location.longitude,
      latitude: location.latitude,
      timestamp: now,
    });
  } catch (error: any) {
    console.error('实时更新失败:', error);
    ElMessage.error('更新失败: ' + (error.message || '未知错误'));
    // 不停止更新，允许重试
  }
}

function startUpdate() {
  if (updateTimer) {
    clearInterval(updateTimer);
  }
  
  enabled.value = true;
  performUpdate(); // 立即执行一次
  
  updateTimer = window.setInterval(() => {
    // 使用防抖函数
    debouncedUpdate();
  }, interval.value);
}

function stopUpdate() {
  if (updateTimer) {
    clearInterval(updateTimer);
    updateTimer = null;
  }
  enabled.value = false;
}

onMounted(() => {
  // 初始化
  enabled.value = queryStore.realTimeUpdateEnabled;
  interval.value = queryStore.updateInterval;
  
  if (enabled.value && queryStore.queryId) {
    startUpdate();
  }
});

onUnmounted(() => {
  stopUpdate();
});
</script>

<style scoped>
.realtime-update-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.no-query-hint {
  text-align: center;
  padding: 20px;
}
</style>

