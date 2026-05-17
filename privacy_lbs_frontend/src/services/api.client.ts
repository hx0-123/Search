/**
 * Axios API Client Configuration
 * Unified management of HTTP request configuration and interceptors
 */

import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { env } from '@/config/env';
import { handleApiError, showError } from '@/utils/error-handler.util';
import type { ApiResponse } from '@/types';

/**
 * Create Axios instance
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: env.apiBaseUrl,
  timeout: 600000, // 10 minutes timeout (Paillier encryption of large datasets takes time)
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor
 */
apiClient.interceptors.request.use(
  (config) => {
    // Add JWT Token (if user authentication is implemented)
    const token = localStorage.getItem('jwt_token') || localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Print request info in development environment (defer to avoid blocking)
    if (env.isDev) {
      setTimeout(() => {
        console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
          params: config.params,
          data: config.data,
        });
      }, 0);
    }
    
    return config;
  },
  (error: AxiosError) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

/**
 * Response interceptor
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    // Print response info in development environment (defer to avoid blocking)
    if (env.isDev) {
      setTimeout(() => {
        console.log(`[API Response] ${response.config.url}`, response.data);
      }, 0);
    }
    
    // If backend returns data structure { success, data, message }
    if (response.data && typeof response.data === 'object' && 'success' in response.data) {
      if (!response.data.success) {
        // Backend returned error
        const error = new Error(response.data.message || response.data.error || 'Request failed');
        return Promise.reject(error);
      }
      // Return data field
      return response.data.data !== undefined ? response.data.data : response.data;
    }
    
    // Directly return response data
    return response.data;
  },
  (error: AxiosError<ApiResponse>) => {
    // Use unified error handling
    const errorInfo = handleApiError(error);
    
    // Show user-friendly error prompt
    showError(errorInfo);
    
    return Promise.reject(error);
  }
);

/**
 * Export configured API client
 */
export default apiClient;

/**
 * Export common HTTP methods
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

