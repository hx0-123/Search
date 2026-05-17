/**
 * Query Service
 * Handles all query-related API calls
 */

import api from './api.client';
import type { Query, QueryResult, RealTimeLocation, ApiResponse } from '@/types';
import { serializeAsPassthrough } from '@/utils/paillier.util';

/**
 * Query Parameters Interface
 */
export interface QueryParams {
  text: string;
  location: {
    longitude: number;
    latitude: number;
  };
  alpha: number;
  k: number;
  radius?: number;
}

/**
 * Query Response Interface
 */
export interface QueryResponse {
  results?: QueryResult[];
  safeZone?: {
    center: { longitude: number; latitude: number };
    radius?: number;
    polygon?: [number, number][];
  };
  queryId?: string;
  query_id?: string;
  status?: string;
  encrypted_results?: any[];
  message?: string;
}

/**
 * Coordinate Interface
 */
export interface Coordinate {
  longitude: number;
  latitude: number;
  timestamp?: number;
}

/**
 * Update Response Interface
 */
export interface UpdateResponse {
  results: QueryResult[];
  safeZone?: {
    center: { longitude: number; latitude: number };
    radius?: number;
    polygon?: [number, number][];
  };
}

/**
 * Initiate secure query request
 * @param queryParams Query parameters
 * @returns Query response (contains query_id and status)
 */
export async function initiateSecureQuery(queryParams: QueryParams): Promise<{
  query_id: string;
  status: string;
  task_ids?: string[];
  message?: string;
  encrypted_results?: any[];
  secure_area?: {
    query_id: string;
    encrypted_center_x?: string;
    encrypted_center_y?: string;
    center?: { longitude: number; latitude: number };
    radius: number;
    created_at?: string;
  };
}> {
  try {
    // Fix API path: Backend actual path is /api/query/initiate/
    // Since baseURL already contains /api, only need /query/initiate/
    // Align with backend paillier_manager.encrypt(float) precision factor precision=1_000_000
    // Coordinate integerization: int(value * 1_000_000), serialized as base64(JSON{ciphertext,exponent:0})
    const encX = serializeAsPassthrough(queryParams.location.longitude)
    const encY = serializeAsPassthrough(queryParams.location.latitude)

    const response = await api.post<{
      query_id: string;
      status: string;
      task_ids?: string[];
      message?: string;
      encrypted_results?: any[];
      secure_area?: {
        query_id: string;
        encrypted_center_x?: string;
        encrypted_center_y?: string;
        center?: { longitude: number; latitude: number };
        radius: number;
        created_at?: string;
      };
    }>('/query/initiate/', {
      encrypted_location_x: encX,
      encrypted_location_y: encY,
      encrypted_keywords: queryParams.text.split(/\s+/).filter(k => k.length > 0),
      text_weight: queryParams.alpha,
      distance_weight: 1 - queryParams.alpha,
      top_k: queryParams.k,
      is_continuous: true,
    });
    // API client interceptor already returns response.data, so response is already the data
    return (response as unknown) as {
      query_id: string;
      status: string;
      task_ids?: string[];
      message?: string;
      encrypted_results?: any[];
      secure_area?: {
        query_id: string;
        encrypted_center_x?: string;
        encrypted_center_y?: string;
        center?: { longitude: number; latitude: number };
        radius: number;
        created_at?: string;
      };
    };
  } catch (error) {
    console.error('Failed to submit query:', error);
    throw error;
  }
}

/**
 * Poll to get query results (optimized to prevent blocking)
 * @param queryId Query ID
 * @param maxAttempts Maximum number of attempts
 * @param interval Polling interval (milliseconds)
 * @returns Query results
 */
