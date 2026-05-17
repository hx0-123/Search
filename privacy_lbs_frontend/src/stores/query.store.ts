/**
 * Query State Management (Combined Version)
 * Merged from original query.store.ts + queryStore.ts
 * Manages query parameters, query status, query history, etc.
 */

import { defineStore } from 'pinia';
import { ref, reactive, computed } from 'vue';
import type { Query, RealTimeLocation, QueryHistoryItem, POI } from '@/types';
import { QueryStatus } from '@/types';
import { generateId } from '@/utils/crypto.util';
import { submitQuery, updateQuery, cancelQuery } from '@/services/query.service';
import { eventBus, Events } from '@/utils/event-bus';

export const useQueryStore = defineStore('query', () => {
  // --- Query Parameters ----------------------------------------

  /** Current query object */
  const currentQuery = ref<Query | null>(null);
  
  /** Query status */
  const queryStatus = ref<QueryStatus>(QueryStatus.IDLE);
  
  /** Query ID returned from backend */
  const queryId = ref<string | null>(null);
  
  /** Query text (keywords) */
  const queryText = ref<string>('');

  /** Alias for queryText, maintains backward compatibility */
  const keywords = ref<string>('');
  
  /** Current location (default: Beijing city center) */
  const currentLocation = ref<{ longitude: number; latitude: number }>({
    longitude: 116.4074,
    latitude: 39.9042,
  });
  
  /** Text-distance weight (alpha: 0-1) */
  const alpha = ref<number>(0.5);
  
  /** Top-K count */
  const k = ref<number>(10);
  
  /** Query radius (optional, meters) */
  const radius = ref<number | undefined>(undefined);
  
  /** Secure zone (returned from backend) */
  const safeZone = ref<{
    center: { longitude: number; latitude: number };
    radius?: number;
    polygon?: [number, number][];
  } | null>(null);
  
  /** Whether real-time update is enabled */
  const realTimeUpdateEnabled = ref<boolean>(false);
  
  /** Real-time location update interval (milliseconds) */
  const updateInterval = ref<number>(5000);
  
  /** Error message */
  const error = ref<string | null>(null);
  
  // --- Migrated fields from queryStore.ts ----------------------

  /** Query history records */
  const queryHistory = ref<QueryHistoryItem[]>([]);

  /** Current query start time (used for latency calculation) */
  const _queryStartTime = ref<number>(0);

  // --- POI Data Management --------------------------------------

  /** Uploaded POI list (with encryption status) */
  const uploadedPOIs = ref<(POI & { encrypted?: boolean })[]>([]);

  /** Last upload time */
  const lastUploadTime = ref<Date | null>(null);

  /** Total encryption time (milliseconds) */
  const totalEncryptionTimeMs = ref<number>(0);

  // --- Query Stage Tracking --------------------------------------

  /**
   * Stage progress status
   * encrypting  : Frontend location/keyword encryption
   * pruning     : Cloud spatial + keyword pruning
   * scoring     : Fog node scoring calculation
   * aggregation : Result aggregation and sorting
   */
  const stage = reactive({
    encrypting:  { progress: 0, timeMs: 0 },
    pruning:     { progress: 0, candidates: [0, 0] as [number, number] },
    scoring:     { progress: 0, completedNodes: 0, totalNodes: 5 },
    aggregation: { progress: 0, finalCount: 0 },
  });

  /** Currently active stage (null = not started/finished) */
  const activeStage = ref<'encrypting' | 'pruning' | 'scoring' | 'aggregation' | null>(null);

  /** Query overall start timestamp (used for total elapsed time calculation) */
  const queryWallStart = ref<number>(0);

  /** Total elapsed time (milliseconds, real-time update) */
  const totalElapsedMs = ref<number>(0);

  /** Total elapsed time timer */
  let _elapsedTimer: ReturnType<typeof setInterval> | null = null;

  /** Start total elapsed timer */
  function _startElapsedTimer() {
    queryWallStart.value = Date.now();
    totalElapsedMs.value = 0;
    if (_elapsedTimer) clearInterval(_elapsedTimer);
    _elapsedTimer = setInterval(() => {
      totalElapsedMs.value = Date.now() - queryWallStart.value;
    }, 100);
  }

  /** Stop total elapsed timer */
  function _stopElapsedTimer() {
    if (_elapsedTimer) { clearInterval(_elapsedTimer); _elapsedTimer = null; }
  }

  /** Reset all stage progress */
  function resetStages() {
    stage.encrypting  = { progress: 0, timeMs: 0 };
    stage.pruning     = { progress: 0, candidates: [0, 0] };
    stage.scoring     = { progress: 0, completedNodes: 0, totalNodes: 5 };
    stage.aggregation = { progress: 0, finalCount: 0 };
    activeStage.value = null;
    totalElapsedMs.value = 0;
    _stopElapsedTimer();
  }

  /**
   * Update specified stage progress (called by external or submit flow)
   * @param name   Stage name
   * @param data   Partial update data
   */
  function updateStage(
    name: 'encrypting' | 'pruning' | 'scoring' | 'aggregation',
    data: Partial<typeof stage[typeof name]>
  ) {
    activeStage.value = name;
    Object.assign(stage[name], data);
  }

  // --- Computed Properties ---------------------------------------

  /** Whether query parameters are valid */
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
  
  /** Whether query is in progress */
  const isQuerying = computed(() => {
    return (
      queryStatus.value === QueryStatus.PENDING ||
      queryStatus.value === QueryStatus.PROCESSING
    );
  });
  
  /** Query history count */
  const historyCount = computed(() => queryHistory.value.length);

  // --- Setter Methods --------------------------------------------

  /** Set query text (synchronously update keywords alias) */
  function setQueryText(text: string) {
    queryText.value = text;
    keywords.value = text;
  }
  
  /** Alias for setQueryText, maintains backward compatibility */
  function setKeywords(text: string) {
    setQueryText(text);
  }
  
  /** Set secure zone and notify map layer via eventBus */
  function setSafeZone(zone: {
    center: { longitude: number; latitude: number };
    radius?: number;
    polygon?: [number, number][];
  } | null) {
    console.log('[QueryStore] setSafeZone called with:', zone);
    safeZone.value = zone;
    setTimeout(() => {
      try {
        eventBus.emit(Events.SAFE_ZONE_UPDATED, zone);
        console.log('[QueryStore] SAFE_ZONE_UPDATED event emitted');
      } catch (e) {
        console.error('[QueryStore] Error emitting SAFE_ZONE_UPDATED:', e);
      }
    }, 0);
  }
  
  /** Set current location */
  function setCurrentLocation(location: { longitude: number; latitude: number }) {
    currentLocation.value = location;
  }
  
  /** Set weight alpha (0-1) */
  function setAlpha(value: number) {
    if (value >= 0 && value <= 1) alpha.value = value;
  }
  
  /** Set Top-K count (1-100) */
  function setK(value: number) {
    if (value >= 1 && value <= 100) k.value = value;
  }
  
  /** Set query radius */
  function setRadius(value: number | undefined) {
    radius.value = value;
  }
  
  /** Set whether real-time update is enabled */
  function setRealTimeUpdate(enabled: boolean) {
    realTimeUpdateEnabled.value = enabled;
  }
  
  // --- Migrated methods from queryStore.ts ----------------------

  /**
   * Initiate query (original queryStore.initiateQuery)
   * Only updates status to PENDING, does not call API, suitable for external triggers
   */
  function initiateQuery(params: {
    keywords: string;
    location: [number, number];
    radius: number;
    alpha: number;
  }) {
    setQueryText(params.keywords);
    setCurrentLocation({ longitude: params.location[0], latitude: params.location[1] });
    setRadius(params.radius);
    setAlpha(params.alpha);
    queryStatus.value = QueryStatus.PENDING;
    _queryStartTime.value = Date.now();
    error.value = null;
    console.log('[QueryStore] initiateQuery:', params);
  }

  /**
   * Update query status (original queryStore.updateStatus)
   */
  function updateStatus(status: QueryStatus, message?: string) {
    queryStatus.value = status;
    if (message) error.value = message;
    console.log('[QueryStore] updateStatus:', status, message ?? '');
  }

  /**
   * Clear query results and reset status (original queryStore.clearResults)
   */
  function clearResults() {
    queryStatus.value = QueryStatus.IDLE;
    queryId.value = null;
    currentQuery.value = null;
    safeZone.value = null;
    error.value = null;
    console.log('[QueryStore] clearResults');
  }

  /**
   * Append current query to history
   * @param resultCount   Number of results
   * @param safeZoneHit  Whether secure zone cache was hit
   */
  function recordHistory(resultCount: number, safeZoneHit = false) {
    if (!queryText.value.trim()) return;
    const latencyMs = _queryStartTime.value > 0 ? Date.now() - _queryStartTime.value : 0;
    const item: QueryHistoryItem = {
      id: generateId('hist'),
      timestamp: new Date(),
      keywords: queryText.value.trim().split(/\s+/).filter(Boolean),
      location: [currentLocation.value.longitude, currentLocation.value.latitude],
      radius: radius.value ?? 0,
      alpha: alpha.value,
      latencyMs,
      safeZoneHit,
      resultCount,
    };
    queryHistory.value.unshift(item);
    // Keep maximum 50 history records
    if (queryHistory.value.length > 50) queryHistory.value.length = 50;
    console.log('[QueryStore] recordHistory:', item);
  }

  /**
   * Clear query history
   */
  function clearHistory() {
    queryHistory.value = [];
  }

  // --- POI Data Management Methods ------------------------------

  /**
   * Append POI list (called after upload)
   * @param pois POI array to add
   * @param encryptionTimeMs Encryption time for this batch (milliseconds)
   */
  function addUploadedPOIs(pois: (POI & { encrypted?: boolean })[], encryptionTimeMs = 0) {
    uploadedPOIs.value.push(...pois);
    lastUploadTime.value = new Date();
    totalEncryptionTimeMs.value += encryptionTimeMs;
    console.log(`[QueryStore] addUploadedPOIs: +${pois.length} POIs, total=${uploadedPOIs.value.length}`);
  }

  /**
   * Mark specified POIs as encrypted
   * @param ids POI ids to mark
   */
  function markPOIsEncrypted(ids: string[]) {
    const idSet = new Set(ids);
    uploadedPOIs.value.forEach(p => {
      if (idSet.has(p.id)) p.encrypted = true;
    });
  }

  /**
   * Clear all uploaded POI data
   */
  function clearData() {
    uploadedPOIs.value = [];
    lastUploadTime.value = null;
    totalEncryptionTimeMs.value = 0;
    console.log('[QueryStore] clearData: POI data cleared');
  }

  // --- Core Async Operations ------------------------------------

  /**
   * Submit query (call API, poll results)
   * @returns QueryResult[] Result array
   */
  async function submit() {
    if (!isQueryValid.value) {
      error.value = 'Invalid query parameters';
      return;
    }
    
    try {
      queryStatus.value = QueryStatus.PENDING;
      error.value = null;
      _queryStartTime.value = Date.now();

      // --- Reset and start stage tracking ---
      resetStages();
      _startElapsedTimer();

      // --- Stage 1: Frontend encryption simulation (100ms animation) ---
      updateStage('encrypting', { progress: 0, timeMs: 0 });
      const encStart = Date.now();
      for (let p = 0; p <= 100; p += 20) {
        updateStage('encrypting', { progress: p });
        await new Promise(r => setTimeout(r, 16));
      }
      updateStage('encrypting', { progress: 100, timeMs: Date.now() - encStart });
      
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
      
      // --- Stage 2: Cloud pruning (send request, animate to 80%, wait for response) ---
      updateStage('pruning', { progress: 0, candidates: [5000, 5000] });
      const pruneAnim = setInterval(() => {
        if (stage.pruning.progress < 80) {
          updateStage('pruning', { progress: stage.pruning.progress + 5 });
        }
      }, 120);

      // --- Send actual API request ---
      queryStatus.value = QueryStatus.PROCESSING;
      const {
        results,
        queryId: backendQueryId,
        safeZone: returnedSafeZone,
      } = await submitQuery(query);
      
      clearInterval(pruneAnim);
      const afterPrune = Math.max(50, Math.round(results.length * 1.5));
      updateStage('pruning', { progress: 100, candidates: [5000, afterPrune] });

      queryId.value = backendQueryId;
      if (returnedSafeZone) setSafeZone(returnedSafeZone);

      // --- Stage 3: Fog node scoring (simulate progressive completion) ---
      updateStage('scoring', { progress: 0, completedNodes: 0, totalNodes: 5 });
      for (let node = 1; node <= 5; node++) {
        await new Promise(r => setTimeout(r, 60));
        updateStage('scoring', {
          completedNodes: node,
          progress: Math.round((node / 5) * 100),
        });
      }

      // --- Stage 4: Aggregation and sorting ---
      updateStage('aggregation', { progress: 0, finalCount: 0 });
      for (let p = 0; p <= 100; p += 25) {
        updateStage('aggregation', { progress: p });
        await new Promise(r => setTimeout(r, 20));
      }
      updateStage('aggregation', { progress: 100, finalCount: results.length });
      activeStage.value = null;
      _stopElapsedTimer();
      
      queryStatus.value = QueryStatus.SUCCESS;
      
      // Record history
      recordHistory(results.length, false);

      return results;
    } catch (err: any) {
      _stopElapsedTimer();
      activeStage.value = null;
      queryStatus.value = QueryStatus.ERROR;
      error.value = err.message || 'Query failed';
      throw err;
    }
  }
  
  /**
   * Real-time location update (continuous query)
   * @returns QueryResult[] Updated result array
   */
  async function update(location: RealTimeLocation, signal?: AbortSignal) {
    if (!queryId.value) {
      console.warn('[QueryStore] update: No queryId available');
      return;
    }
    
    try {
      // Note: Real-time update does not modify global queryStatus to avoid affecting routing and other components
      error.value = null;
      
      currentLocation.value = {
        longitude: location.longitude,
        latitude: location.latitude,
      };
      
      const response = await updateQuery(queryId.value, location, signal);
      
      if (response?.safeZone) setSafeZone(response.safeZone);
      
      return response.results || [];
    } catch (err: any) {
      // AbortError is intentional cancellation, not an error
      if (err?.name === 'AbortError' || err?.code === 'ERR_CANCELED') {
        console.log('[QueryStore] update: request aborted (navigation or timeout)');
        return [];
      }
      error.value = err.message || 'Query update failed';
      throw err;
    }
  }
  
  /**
   * Cancel current query
   */
  async function cancel() {
    if (queryId.value) {
      try {
        await cancelQuery(queryId.value);
      } catch (err) {
        console.error('[QueryStore] cancel: API call failed:', err);
      }
    }
    queryStatus.value = QueryStatus.IDLE;
    queryId.value = null;
    currentQuery.value = null;
    error.value = null;
  }
  
  /**
   * Full reset of all state
   */
  function reset() {
    queryStatus.value = QueryStatus.IDLE;
    queryId.value = null;
    currentQuery.value = null;
    queryText.value = '';
    keywords.value = '';
    alpha.value = 0.5;
    k.value = 10;
    radius.value = undefined;
    realTimeUpdateEnabled.value = false;
    safeZone.value = null;
    error.value = null;
    _queryStartTime.value = 0;
  }
  
  /** Count of encrypted POIs */
  const encryptedPOICount = computed(() => uploadedPOIs.value.filter(p => p.encrypted).length);

  /** POI count by category */
  const poiCategoryStats = computed(() => {
    const stats: Record<string, number> = {};
    uploadedPOIs.value.forEach(p => {
      const cat = p.category || 'Uncategorized';
      stats[cat] = (stats[cat] || 0) + 1;
    });
    return stats;
  });

  // --- Exports -------------------------------------------------
  return {
    // State
    currentQuery,
    queryStatus,
    queryId,
    queryText,
    keywords,
    currentLocation,
    alpha,
    k,
    radius,
    safeZone,
    realTimeUpdateEnabled,
    updateInterval,
    error,
    queryHistory,
    uploadedPOIs,
    lastUploadTime,
    totalEncryptionTimeMs,
    // Query Stage Tracking
    stage,
    activeStage,
    totalElapsedMs,
    resetStages,
    updateStage,
    // Computed Properties
    isQueryValid,
    isQuerying,
    historyCount,
    encryptedPOICount,
    poiCategoryStats,
    // Setter
    setQueryText,
    setKeywords,
    setCurrentLocation,
    setAlpha,
    setK,
    setRadius,
    setSafeZone,
    setRealTimeUpdate,
    // Migrated from queryStore.ts
    initiateQuery,
    updateStatus,
    clearResults,
    recordHistory,
    clearHistory,
    // POI Data Management
    addUploadedPOIs,
    markPOIsEncrypted,
    clearData,
    // Core Async Operations
    submit,
    update,
    cancel,
    reset,
  };
});
