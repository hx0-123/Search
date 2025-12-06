/**
 * TypeScript类型定义
 * 定义系统中使用的所有接口和类型
 */

/**
 * 空间对象（POI）
 */
export interface SpatialObject {
  id: string;
  name: string;
  description?: string;
  location: {
    longitude: number;
    latitude: number;
  };
  category?: string;
  tags?: string[];
  attributes?: Record<string, any>;
}

/**
 * 查询参数
 */
export interface Query {
  id?: string;
  text: string; // 查询文本
  location: {
    longitude: number;
    latitude: number;
  };
  alpha: number; // 文本-距离权重 (0-1)
  k: number; // Top-K结果数量
  radius?: number; // 查询半径（可选）
  timestamp?: number; // 查询时间戳
}

/**
 * 查询结果
 */
export interface QueryResult {
  id: string;
  spatialObject: SpatialObject;
  score: number; // 综合评分
  textScore?: number; // 文本相似度评分
  distanceScore?: number; // 距离评分
  distance: number; // 距离（米）
  encryptedScore?: string; // 加密评分（从服务器返回）
}

/**
 * 安全区域
 */
export interface SafeZone {
  id: string;
  name: string;
  center: {
    longitude: number;
    latitude: number;
  };
  radius: number; // 半径（米）
  polygon?: [number, number][]; // 多边形边界（可选）
}

/**
 * 用户轨迹点
 */
export interface TrajectoryPoint {
  longitude: number;
  latitude: number;
  timestamp: number;
  speed?: number;
  heading?: number;
}

/**
 * 路线规划结果
 */
export interface RoutePlan {
  id: string;
  waypoints: SpatialObject[];
  totalDistance: number; // 总距离（米）
  totalTime: number; // 预计总时间（秒）
  polyline: [number, number][]; // 路线折线
  steps?: RouteStep[];
}

/**
 * 路线步骤
 */
export interface RouteStep {
  instruction: string;
  distance: number;
  duration: number;
  polyline: [number, number][];
}

/**
 * 实时位置更新
 */
export interface RealTimeLocation {
  longitude: number;
  latitude: number;
  timestamp: number;
  accuracy?: number;
}

/**
 * 查询状态
 */
export enum QueryStatus {
  IDLE = 'idle',
  PENDING = 'pending',
  PROCESSING = 'processing',
  SUCCESS = 'success',
  ERROR = 'error',
}

/**
 * API响应基础结构
 */
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * WebSocket消息类型
 */
export interface WebSocketMessage {
  type: 'query_update' | 'result_update' | 'error' | 'status';
  payload: any;
  timestamp: number;
}

