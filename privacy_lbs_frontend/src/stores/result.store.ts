/**
 * 查询结果状态管理
 * 管理查询结果、排序、筛选等
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { QueryResult, RoutePlan, SpatialObject } from '@/types';

export type SortField = 'score' | 'distance' | 'name';
export type SortOrder = 'asc' | 'desc';

export const useResultStore = defineStore('result', () => {
  // 查询结果列表
  const results = ref<QueryResult[]>([]);
  
  // Top-K结果（别名，与results同步）
  const topKResults = computed(() => results.value);
  
  // 当前选中的结果
  const selectedResult = ref<QueryResult | null>(null);
  
  // 选中的路线（别名，与routePlan同步）
  const selectedRoute = computed(() => routePlan.value);
  
  // 路线规划结果
  const routePlan = ref<RoutePlan | null>(null);
  
  // 排序字段
  const sortField = ref<SortField>('score');
  
  // 排序顺序
  const sortOrder = ref<SortOrder>('desc');
  
  // 筛选关键词
  const filterKeyword = ref<string>('');
  
  // 计算属性：排序后的结果
  const sortedResults = computed(() => {
    let filtered = [...results.value];
    
    // 应用筛选
    if (filterKeyword.value.trim()) {
      const keyword = filterKeyword.value.toLowerCase();
      filtered = filtered.filter(result =>
        result.spatialObject.name.toLowerCase().includes(keyword) ||
        result.spatialObject.description?.toLowerCase().includes(keyword) ||
        result.spatialObject.category?.toLowerCase().includes(keyword)
      );
    }
    
    // 应用排序
    filtered.sort((a, b) => {
      let comparison = 0;
      
      switch (sortField.value) {
        case 'score':
          comparison = a.score - b.score;
          break;
        case 'distance':
          comparison = a.distance - b.distance;
          break;
        case 'name':
          comparison = a.spatialObject.name.localeCompare(b.spatialObject.name);
          break;
      }
      
      return sortOrder.value === 'asc' ? comparison : -comparison;
    });
    
    return filtered;
  });
  
  // 计算属性：结果数量
  const resultCount = computed(() => {
    return results.value.length;
  });
  
  // 计算属性：是否有结果
  const hasResults = computed(() => {
    return results.value.length > 0;
  });
  
  /**
   * 设置查询结果
   */
  function setResults(newResults: QueryResult[]) {
    results.value = newResults;
    // 默认选中第一个结果
    if (newResults.length > 0 && !selectedResult.value) {
      selectedResult.value = newResults[0];
    }
  }
  
  /**
   * 添加结果（用于增量更新）
   */
  function addResults(newResults: QueryResult[]) {
    // 合并结果，去重
    const existingIds = new Set(results.value.map(r => r.id));
    const uniqueNewResults = newResults.filter(r => !existingIds.has(r.id));
    results.value = [...results.value, ...uniqueNewResults];
  }
  
  /**
   * 更新结果（用于实时更新）
   */
  function updateResults(newResults: QueryResult[]) {
    // 更新现有结果，添加新结果
    const resultMap = new Map(results.value.map(r => [r.id, r]));
    
    for (const newResult of newResults) {
      resultMap.set(newResult.id, newResult);
    }
    
    results.value = Array.from(resultMap.values());
  }
  
  /**
   * 设置选中的结果
   */
  function setSelectedResult(result: QueryResult | null) {
    selectedResult.value = result;
  }
  
  /**
   * 设置路线规划
   */
  function setRoutePlan(plan: RoutePlan | null) {
    routePlan.value = plan;
  }
  
  /**
   * 设置排序
   */
  function setSort(field: SortField, order: SortOrder = 'desc') {
    sortField.value = field;
    sortOrder.value = order;
  }
  
  /**
   * 切换排序顺序
   */
  function toggleSortOrder() {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  }
  
  /**
   * 设置筛选关键词
   */
  function setFilterKeyword(keyword: string) {
    filterKeyword.value = keyword;
  }
  
  /**
   * 清空筛选
   */
  function clearFilter() {
    filterKeyword.value = '';
  }
  
  /**
   * 根据ID获取结果
   */
  function getResultById(id: string): QueryResult | undefined {
    return results.value.find(r => r.id === id);
  }
  
  /**
   * 清空结果
   */
  function clearResults() {
    results.value = [];
    selectedResult.value = null;
    routePlan.value = null;
  }
  
  /**
   * 重置状态
   */
  function reset() {
    clearResults();
    sortField.value = 'score';
    sortOrder.value = 'desc';
    filterKeyword.value = '';
  }
  
  return {
    // 状态
    results,
    topKResults, // 导出topKResults别名
    selectedResult,
    selectedRoute, // 导出selectedRoute别名
    routePlan,
    sortField,
    sortOrder,
    filterKeyword,
    // 计算属性
    sortedResults,
    resultCount,
    hasResults,
    // 方法
    setResults,
    addResults,
    updateResults,
    setSelectedResult,
    setRoutePlan,
    setSort,
    toggleSortOrder,
    setFilterKeyword,
    clearFilter,
    getResultById,
    clearResults,
    reset,
  };
});