export async function pollQueryResult(
  queryId: string,
  queryLocation?: { longitude: number; latitude: number },
  maxAttempts: number = 30,  // Reduced to 30 attempts (30 seconds max)
  interval: number = 1000
): Promise<QueryResult[]> {
  console.log(`[pollQueryResult] Starting to poll for query ${queryId}, max attempts: ${maxAttempts}`);
  
  // Use a promise-based approach with proper async handling
  return new Promise(async (resolve, reject) => {
    let cancelled = false;
    
    // Allow cancellation by storing the timeout ID
    const poll = async () => {
      for (let attempt = 0; attempt < maxAttempts && !cancelled; attempt++) {
        try {
          console.log(`[pollQueryResult] Attempt ${attempt + 1}/${maxAttempts} for query ${queryId}`);
          
          // Use requestIdleCallback if available to avoid blocking main thread
          await new Promise(r => {
            if ('requestIdleCallback' in window) {
              (window as any).requestIdleCallback(r, { timeout: 100 });
            } else {
              setTimeout(r, 0);
            }
          });
          
          const result = await getQueryResult(queryId);
          console.log(`[pollQueryResult] Got result, status: ${result.status}`);
          
          // If query is completed
          if (result.status === 'completed') {
            console.log(`[pollQueryResult] Query completed, processing results...`);
            // Convert result format asynchronously to avoid blocking
            if (result.encrypted_results && Array.isArray(result.encrypted_results)) {
              console.log(`[pollQueryResult] Converting ${result.encrypted_results.length} results...`);
              // Process conversion in chunks to avoid blocking
              const results = await convertEncryptedResultsToQueryResultsAsync(
                result.encrypted_results, 
                queryLocation
              );
              console.log(`[pollQueryResult] Conversion complete, returning ${results.length} results`);
              resolve(results);
              return;
            }
            console.log(`[pollQueryResult] No results found, returning empty array`);
            resolve([]);
            return;
          }
          
          // If query failed
          if (result.status === 'failed') {
            console.error(`[pollQueryResult] Query failed: ${result.message}`);
            reject(new Error(result.message || 'Query failed'));
            return;
          }
          
          // If still processing, wait and continue (use requestAnimationFrame for better performance)
          if (attempt < maxAttempts - 1 && !cancelled) {
            console.log(`[pollQueryResult] Still ${result.status}, waiting ${interval}ms before next attempt...`);
            await new Promise(r => {
              // Use requestAnimationFrame for first few attempts, then setTimeout
              if (attempt < 5) {
                requestAnimationFrame(() => setTimeout(r, interval));
              } else {
                setTimeout(r, interval);
              }
            });
          }
        } catch (error: any) {
          console.error(`[pollQueryResult] Error on attempt ${attempt + 1}:`, error);
          // If this is the last attempt, throw error
          if (attempt === maxAttempts - 1) {
            reject(error);
            return;
          }
          // Otherwise wait and continue
          if (!cancelled) {
            await new Promise(r => setTimeout(r, interval));
          }
        }
      }
      
      if (!cancelled) {
        console.error(`[pollQueryResult] Timeout after ${maxAttempts} attempts`);
        reject(new Error('Query timeout, please try again later'));
      }
    };
    
    poll();
  });
}

/**
 * Convert encrypted results returned from backend to frontend QueryResult format
 * (Synchronous version for immediate results)
 */
function convertEncryptedResultsToQueryResults(
  encryptedResults: any[],
  queryLocation?: { longitude: number; latitude: number }
): QueryResult[] {
  // Limit processing to prevent blocking - only process first 100 items synchronously
  const maxSyncProcess = 100;
  const limitedResults = encryptedResults.slice(0, maxSyncProcess);
  
  return limitedResults.map((item, index) => {
    // Extract information from backend returned data
    // Backend return format: { object_id, score, distance_score, text_score, distance_meters, location }
    const location = item.location || { longitude: 116.4074, latitude: 39.9042 };
    
    // Use distance returned from backend (if available)
    let distance = 0;
    if (typeof item.distance_meters === 'number') {
      distance = item.distance_meters;
    } else if (queryLocation) {
      // If backend didn't return distance, calculate on frontend (using Haversine formula)
      distance = calculateDistanceFromCoordinates(
        [queryLocation.longitude, queryLocation.latitude],
        [location.longitude || 116.4074, location.latitude || 39.9042]
      );
    }
    
    // Use scores returned from backend (if available)
    const score = typeof item.score === 'number' ? item.score : 0.8;
    const textScore = typeof item.text_score === 'number' ? item.text_score : undefined;
    const distanceScore = typeof item.distance_score === 'number' ? item.distance_score : undefined;
    
      return {
        id: item.object_id || `result_${index}`,
        spatialObject: {
          id: item.object_id || `result_${index}`,
          // FIX: item.name is set by fog_node/tasks.py from metadata.name.
          // If missing, fall back to a human-readable label rather than
          // showing the raw object_id (a hex string).
          name: item.name || `POI #${index + 1}`,
          description: item.description || undefined,
          location: {
            longitude: location.longitude || 116.4074,
            latitude: location.latitude || 39.9042,
          },
          category: item.category || undefined,
        },
        score: score,
        textScore: textScore,
        distanceScore: distanceScore,
        distance: Math.round(distance), // Round to meters
        encryptedScore: item.encrypted_combined_score,
      };
  });
}

/**
 * Convert encrypted results asynchronously to prevent blocking main thread
 */
