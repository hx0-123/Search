/**
 * 查询状态管理
 * 管理查询参数、查询状态等
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Query, RealTimeLocation } from '@/types';
import { QueryStatus } from '@/types';
import { generateId } from '@/utils/crypto.util';
import { submitQuery, updateQuery, cancelQuery } from '@/services/query.service';

export const useQueryStore = defineStore('query', () => {
  // 当前查询
  const currentQuery = ref<Query | null>(null);
  
  // 查询状态
  const queryStatus = ref<QueryStatus>(QueryStatus.IDLE);
  
  // 查询ID
  const queryId = ref<string | null>(null);
  
  // 查询文本（关键词）
  const queryText = ref<string>('');
  const keywords = ref<string>(''); // 别名，与queryText同步
  
  // 当前位置
  const currentLocation = ref<{ longitude: number; latitude: number }>({
    longitude: 116.4074,
    latitude: 39.9042,
  });
  
  // 文本-距离权重 (alpha)
  const alpha = ref<number>(0.5);
  
  // Top-K数量
  const k = ref<number>(10);
  
  // 查询半径（可选）
  const radius = ref<number | undefined>(undefined);
  
  // 安全区域边界（从后端返回）
  const safeZone = ref<{
    center: { longitude: number; latitude: number };
    radius?: number;
    polygon?: [number, number][];
  } | null>(null);
  
  // 是否启用实时更新
  const realTimeUpdateEnabled = ref<boolean>(false);
  
  // 实时位置更新间隔（毫秒）
  const updateInterval = ref<number>(5000);
  
  // 错误信息
  const error = ref<string | null>(null);
  
  // 计算属性：查询是否有效
  const isQueryValid = computed(() => {
    return (
      queryText.value.trim().length > 0 &&
      currentLocation.value.longitude !== undefined &&
      currentLocation.value.latitude !== undefined &&
      alpha.value >= 0 &&
      alpha.value <= 1 &&
      k.value >= 1 &&
      k.value <= 100
    );
  });
  
  // 计算属性：是否正在查询
  const isQuerying = computed(() => {
    return queryStatus.value === QueryStatus.PENDING || 
           queryStatus.value === QueryStatus.PROCESSING;
  });
  
  /**
   * 设置查询文本
   */
  function setQueryText(text: string) {
    queryText.value = text;
    keywords.value = text; // 同步更新keywords
  }
  
  /**
   * 设置关键词（别名）
   */
  function setKeywords(text: string) {
    setQueryText(text);
  }
  
  /**
   * 设置安全区域
   */
  function setSafeZone(zone: {
    center: { longitude: number; latitude: number };
    radius?: number;
    polygon?: [number, number][];
  } | null) {
    safeZone.value = zone;
  }
  
  /**
   * 设置当前位置
   */
  function setCurrentLocation(location: { longitude: number; latitude: number }) {
    currentLocation.value = location;
  }
  
  /**
   * 设置权重
   */
  function setAlpha(value: number) {
    if (value >= 0 && value <= 1) {
      alpha.value = value;
    }
  }
  
  /**
   * 设置Top-K数量
   */
  function setK(value: number) {
    if (value >= 1 && value <= 100) {
      k.value = value;
    }
  }
  
  /**
   * 设置查询半径
   */
  function setRadius(value: number | undefined) {
    radius.value = value;
  }
  
  /**
   * 设置实时更新
   */
  function setRealTimeUpdate(enabled: boolean) {
    realTimeUpdateEnabled.value = enabled;
  }
  
  /**
   * 提交查询
   */
  async function submit() {
    if (!isQueryValid.value) {
      error.value = '查询参数无效';
      return;
    }
    
    try {
      queryStatus.value = QueryStatus.PENDING;
      error.value = null;
      
      const query: Query = {
        id: generateId('query'),
        text: queryText.value,
        location: currentLocation.value,
        alpha: alpha.value,
        k: k.value,
        radius: radius.value,
        timestamp: Date.now(),
      };
      
      currentQuery.value = query;
      queryId.value = query.id;
      
      // 调用API
      const response = await submitQuery(query);
      
      // 检查响应中是否包含安全区域信息
      if (response && (response as any).safeZone) {
        setSafeZone((response as any).safeZone);
      }
      
      queryStatus.value = QueryStatus.SUCCESS;
      
      // 返回结果供result store使用
      return Array.isArray(response) ? response : (response as any).results || [];
    } catch (err: any) {
      queryStatus.value = QueryStatus.ERROR;
      error.value = err.message || '查询失败';
      throw err;
    }
  }
  
  /**
   * 更新查询（实时位置更新）
   */
  async function update(location: RealTimeLocation) {
    if (!queryId.value) {
      return;
    }
    
    try {
      queryStatus.value = QueryStatus.PROCESSING;
      error.value = null;
      
      // 更新当前位置
      currentLocation.value = {
        longitude: location.longitude,
        latitude: location.latitude,
      };
      
      // 调用API
      const response = await updateQuery(queryId.value, location);
      
      // 检查响应中是否包含安全区域信息
      if (response && (response as any).safeZone) {
        setSafeZone((response as any).safeZone);
      }
      
      queryStatus.value = QueryStatus.SUCCESS;
      
      return Array.isArray(response) ? response : (response as any).results || [];
    } catch (err: any) {
      queryStatus.value = QueryStatus.ERROR;
      error.value = err.message || '更新查询失败';
      throw err;
    }
  }
  
  /**
   * 取消查询
   */
  async function cancel() {
    if (queryId.value) {
      try {
        await cancelQuery(queryId.value);
      } catch (err) {
        console.error('取消查询失败:', err);
      }
    }
    
    queryStatus.value = QueryStatus.IDLE;
    queryId.value = null;
    currentQuery.value = null;
    error.value = null;
  }
  
  /**
   * 重置查询状态
   */
  function reset() {
    queryStatus.value = QueryStatus.IDLE;
    queryId.value = null;
    currentQuery.value = null;
    queryText.value = '';
    alpha.value = 0.5;
    k.value = 10;
    radius.value = undefined;
    realTimeUpdateEnabled.value = false;
    error.value = null;
  }
  
  return {
    // 状态
    currentQuery,
    queryStatus,
    queryId,
    queryText,
    keywords, // 导出keywords别名
    currentLocation,
    alpha,
    k,
    radius,
    safeZone, // 导出安全区域
    realTimeUpdateEnabled,
    updateInterval,
    error,
    // 计算属性
    isQueryValid,
    isQuerying,
    // 方法
    setQueryText,
    setKeywords, // 导出setKeywords方法
    setCurrentLocation,
    setAlpha,
    setK,
    setRadius,
    setSafeZone, // 导出setSafeZone方法
    setRealTimeUpdate,
    submit,
    update,
    cancel,
    reset,
  };
});

