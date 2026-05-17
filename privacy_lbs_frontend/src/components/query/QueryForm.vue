<!--
  Query Form Component
  Used to initiate query requests
-->
<template>
  <el-card class="query-form-card">
    <template #header>
      <div class="card-header">
        <span>Privacy-Preserving Query</span>
      </div>
    </template>
    
    <el-form :model="form" label-width="100px" @submit.prevent="handleSubmit">
      <el-form-item label="Query Keywords" required>
        <el-input
          v-model="form.text"
          placeholder="Enter query keywords"
          clearable
          @input="handleTextChange"
        />
      </el-form-item>
      
      <el-form-item label="Current Location">
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
            Get Current Location
          </el-button>
        </div>
      </el-form-item>
      
      <el-form-item label="Weight Adjustment">
        <WeightSlider 
          v-model="form.alpha" 
          @change="handleAlphaChange"
          :auto-query="autoQueryOnWeightChange"
        />
        <div style="margin-top: 8px;">
          <el-checkbox v-model="autoQueryOnWeightChange" size="small">
            Auto re-query on weight change
          </el-checkbox>
        </div>
      </el-form-item>
      
      <el-form-item label="Result Count">
        <el-input-number
          v-model="form.k"
          :min="1"
          :max="100"
          :step="1"
        />
      </el-form-item>
      
      <el-form-item label="Query Radius">
        <el-input-number
          v-model="form.radius"
          :min="100"
          :max="50000"
          :step="100"
          :precision="0"
          placeholder="Optional, unit: meters"
        />
        <el-text type="info" size="small" style="margin-left: 8px;">
          If not set, no limit
        </el-text>
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
const autoQueryOnWeightChange = ref(false);

const form = reactive({
  text: '',
  alpha: 0.5,
  k: 10,
  radius: undefined as number | undefined,
});

onMounted(() => {
  requestAnimationFrame(() => {
    form.text = queryStore.queryText;
    form.alpha = queryStore.alpha;
    form.k = queryStore.k;
    form.radius = queryStore.radius;
  });
});

function handleTextChange(value: string) {
  queryStore.setQueryText(value);
  form.text = value;
}

async function handleAlphaChange(value: number) {
  queryStore.setAlpha(value);
  form.alpha = value;
  
  if (autoQueryOnWeightChange.value && queryStore.queryId) {
    try {
      const results = await queryStore.submit();
      if (results) {
        resultStore.setResults(results);
        ElMessage.success('Weights updated, query results refreshed');
      }
    } catch (error: any) {
      console.error('Re-query failed after weight adjustment:', error);
      resortResultsByWeight(value);
    }
  } else if (resultStore.hasResults) {
    resortResultsByWeight(value);
  }
}

function resortResultsByWeight(newAlpha: number) {
  const results = resultStore.results;
  if (results.length === 0) return;
  
  const maxProcessCount = 100;
  const limitedResults = results.slice(0, maxProcessCount);
  
  requestAnimationFrame(() => {
    const sorted = [...limitedResults].sort((a, b) => {
      const scoreA = (newAlpha * (a.textScore || 0)) + ((1 - newAlpha) * (a.distanceScore || 0));
      const scoreB = (newAlpha * (b.textScore || 0)) + ((1 - newAlpha) * (b.distanceScore || 0));
      return scoreB - scoreA;
    });
    
    const remainingResults = results.slice(maxProcessCount);
    const finalResults = [...sorted, ...remainingResults];
    
    resultStore.setResults(finalResults);
    ElMessage.info('Results re-sorted by new weights');
  });
}

function handleKChange(value: number) {
  queryStore.setK(value);
  form.k = value;
}

let isSubmitting = false;

async function handleSubmit() {
  if (isSubmitting) {
    return;
  }
  
  if (!queryStore.isQueryValid) {
    ElMessage.warning('Please complete the query form');
    return;
  }
  
  try {
    isSubmitting = true;
    queryStore.setRadius(form.radius);
    const results = await queryStore.submit();
    
    if (results) {
      requestAnimationFrame(() => {
        resultStore.setResults(results);
        ElMessage.success('Query successful');
      });
    }
  } catch (error: any) {
    ElMessage.error(error.message || 'Query failed');
  } finally {
    setTimeout(() => {
      isSubmitting = false;
    }, 100);
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
      message: 'Browser does not support Geolocation API',
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
    showSuccess('Current location obtained');
  } catch (error: any) {
    if (error instanceof GeolocationPositionError) {
      const errorInfo = handleLocationError(error);
      showError(errorInfo);
    } else {
      showError({
        type: 'location' as any,
        message: 'Failed to get location: ' + (error.message || 'Unknown error'),
      });
    }
  } finally {
    gettingLocation.value = false;
  }
}
</script>

<style scoped>
.query-form-card {
  flex-shrink: 0;
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