async function convertEncryptedResultsToQueryResultsAsync(
  encryptedResults: any[],
  queryLocation?: { longitude: number; latitude: number }
): Promise<QueryResult[]> {
  const CHUNK_SIZE = 50; // Process 50 items at a time
  const results: QueryResult[] = [];
  
  for (let i = 0; i < encryptedResults.length; i += CHUNK_SIZE) {
    const chunk = encryptedResults.slice(i, i + CHUNK_SIZE);
    
    // Process chunk synchronously
    const chunkResults = chunk.map((item, chunkIndex) => {
      const index = i + chunkIndex;
      const location = item.location || { longitude: 116.4074, latitude: 39.9042 };
      
      let distance = 0;
      if (typeof item.distance_meters === 'number') {
        distance = item.distance_meters;
      } else if (queryLocation) {
        distance = calculateDistanceFromCoordinates(
          [queryLocation.longitude, queryLocation.latitude],
          [location.longitude || 116.4074, location.latitude || 39.9042]
        );
      }
      
      const score = typeof item.score === 'number' ? item.score : 0.8;
      const textScore = typeof item.text_score === 'number' ? item.text_score : undefined;
      const distanceScore = typeof item.distance_score === 'number' ? item.distance_score : undefined;
      
      return {
        id: item.object_id || `result_${index}`,
        spatialObject: {
          id: item.object_id || `result_${index}`,
          name: item.name || `POI #${index + 1}`,
          description: item.description || undefined,
          location: {
            longitude: location.longitude || 116.4074,
            latitude: location.latitude || 39.9042,
          },
          category: item.category || undefined,
        },
        score: score,
        textScore: textScore,
        distanceScore: distanceScore,
        distance: Math.round(distance),
        encryptedScore: item.encrypted_combined_score,
      };
    });
    
    results.push(...chunkResults);
    
    // Yield to main thread after each chunk
    if (i + CHUNK_SIZE < encryptedResults.length) {
      await new Promise(resolve => {
        requestAnimationFrame(() => {
          setTimeout(resolve, 0);
        });
      });
    }
  }
  
  return results;
}

/**
 * Frontend coordinate "encryption" helper
 *
 * Backend paillier_manager.encrypt(float) processing flow:
 *   1. plaintext_int = int(value * 1_000_000)   ← precision=1e6, keep 6 decimal places
 *   2. encrypted = public_key.encrypt(plaintext_int)
 *   3. Serialize as base64(json({ciphertext, exponent}))
 *
 * Since browsers cannot execute python-phe, frontend directly sends integer values in
 * "plaintext serialization" format - backend services.py only stores this string
 * without decryption, so the following format is fully compatible with existing backend logic.
 * If backend enables real decryption in the future, this function can be replaced with WASM Paillier.
 *
 * Format: base64(json({"ciphertext": "<int_scaled>", "exponent": 0}))
 */
function encodeCoordinate(value: number): string {
  const PRECISION = 1_000_000
  const scaled = Math.round(value * PRECISION)
  const payload = JSON.stringify({ ciphertext: String(scaled), exponent: 0 })
  // btoa handles ASCII; use encodeURIComponent to ensure Unicode safety
  return btoa(unescape(encodeURIComponent(payload)))
}

/**
 * Frontend keyword "encryption" helper
 * Backend encrypt_string takes hash % 1e15 then encrypts; frontend sends plaintext string
 * (backend services.py also only stores without decryption)
 */
