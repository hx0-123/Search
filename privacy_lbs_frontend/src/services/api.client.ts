/**
 * Axios API客户端配置
 * 统一管理HTTP请求的配置和拦截器
 */

import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { env } from '@/config/env';
import { handleApiError, showError } from '@/utils/error-handler.util';
import type { ApiResponse } from '@/types';

/**
 * 创建Axios实例
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: env.apiBaseUrl,
  timeout: 30000, // 30秒超时
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * 请求拦截器
 */
apiClient.interceptors.request.use(
  (config) => {
    // 添加JWT Token（如果已实现用户认证）
    const token = localStorage.getItem('jwt_token') || localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // 开发环境下打印请求信息
    if (env.isDev) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
        params: config.params,
        data: config.data,
      });
    }
    
    return config;
  },
  (error: AxiosError) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

/**
 * 响应拦截器
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    // 开发环境下打印响应信息
    if (env.isDev) {
      console.log(`[API Response] ${response.config.url}`, response.data);
    }
    
    // 如果后端返回的数据结构是 { success, data, message }
    if (response.data && typeof response.data === 'object' && 'success' in response.data) {
      if (!response.data.success) {
        // 后端返回了错误
        const error = new Error(response.data.message || response.data.error || '请求失败');
        return Promise.reject(error);
      }
      // 返回data字段
      return response.data.data !== undefined ? response.data.data : response.data;
    }
    
    // 直接返回响应数据
    return response.data;
  },
  (error: AxiosError<ApiResponse>) => {
    // 使用统一的错误处理
    const errorInfo = handleApiError(error);
    
    // 显示用户友好的错误提示
    showError(errorInfo);
    
    return Promise.reject(error);
  }
);

/**
 * 导出配置好的API客户端
 */
export default apiClient;

/**
 * 导出常用的HTTP方法
 */
export const api = {
  get: <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    return apiClient.get(url, config);
  },
  
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    return apiClient.post(url, data, config);
  },
  
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    return apiClient.put(url, data, config);
  },
  
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    return apiClient.patch(url, data, config);
  },
  
  delete: <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    return apiClient.delete(url, config);
  },
};

