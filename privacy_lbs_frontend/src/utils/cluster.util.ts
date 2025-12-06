/**
 * 地图标记聚类工具
 * 当结果点很多时，使用聚类来优化性能
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
 * 简单的网格聚类算法
 * @param results 查询结果数组
 * @param zoom 当前地图缩放级别
 * @param threshold 聚类阈值（像素）
 * @returns 聚类后的点数组
 */
export function clusterResults(
  results: QueryResult[],
  zoom: number,
  threshold: number = 50
): ClusterPoint[] {
  if (results.length === 0) return [];
  
  // 根据缩放级别决定是否启用聚类
  // 缩放级别越高（数字越大），显示越详细，聚类阈值越小
  const clusterZoom = zoom < 12;
  
  if (!clusterZoom || results.length < 10) {
    // 不聚类，直接返回所有点
    return results.map(result => ({
      id: result.id,
      longitude: result.spatialObject.location.longitude,
      latitude: result.spatialObject.location.latitude,
      result: result,
    }));
  }
  
  // 计算网格大小（根据缩放级别和阈值）
  const gridSize = threshold / (256 * Math.pow(2, zoom));
  
  // 使用网格聚类
  const grid = new Map<string, ClusterPoint[]>();
  
  for (const result of results) {
    const { longitude, latitude } = result.spatialObject.location;
    
    // 计算网格坐标
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
  
  // 生成聚类点
  const clusters: ClusterPoint[] = [];
  
  for (const [key, points] of grid.entries()) {
    if (points.length === 1) {
      // 单个点，直接添加
      clusters.push(points[0]);
    } else {
      // 多个点，创建聚类
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
 * 判断是否应该显示聚类
 * @param resultCount 结果数量
 * @param zoom 缩放级别
 * @returns 是否应该聚类
 */
export function shouldCluster(resultCount: number, zoom: number): boolean {
  return resultCount > 20 && zoom < 14;
}