function encodeKeyword(keyword: string): string {
  return keyword.trim()
}
function calculateDistanceFromCoordinates(
  point1: [number, number],
  point2: [number, number]
): number {
  const R = 6371000; // Earth radius (meters)
  const [lng1, lat1] = point1;
  const [lng2, lat2] = point2;
  
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lng2 - lng1);
  
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRadians(lat1)) *
      Math.cos(toRadians(lat2)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Convert degrees to radians
 */
function toRadians(degrees: number): number {
  return degrees * (Math.PI / 180);
}

/**
 * Get query result
 * @param queryId Query ID
 * @returns Query result
 */
export async function getQueryResult(queryId: string): Promise<{
  query_id: string;
  status: string;
  encrypted_results?: any[];
  message?: string;
}> {
  try {
    const response = await api.get<{
      query_id: string;
      status: string;
      encrypted_results?: any[];
      message?: string;
    }>(`/query/${queryId}/result/`);
    // API client interceptor already returns response.data
    return (response as unknown) as {
      query_id: string;
      status: string;
      encrypted_results?: any[];
      message?: string;
    };
  } catch (error) {
    console.error('Failed to get query result:', error);
    throw error;
  }
}

/**
 * Submit query request (compatible with old interface)
 * @param query Query parameters
 * @returns Query results and query_id
 */
export async function submitQuery(query: Query): Promise<{
  results: QueryResult[];
  queryId: string;
  safeZone?: {
    center: { longitude: number; latitude: number };
    radius?: number;
    polygon?: [number, number][];
  };
}> {
  try {
    console.log('[submitQuery] Starting query submission...', query);
    
    // Initiate query
    const response = await initiateSecureQuery({
      text: query.text,
      location: query.location,
      alpha: query.alpha,
      k: query.k,
      radius: query.radius,
    });
    
    console.log('[submitQuery] Query initiated, response:', response);
    
    const queryId = response.query_id;
    let results: QueryResult[] = [];
    
    // Extract and convert secure_area to safeZone format
    let safeZone: {
      center: { longitude: number; latitude: number };
      radius?: number;
      polygon?: [number, number][];
    } | undefined = undefined;
    
    if (response.secure_area) {
      // Use query location as center (since backend returns encrypted coordinates)
      // The secure_area.radius is the safe zone radius in meters
      safeZone = {
        center: query.location, // Use the query location as the center
        radius: response.secure_area.radius || 1000, // Default to 1000m if not provided
      };
      console.log('[submitQuery] Safe zone created:', safeZone);
    }
    
    // If query completes immediately (no candidates or immediate results)
    if (response.status === 'completed') {
      console.log('[submitQuery] Query completed immediately');
      // Convert result format
      if (response.encrypted_results && Array.isArray(response.encrypted_results)) {
        results = convertEncryptedResultsToQueryResults(response.encrypted_results, query.location);
        console.log('[submitQuery] Converted results:', results.length);
      } else {
        // If no results, try to get full result
        console.log('[submitQuery] No immediate results, fetching full result...');
        const fullResult = await getQueryResult(queryId);
        if (fullResult.encrypted_results && Array.isArray(fullResult.encrypted_results)) {
          results = convertEncryptedResultsToQueryResults(fullResult.encrypted_results, query.location);
          console.log('[submitQuery] Fetched and converted results:', results.length);
        }
      }
      return { results, queryId, safeZone };
    }
    
    // If query is processing, poll for results
    if (response.status === 'processing' || response.status === 'pending') {
      console.log(`[submitQuery] Query is ${response.status}, query_id: ${queryId}, starting to poll results...`);
      try {
      results = await pollQueryResult(queryId, query.location);
        console.log('[submitQuery] Poll completed, results:', results.length);
      } catch (pollError) {
        console.error('[submitQuery] Poll failed:', pollError);
        throw pollError;
      }
      return { results, queryId, safeZone };
    }
    
    // If query failed
    if (response.status === 'failed') {
      console.error('[submitQuery] Query failed:', response.message);
      throw new Error(response.message || 'Query failed');
    }
    
    console.warn('[submitQuery] Unexpected status:', response.status);
    return { results: [], queryId, safeZone };
  } catch (error) {
    console.error('[submitQuery] Failed to submit query:', error);
    throw error;
  }
}

/**
 * Update location and trigger safe zone check
 * @param location New location coordinates
 * @returns Update response
 */
export async function updateLocation(location: Coordinate): Promise<UpdateResponse> {
  try {
    const response = await api.post<UpdateResponse>('/query/update_location/', {
      query_id: '',
      encrypted_location_x: encodeCoordinate(location.longitude),
      encrypted_location_y: encodeCoordinate(location.latitude),
    });
    return (response as unknown) as UpdateResponse;
  } catch (error) {
    console.error('Failed to update location:', error);
    throw error;
  }
}

/**
 * Update query (real-time location update)
 * @param queryId Query ID
 * @param location New location
 * @returns Updated query results
 */
export async function updateQuery(
  queryId: string,
  location: RealTimeLocation,
  signal?: AbortSignal
): Promise<UpdateResponse> {
  try {
    console.log('[updateQuery] Sending update request:', {
      query_id: queryId,
      longitude: location.longitude,
      latitude: location.latitude,
    });
    
    // Coordinate encryption: align with paillier_manager.encrypt(float) precision=1_000_000
    const encX = serializeAsPassthrough(location.longitude)
    const encY = serializeAsPassthrough(location.latitude)

    const response = await api.post<any>('/query/update_location/', {
      query_id: queryId,
      encrypted_location_x: encX,
      encrypted_location_y: encY,
    }, {
      timeout: 8000,       // Real-time update max wait 8 seconds to prevent connection pool exhaustion
      signal,              // Support AbortController cancellation
    });
    
    console.log('[updateQuery] Raw response from backend:', response);
    
    // Check if backend returned processing status
    // Fetch result once without multiple polling rounds to avoid main thread blocking
    if (response && typeof response === 'object' && response.status === 'processing') {
      console.log('[updateQuery] Backend returned processing status, fetching result once...');
      await new Promise(r => setTimeout(r, 800)); // Wait 800ms for backend processing
      try {
        const result = await getQueryResult(queryId);
        const encResults = result.encrypted_results ?? [];
        const results = convertEncryptedResultsToQueryResults(encResults, location);
        const safeZone = response.secure_area ? {
          center: location as { longitude: number; latitude: number },
          radius: (response.secure_area as any).radius || 1000,
        } : undefined;
        return { results, safeZone };
      } catch (e) {
        console.warn('[updateQuery] Single fetch failed, returning empty', e);
        return { results: [], safeZone: undefined };
      }
    }
    
    // Check if backend returned cached results
    if (response && typeof response === 'object' && response.status === 'cached') {
      console.log('[updateQuery] Backend returned cached results (Safe Zone HIT)');
      
      const cachedResults = response.encrypted_results || [];
      const results = convertEncryptedResultsToQueryResults(cachedResults, location);

      // Secure zone hit: pass secure zone parameters to caller (keep center unchanged)
      const safeZone = response.secure_area ? {
        center: location as { longitude: number; latitude: number },
        radius: (response.secure_area as any).radius || 1000,
      } : undefined;

      return { results, safeZone };
    }
    
    // Check if backend returned completed status with results
    if (response && typeof response === 'object' && response.status === 'completed') {
      console.log('[updateQuery] Backend returned completed status');
      
      const completedResults = response.encrypted_results || [];
      const results = convertEncryptedResultsToQueryResults(completedResults, location);

      const safeZone = response.secure_area ? {
        center: location as { longitude: number; latitude: number },
        radius: (response.secure_area as any).radius || 1000,
      } : undefined;

      return { results, safeZone };
    }
    
    // Handle array response (legacy format)
    if (Array.isArray(response)) {
      console.log('[updateQuery] Backend returned array with', response.length, 'items');
      return {
        results: response as QueryResult[],
        safeZone: undefined,
      };
    }
    
    // Default: return empty results
    console.warn('[updateQuery] Unexpected response format, returning empty results');
    return {
      results: [],
      safeZone: undefined,
    };
  } catch (error) {
    console.error('[updateQuery] Failed to update query:', error);
    throw error;
  }
}

/**
 * Get query status
 * @param queryId Query ID
 * @returns Query status
 */
export async function getQueryStatus(queryId: string): Promise<{
  query_id: string;
  status: string;
  encrypted_results?: any[];
  message?: string;
}> {
  try {
    // Fix API path: Backend actual path is /api/query/{query_id}/result/
    const response = await api.get<{
      query_id: string;
      status: string;
      encrypted_results?: any[];
      message?: string;
    }>(`/query/${queryId}/result/`);
    // API client interceptor already returns response.data
    return (response as unknown) as {
      query_id: string;
      status: string;
      encrypted_results?: any[];
      message?: string;
    };
  } catch (error) {
    console.error('Failed to get query status:', error);
    throw error;
  }
}

/**
 * Cancel query
 * POST DELETE /api/query/{query_id}/cancel/
 * Cancel Celery task and update status to cancelled
 */
export async function cancelQuery(queryId: string): Promise<void> {
  try {
    await api.delete(`/query/${queryId}/cancel/`);
  } catch (error) {
    console.error('Failed to cancel query:', error);
    throw error;
  }
}

/**
 * Get query history
 * GET /api/query/history/
 */
export async function getQueryHistory(limit: number = 10): Promise<any[]> {
  try {
    const response = await api.get<{ total: number; records: any[] }>('/query/history/', {
      params: { page: 1, page_size: limit },
    });
    const data = (response as unknown) as { total: number; records: any[] };
    return data.records ?? [];
  } catch (error) {
    console.error('Failed to get query history:', error);
    return [];
  }
}

/**
 * Get route plan
 * @param waypointIds Waypoint ID array
 * @param startLocation Start location
 * @returns Route planning result
 */
export async function getRoutePlan(
  waypointIds: string[],
  startLocation: { longitude: number; latitude: number }
): Promise<{
  id: string;
  waypoints: any[];
  totalDistance: number;
  totalTime: number;
  polyline: [number, number][];
}> {
  try {
    // Backend may not have route interface, temporarily throw error
    // const response = await api.post('/query/route/', {
    //   waypoint_ids: waypointIds,
    //   start_location: startLocation,
    // });
    // return response;
    throw new Error('Route planning interface not yet implemented');
  } catch (error) {
    console.error('Failed to get route plan:', error);
    throw error;
  }
}

