/**
 * Error Handling Utility
 * Unified handling of various errors and provides user-friendly prompts
 */

import { ElMessage, ElNotification } from 'element-plus';
import type { AxiosError } from 'axios';

/**
 * Error Type Enum
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
 * Error Info Interface
 */
export interface ErrorInfo {
  type: ErrorType;
  message: string;
  code?: string | number;
  details?: any;
}

/**
 * Handle API errors
 */
export function handleApiError(error: any): ErrorInfo {
  if (error.response) {
    // Server returned error response
    const status = error.response.status;
    const data = error.response.data;
    
    let message = 'Request failed';
    
    switch (status) {
      case 400:
        message = data?.message || data?.error || 'Invalid request parameters';
        break;
      case 401:
        message = 'Unauthorized, please login again';
        break;
      case 403:
        message = 'No permission to access this resource';
        break;
      case 404:
        message = 'Requested resource not found';
        break;
      case 500:
        message = 'Internal server error, please try again later';
        break;
      case 502:
        message = 'Gateway error, please try again later';
        break;
      case 503:
        message = 'Service temporarily unavailable, please try again later';
        break;
      default:
        message = data?.message || data?.error || `Request failed (${status})`;
    }
    
    return {
      type: ErrorType.API,
      message,
      code: status,
      details: data,
    };
  } else if (error.request) {
    // Request sent but no response received
    return {
      type: ErrorType.NETWORK,
      message: 'Network connection failed, please check network settings',
      code: 'NETWORK_ERROR',
    };
  } else {
    // Request configuration error
    return {
      type: ErrorType.UNKNOWN,
      message: error.message || 'Unknown error',
    };
  }
}

/**
 * Handle map errors
 */
export function handleMapError(error: any): ErrorInfo {
  let message = 'Map loading failed';
  
  if (error.message) {
    if (error.message.includes('token')) {
      message = 'Mapbox access token invalid, please check configuration';
    } else if (error.message.includes('style')) {
      message = 'Map style loading failed';
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
 * Handle location acquisition errors
 */
export function handleLocationError(error: GeolocationPositionError): ErrorInfo {
  let message = 'Failed to get location';
  
  switch (error.code) {
    case error.PERMISSION_DENIED:
      message = 'Location permission denied, please allow location access in browser settings';
      break;
    case error.POSITION_UNAVAILABLE:
      message = 'Location information unavailable, please check GPS settings';
      break;
    case error.TIMEOUT:
      message = 'Location acquisition timeout, please try again';
      break;
    default:
      message = 'Failed to get location';
  }
  
  return {
    type: ErrorType.LOCATION,
    message,
    code: error.code,
  };
}

/**
 * Show error prompt
 */
export function showError(errorInfo: ErrorInfo, useNotification: boolean = false) {
  const { message, type } = errorInfo;
  
  if (useNotification) {
    ElNotification({
      title: 'Error',
      message,
      type: 'error',
      duration: 5000,
    });
  } else {
    ElMessage.error(message);
  }
  
  // Print detailed error info in development environment
  if (import.meta.env.DEV) {
    console.error(`[${type}]`, errorInfo);
  }
}

/**
 * Show success prompt
 */
export function showSuccess(message: string) {
  ElMessage.success(message);
}

/**
 * Show warning prompt
 */
export function showWarning(message: string) {
  ElMessage.warning(message);
}

/**
 * Show info prompt
 */
export function showInfo(message: string) {
  ElMessage.info(message);
}



