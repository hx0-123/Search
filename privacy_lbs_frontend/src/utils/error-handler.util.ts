/**
 * 错误处理工具
 * 统一处理各种错误并提供友好的用户提示
 */

import { ElMessage, ElNotification } from 'element-plus';
import type { AxiosError } from 'axios';

/**
 * 错误类型枚举
 */
export enum ErrorType {
  NETWORK = 'network',
  API = 'api',
  MAP = 'map',
  LOCATION = 'location',
  VALIDATION = 'validation',
  UNKNOWN = 'unknown',
}

/**
 * 错误信息接口
 */
export interface ErrorInfo {
  type: ErrorType;
  message: string;
  code?: string | number;
  details?: any;
}

/**
 * 处理API错误
 */
export function handleApiError(error: any): ErrorInfo {
  if (error.response) {
    // 服务器返回了错误响应
    const status = error.response.status;
    const data = error.response.data;
    
    let message = '请求失败';
    
    switch (status) {
      case 400:
        message = data?.message || data?.error || '请求参数错误';
        break;
      case 401:
        message = '未授权，请重新登录';
        break;
      case 403:
        message = '无权限访问此资源';
        break;
      case 404:
        message = '请求的资源不存在';
        break;
      case 500:
        message = '服务器内部错误，请稍后重试';
        break;
      case 502:
        message = '网关错误，请稍后重试';
        break;
      case 503:
        message = '服务暂时不可用，请稍后重试';
        break;
      default:
        message = data?.message || data?.error || `请求失败 (${status})`;
    }
    
    return {
      type: ErrorType.API,
      message,
      code: status,
      details: data,
    };
  } else if (error.request) {
    // 请求已发出但没有收到响应
    return {
      type: ErrorType.NETWORK,
      message: '网络连接失败，请检查网络设置',
      code: 'NETWORK_ERROR',
    };
  } else {
    // 请求配置出错
    return {
      type: ErrorType.UNKNOWN,
      message: error.message || '未知错误',
    };
  }
}

/**
 * 处理地图错误
 */
export function handleMapError(error: any): ErrorInfo {
  let message = '地图加载失败';
  
  if (error.message) {
    if (error.message.includes('token')) {
      message = 'Mapbox访问令牌无效，请检查配置';
    } else if (error.message.includes('style')) {
      message = '地图样式加载失败';
    } else {
      message = error.message;
    }
  }
  
  return {
    type: ErrorType.MAP,
    message,
    details: error,
  };
}

/**
 * 处理位置获取错误
 */
export function handleLocationError(error: GeolocationPositionError): ErrorInfo {
  let message = '获取位置失败';
  
  switch (error.code) {
    case error.PERMISSION_DENIED:
      message = '位置权限被拒绝，请在浏览器设置中允许位置访问';
      break;
    case error.POSITION_UNAVAILABLE:
      message = '位置信息不可用，请检查GPS设置';
      break;
    case error.TIMEOUT:
      message = '获取位置超时，请重试';
      break;
    default:
      message = '获取位置失败';
  }
  
  return {
    type: ErrorType.LOCATION,
    message,
    code: error.code,
  };
}

/**
 * 显示错误提示
 */
export function showError(errorInfo: ErrorInfo, useNotification: boolean = false) {
  const { message, type } = errorInfo;
  
  if (useNotification) {
    ElNotification({
      title: '错误',
      message,
      type: 'error',
      duration: 5000,
    });
  } else {
    ElMessage.error(message);
  }
  
  // 开发环境下打印详细错误信息
  if (import.meta.env.DEV) {
    console.error(`[${type}]`, errorInfo);
  }
}

/**
 * 显示成功提示
 */
export function showSuccess(message: string) {
  ElMessage.success(message);
}

/**
 * 显示警告提示
 */
export function showWarning(message: string) {
  ElMessage.warning(message);
}

/**
 * 显示信息提示
 */
export function showInfo(message: string) {
  ElMessage.info(message);
}



