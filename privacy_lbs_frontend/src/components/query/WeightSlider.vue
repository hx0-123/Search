<!--
  权重滑块组件
  用于调整文本-距离权重 (alpha)
-->
<template>
  <div class="weight-slider">
    <el-slider
      v-model="localValue"
      :min="0"
      :max="1"
      :step="0.01"
      :format-tooltip="formatTooltip"
      @change="handleChange"
    />
    <div class="slider-labels">
      <span class="label-left">距离优先</span>
      <span class="label-right">文本优先</span>
    </div>
    <div class="current-value">
      当前权重: <strong>{{ formatValue(localValue) }}</strong>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

const props = defineProps<{
  modelValue: number;
  autoQuery?: boolean; // 是否在调整时自动触发查询
}>();

const emit = defineEmits<{
  'update:modelValue': [value: number];
  'change': [value: number];
}>();

const localValue = ref(props.modelValue);

watch(
  () => props.modelValue,
  (newValue) => {
    localValue.value = newValue;
  }
);

function handleChange(value: number) {
  emit('update:modelValue', value);
  emit('change', value);
}

function formatTooltip(value: number): string {
  if (value < 0.3) {
    return '距离优先';
  } else if (value > 0.7) {
    return '文本优先';
  } else {
    return '平衡';
  }
}

function formatValue(value: number): string {
  return (value * 100).toFixed(0) + '%';
}
</script>

<style scoped>
.weight-slider {
  width: 100%;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #666;
}

.label-left {
  color: #3b82f6;
}

.label-right {
  color: #10b981;
}

.current-value {
  margin-top: 8px;
  text-align: center;
  font-size: 14px;
  color: #333;
}

.current-value strong {
  color: #409eff;
}
</style>

