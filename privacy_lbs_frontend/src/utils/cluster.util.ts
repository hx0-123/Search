/**
 * Map marker clustering utility
 * When there are many result points, use clustering to optimize performance
 */

import type { QueryResult } from '@/types';

export interface ClusterPoint {
  id: string;
  longitude: number;
  latitude: number;
  result?: QueryResult;
  count?: number;
}

/**
 * Simple grid clustering algorithm
 * @param results Query results array
 * @param zoom Current map zoom level
 * @param threshold Clustering threshold (pixels)
 * @returns Clustered points array
 */
export function clusterResults(
  results: QueryResult[],
  zoom: number,
  threshold: number = 50
): ClusterPoint[] {
  if (results.length === 0) return [];
  
  // Determine whether to enable clustering based on zoom level
  // Higher zoom level (larger number) means more detailed display, smaller clustering threshold
  const clusterZoom = zoom < 12;
  
  if (!clusterZoom || results.length < 10) {
    // No clustering, return all points directly
    return results.map(result => ({
      id: result.id,
      longitude: result.spatialObject.location.longitude,
      latitude: result.spatialObject.location.latitude,
      result: result,
    }));
  }
  
  // Calculate grid size (based on zoom level and threshold)
  const gridSize = threshold / (256 * Math.pow(2, zoom));
  
  // Use grid clustering
  const grid = new Map<string, ClusterPoint[]>();
  
  for (const result of results) {
    const { longitude, latitude } = result.spatialObject.location;
    
    // Calculate grid coordinates
    const gridX = Math.floor(longitude / gridSize);
    const gridY = Math.floor(latitude / gridSize);
    const key = `${gridX},${gridY}`;
    
    if (!grid.has(key)) {
      grid.set(key, []);
    }
    
    grid.get(key)!.push({
      id: result.id,
      longitude,
      latitude,
      result,
    });
  }
  
  // Generate cluster points
  const clusters: ClusterPoint[] = [];
  
  for (const [key, points] of grid.entries()) {
    if (points.length === 1) {
      // Single point, add directly
      clusters.push(points[0]);
    } else {
      // Multiple points, create cluster
      const centerLng = points.reduce((sum, p) => sum + p.longitude, 0) / points.length;
      const centerLat = points.reduce((sum, p) => sum + p.latitude, 0) / points.length;
      
      clusters.push({
        id: `cluster_${key}`,
        longitude: centerLng,
        latitude: centerLat,
        count: points.length,
      });
    }
  }
  
  return clusters;
}

/**
 * Determine whether clustering should be displayed
 * @param resultCount Result count
 * @param zoom Zoom level
 * @returns Whether clustering should be applied
 */
export function shouldCluster(resultCount: number, zoom: number): boolean {
  return resultCount > 20 && zoom < 14;
}



