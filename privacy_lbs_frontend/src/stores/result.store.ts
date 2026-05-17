/**
 * Query Result State Management
 * Manages query results, sorting, filtering, etc.
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { QueryResult, RoutePlan, SpatialObject } from '@/types';

export type SortField = 'score' | 'distance' | 'name';
export type SortOrder = 'asc' | 'desc';

export const useResultStore = defineStore('result', () => {
  // Query results list
  const results = ref<QueryResult[]>([]);
  
  // Top-K results (alias, synchronized with results)
  const topKResults = computed(() => results.value);
  
  // Currently selected result
  const selectedResult = ref<QueryResult | null>(null);
  
  // Selected route (alias, synchronized with routePlan)
  const selectedRoute = computed(() => routePlan.value);
  
  // Route planning result
  const routePlan = ref<RoutePlan | null>(null);
  
  // Sort field
  const sortField = ref<SortField>('score');
  
  // Sort order
  const sortOrder = ref<SortOrder>('desc');
  
  // Filter keyword
  const filterKeyword = ref<string>('');
  
  // Computed property: Sorted results
  // FIX: Removed manual cache variables — they break Vue's reactivity tracking.
  // Vue's computed() already memoises by dependency; a manual cache on top
  // causes the watcher in ResultMarkerLayer to miss updates when the array
  // contents change but the cached length happens to match.
  const sortedResults = computed(() => {
    const sourceResults = results.value;
    if (!sourceResults || sourceResults.length === 0) return [];

    const currentSortField = sortField.value;
    const currentSortOrder = sortOrder.value;
    const currentFilterKeyword = filterKeyword.value?.trim() || '';

    let filtered = sourceResults.slice(0, 50);

    if (currentFilterKeyword) {
      const keywordLower = currentFilterKeyword.toLowerCase();
      filtered = filtered.filter(r =>
        r?.spatialObject?.name?.toLowerCase().includes(keywordLower)
      );
    }

    if (filtered.length > 1) {
      filtered = [...filtered].sort((a, b) => {
        let cmp = 0;
        switch (currentSortField) {
          case 'score':    cmp = (a.score || 0) - (b.score || 0); break;
          case 'distance': cmp = (a.distance || 0) - (b.distance || 0); break;
          case 'name': {
            const na = a.spatialObject?.name || '';
            const nb = b.spatialObject?.name || '';
            cmp = na.localeCompare(nb);
            break;
          }
        }
        return currentSortOrder === 'asc' ? cmp : -cmp;
      });
    }

    return filtered.slice(0, 30);
  });
  
  // Computed property: Result count
  const resultCount = computed(() => {
    return results.value.length;
  });
  
  // Computed property: Whether there are results
  const hasResults = computed(() => {
    return results.value.length > 0;
  });
  
  /**
   * Set query results (optimized: avoid blocking main thread)
   */
  function setResults(newResults: QueryResult[]) {
    // Render max 50 results to prevent rAF loop blocking main thread
    const MAX_RESULTS = 50;
    if (newResults.length > MAX_RESULTS) {
      console.warn(`[ResultStore] Truncating ${newResults.length} results to ${MAX_RESULTS}`);
      newResults = newResults.slice(0, MAX_RESULTS);
    }
    console.log('[ResultStore] setResults called with', newResults.length, 'results');
    
    // CRITICAL: Early return for empty arrays to avoid unnecessary async operations
    if (!newResults || newResults.length === 0) {
      console.log('[ResultStore] Clearing results (empty array)');
      results.value = [];
      selectedResult.value = null;
      return;
    }
    
    console.log('[ResultStore] First new result:', newResults[0]);
    
    // For small arrays, update synchronously to avoid async overhead
    if (newResults.length <= 10) {
      console.log('[ResultStore] Setting results synchronously (small array)');
      results.value = [...newResults];
      if (!selectedResult.value && newResults.length > 0) {
        selectedResult.value = newResults[0] ?? null;
      }
      return;
    }
    
    // For large arrays, use batch processing to avoid blocking
    console.log('[ResultStore] Setting results with batch processing (large array)');
    
    // Clear old results synchronously first
    results.value = [];
    selectedResult.value = null;
    
    // Add new results in batches
    const BATCH_SIZE = 50;
    let index = 0;
    let batchTimer: number | null = null;
    
    function addBatch() {
      if (batchTimer) {
        cancelAnimationFrame(batchTimer);
        batchTimer = null;
      }
      
      const endIndex = Math.min(index + BATCH_SIZE, newResults.length);
      const batch = newResults.slice(index, endIndex);
      
      // Use push instead of spread to avoid creating new array
      for (const item of batch) {
        results.value.push(item);
      }
      
      index = endIndex;
      
      if (index < newResults.length) {
        // Use requestAnimationFrame for next batch
        batchTimer = requestAnimationFrame(addBatch);
      } else {
        // All results added, select first by default
        if (newResults.length > 0 && !selectedResult.value) {
          selectedResult.value = newResults[0] ?? null;
        }
        console.log('[ResultStore] Batch processing completed, total:', results.value.length);
        batchTimer = null;
      }
    }
    
    // Start adding batches after a small delay to ensure UI can render
    batchTimer = requestAnimationFrame(() => {
      requestAnimationFrame(addBatch);
    });
  }
  
  /**
   * Add results (for incremental updates)
   */
  function addResults(newResults: QueryResult[]) {
    // Merge results, remove duplicates
    const existingIds = new Set(results.value.map(r => r.id));
    const uniqueNewResults = newResults.filter(r => !existingIds.has(r.id));
    results.value = [...results.value, ...uniqueNewResults];
  }
  
  /**
   * Update results (for real-time updates)
   */
  function updateResults(newResults: QueryResult[]) {
    console.log('[ResultStore] updateResults called with', newResults.length, 'results');
    
    // For real-time updates, replace all results instead of merging
    if (newResults && newResults.length > 0) {
      console.log('[ResultStore] Replacing results with new data');
      console.log('[ResultStore] First new result:', newResults[0]);
      
      // Replace results directly
      results.value = [...newResults];
      
      console.log('[ResultStore] Results updated, new count:', results.value.length);
    } else {
      console.warn('[ResultStore] No new results to update');
    }
  }
  
  /**
   * Set selected result
   */
  function setSelectedResult(result: QueryResult | null) {
    selectedResult.value = result;
  }
  
  /**
   * Set route plan
   */
  function setRoutePlan(plan: RoutePlan | null) {
    routePlan.value = plan;
  }
  
  /**
   * Set sort
   */
  function setSort(field: SortField, order: SortOrder = 'desc') {
    sortField.value = field;
    sortOrder.value = order;
  }
  
  /**
   * Toggle sort order
   */
  function toggleSortOrder() {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
  }
  
  /**
   * Set filter keyword
   */
  function setFilterKeyword(keyword: string) {
    filterKeyword.value = keyword;
  }
  
  /**
   * Clear filter
   */
  function clearFilter() {
    filterKeyword.value = '';
  }
  
  /**
   * Get result by ID
   */
  function getResultById(id: string): QueryResult | undefined {
    return results.value.find(r => r.id === id);
  }
  
  /**
   * Clear results
   */
  function clearResults() {
    results.value = [];
    selectedResult.value = null;
    routePlan.value = null;
  }
  
  /**
   * Reset state
   */
  function reset() {
    clearResults();
    sortField.value = 'score';
    sortOrder.value = 'desc';
    filterKeyword.value = '';
  }
  
  return {
    // State
    results,
    topKResults, // Export topKResults alias
    selectedResult,
    selectedRoute, // Export selectedRoute alias
    routePlan,
    sortField,
    sortOrder,
    filterKeyword,
    // Computed properties
    sortedResults,
    resultCount,
    hasResults,
    // Methods
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

