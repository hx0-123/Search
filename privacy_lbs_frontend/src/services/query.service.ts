/**
 * 查询服务
 * 处理所有与查询相关的API调用
 */

import api from './api.client';
import type { Query, QueryResult, RealTimeLocation, ApiResponse } from '@/types';

/**
 * 查询参数接口
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
 * 查询响应接口
 */
export interface QueryResponse {
  results: QueryResult[];
  safeZone?: {
    center: { longitude: number; latitude: number };
    radius?: number;
    polygon?: [number, number][];
  };
  queryId?: string;
}

/**
 * 坐标接口
 */
export interface Coordinate {
  longitude: number;
  latitude: number;
  timestamp?: number;
}

/**
 * 更新响应接口
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
 * 发起安全查询请求
 * @param queryParams 查询参数
 * @returns 查询响应
 */
export async function initiateSecureQuery(queryParams: QueryParams): Promise<QueryResponse> {
  try {
    const response = await api.post<QueryResponse>('/secure_query/submit/', {
      text: queryParams.text,
      location: queryParams.location,
      alpha: queryParams.alpha,
      k: queryParams.k,
      radius: queryParams.radius,
    });
    return response;
  } catch (error) {
    console.error('提交查询失败:', error);
    throw error;
  }
}

/**
 * 发起查询请求（兼容旧接口）
 * @param query 查询参数
 * @returns 查询结果
 */
export async function submitQuery(query: Query): Promise<QueryResult[] | QueryResponse> {
  try {
    const response = await initiateSecureQuery({
      text: query.text,
      location: query.location,
      alpha: query.alpha,
      k: query.k,
      radius: query.radius,
    });
    return response;
  } catch (error) {
    console.error('提交查询失败:', error);
    throw error;
  }
}

/**
 * 更新位置并触发安全区域检查
 * @param location 新的位置坐标
 * @returns 更新响应
 */
export async function updateLocation(location: Coordinate): Promise<UpdateResponse> {
  try {
    const response = await api.patch<UpdateResponse>('/secure_query/update_location/', {
      longitude: location.longitude,
      latitude: location.latitude,
      timestamp: location.timestamp || Date.now(),
    });
    return response;
  } catch (error) {
    console.error('更新位置失败:', error);
    throw error;
  }
}

/**
 * 更新查询（实时位置更新）
 * @param queryId 查询ID
 * @param location 新的位置
 * @returns 更新后的查询结果
 */
export async function updateQuery(
  queryId: string,
  location: RealTimeLocation
): Promise<QueryResult[] | UpdateResponse> {
  try {
    const response = await api.patch<UpdateResponse>(`/secure_query/${queryId}/update/`, {
      location: {
        longitude: location.longitude,
        latitude: location.latitude,
      },
      timestamp: location.timestamp,
    });
    return response;
  } catch (error) {
    console.error('更新查询失败:', error);
    throw error;
  }
}

/**
 * 获取查询状态
 * @param queryId 查询ID
 * @returns 查询状态
 */
export async function getQueryStatus(queryId: string): Promise<{
  status: string;
  progress?: number;
  message?: string;
}> {
  try {
    const response = await api.get<{
      status: string;
      progress?: number;
      message?: string;
    }>(`/secure_query/${queryId}/status/`);
    return response;
  } catch (error) {
    console.error('获取查询状态失败:', error);
    throw error;
  }
}

/**
 * 取消查询
 * @param queryId 查询ID
 */
export async function cancelQuery(queryId: string): Promise<void> {
  try {
    await api.delete(`/secure_query/${queryId}/cancel/`);
  } catch (error) {
    console.error('取消查询失败:', error);
    throw error;
  }
}

/**
 * 获取查询历史
 * @param limit 限制数量
 * @returns 查询历史列表
 */
export async function getQueryHistory(limit: number = 10): Promise<Query[]> {
  try {
    const response = await api.get<Query[]>(`/secure_query/history/`, {
      params: { limit },
    });
    return response;
  } catch (error) {
    console.error('获取查询历史失败:', error);
    throw error;
  }
}

/**
 * 获取路线规划
 * @param waypointIds 途经点ID数组
 * @param startLocation 起点位置
 * @returns 路线规划结果
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
    const response = await api.post('/secure_query/route/', {
      waypoint_ids: waypointIds,
      start_location: startLocation,
    });
    return response;
  } catch (error) {
    console.error('获取路线规划失败:', error);
    throw error;
  }
}

