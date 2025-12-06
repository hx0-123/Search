<!--
  查询表单组件
  用于发起查询请求
-->
<template>
  <el-card class="query-form-card">
    <template #header>
      <div class="card-header">
        <span>隐私保护查询</span>
      </div>
    </template>
    
    <el-form :model="form" label-width="100px" @submit.prevent="handleSubmit">
      <el-form-item label="查询文本" required>
        <el-input
          v-model="form.text"
          placeholder="请输入查询关键词"
          clearable
          @input="handleTextChange"
        />
      </el-form-item>
      
      <el-form-item label="当前位置">
        <div class="location-display">
          <el-text type="info">
            {{ formatLocation(queryStore.currentLocation) }}
          </el-text>
          <el-button
            type="primary"
            link
            size="small"
            @click="getCurrentLocation"
            :loading="gettingLocation"
          >
            获取当前位置
          </el-button>
        </div>
      </el-form-item>
      
      <el-form-item label="权重调整">
        <WeightSlider 
          v-model="form.alpha" 
          @change="handleAlphaChange"
          :auto-query="autoQueryOnWeightChange"
        />
        <div style="margin-top: 8px;">
          <el-checkbox v-model="autoQueryOnWeightChange" size="small">
            权重调整时自动重新查询
          </el-checkbox>
        </div>
      </el-form-item>
      
      <el-form-item label="结果数量">
        <el-input-number
          v-model="form.k"
          :min="1"
          :max="100"
          :step="1"
          @change="handleKChange"
        />
      </el-form-item>
      
      <el-form-item label="查询半径">
        <el-input-number
          v-model="form.radius"
          :min="100"
          :max="50000"
          :step="100"
          :precision="0"
          placeholder="可选，单位：米"
        />
        <el-text type="info" size="small" style="margin-left: 8px;">
          不设置则无限制
        </el-text>
      </el-form-item>
      
      <el-form-item>
        <el-button
          type="primary"
          @click="handleSubmit"
          :loading="queryStore.isQuerying"
          :disabled="!queryStore.isQueryValid"
          style="width: 100%"
        >
          {{ queryStore.isQuerying ? '查询中...' : '发起查询' }}
        </el-button>
      </el-form-item>
      
      <el-form-item v-if="queryStore.error">
        <el-alert
          :title="queryStore.error"
          type="error"
          :closable="false"
          show-icon
        />
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { useQueryStore } from '@/stores/query.store';
import { useResultStore } from '@/stores/result.store';
import { handleLocationError, showError, showSuccess } from '@/utils/error-handler.util';
import WeightSlider from './WeightSlider.vue';
import { formatDistance } from '@/utils/coordinate.util';

const queryStore = useQueryStore();
const resultStore = useResultStore();

const gettingLocation = ref(false);
const autoQueryOnWeightChange = ref(false); // 权重调整时是否自动查询

const form = reactive({
  text: '',
  alpha: 0.5,
  k: 10,
  radius: undefined as number | undefined,
});

// 初始化表单
onMounted(() => {
  form.text = queryStore.queryText;
  form.alpha = queryStore.alpha;
  form.k = queryStore.k;
  form.radius = queryStore.radius;
});

function handleTextChange(value: string) {
  queryStore.setQueryText(value);
  form.text = value;
}

async function handleAlphaChange(value: number) {
  queryStore.setAlpha(value);
  form.alpha = value;
  
  // 如果启用了自动查询且有查询ID，则重新查询
  if (autoQueryOnWeightChange.value && queryStore.queryId) {
    try {
      const results = await queryStore.submit();
      if (results) {
        resultStore.setResults(results);
        ElMessage.success('权重已更新，查询结果已刷新');
      }
    } catch (error: any) {
      console.error('权重调整后重新查询失败:', error);
      // 如果查询失败，则进行前端重新排序
      resortResultsByWeight(value);
    }
  } else if (resultStore.hasResults) {
    // 如果没有自动查询，但有结果，则进行前端重新排序
    resortResultsByWeight(value);
  }
}

/**
 * 根据新权重在前端重新排序结果
 */
function resortResultsByWeight(newAlpha: number) {
  const results = resultStore.results;
  if (results.length === 0) return;
  
  // 重新计算综合评分并排序
  const sorted = [...results].sort((a, b) => {
    // 综合评分 = alpha * textScore + (1 - alpha) * distanceScore
    const scoreA = (newAlpha * (a.textScore || 0)) + ((1 - newAlpha) * (a.distanceScore || 0));
    const scoreB = (newAlpha * (b.textScore || 0)) + ((1 - newAlpha) * (b.distanceScore || 0));
    return scoreB - scoreA; // 降序
  });
  
  // 更新结果
  resultStore.setResults(sorted);
  ElMessage.info('结果已按新权重重新排序');
}

function handleKChange(value: number) {
  queryStore.setK(value);
  form.k = value;
}

async function handleSubmit() {
  if (!queryStore.isQueryValid) {
    ElMessage.warning('请填写完整的查询信息');
    return;
  }
  
  try {
    // 更新查询参数
    queryStore.setRadius(form.radius);
    
    // 提交查询
    const results = await queryStore.submit();
    
    // 更新结果
    if (results) {
      resultStore.setResults(results);
      ElMessage.success('查询成功');
    }
  } catch (error: any) {
    ElMessage.error(error.message || '查询失败');
  }
}

function formatLocation(location: { longitude: number; latitude: number }): string {
  return `${location.latitude.toFixed(6)}, ${location.longitude.toFixed(6)}`;
}

async function getCurrentLocation() {
  gettingLocation.value = true;
  
  if (!navigator.geolocation) {
    showError({
      type: 'location' as any,
      message: '浏览器不支持地理位置API',
    });
    gettingLocation.value = false;
    return;
  }
  
  try {
    const position = await new Promise<GeolocationPosition>((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      });
    });
    
    const location = {
      longitude: position.coords.longitude,
      latitude: position.coords.latitude,
    };
    
    queryStore.setCurrentLocation(location);
    showSuccess('已获取当前位置');
  } catch (error: any) {
    if (error instanceof GeolocationPositionError) {
      const errorInfo = handleLocationError(error);
      showError(errorInfo);
    } else {
      showError({
        type: 'location' as any,
        message: '获取位置失败: ' + (error.message || '未知错误'),
      });
    }
  } finally {
    gettingLocation.value = false;
  }
}
</script>

<style scoped>
.query-form-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.location-display {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>

