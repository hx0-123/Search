/**
 * 数据服务
 * 处理数据上传和其他数据相关服务
 * 注意：这个服务主要用于数据拥有者上传数据
 */

import api from './api.client';
import type { ApiResponse } from '@/types';

/**
 * 上传数据文件
 * @param file 数据文件（CSV、JSON等）
 * @param onProgress 上传进度回调
 * @returns 上传结果
 */
export async function uploadDataFile(
  file: File,
  onProgress?: (progress: number) => void
): Promise<{
  taskId: string;
  message: string;
}> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post<{
      taskId: string;
      message: string;
    }>('/data_owner/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(progress);
        }
      },
    });
    
    return response;
  } catch (error) {
    console.error('上传数据文件失败:', error);
    throw error;
  }
}

/**
 * 获取上传任务状态
 * @param taskId 任务ID
 * @returns 任务状态
 */
export async function getUploadTaskStatus(taskId: string): Promise<{
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  message?: string;
  result?: {
    totalRecords: number;
    encryptedRecords: number;
    indexBuilt: boolean;
  };
}> {
  try {
    const response = await api.get(`/data_owner/upload/${taskId}/status/`);
    return response;
  } catch (error) {
    console.error('获取上传任务状态失败:', error);
    throw error;
  }
}

/**
 * 获取数据统计信息
 * @returns 数据统计
 */
export async function getDataStatistics(): Promise<{
  totalObjects: number;
  totalCategories: number;
  lastUpdateTime: string;
}> {
  try {
    const response = await api.get('/data_owner/statistics/');
    return response;
  } catch (error) {
    console.error('获取数据统计失败:', error);
    throw error;
  }
}

/**
 * 验证数据文件格式
 * @param file 数据文件
 * @returns 验证结果
 */
export function validateDataFile(file: File): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];
  const maxSize = 100 * 1024 * 1024; // 100MB
  const allowedTypes = [
    'text/csv',
    'application/json',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  ];
  
  if (file.size > maxSize) {
    errors.push(`文件大小超过限制（最大${maxSize / 1024 / 1024}MB）`);
  }
  
  if (!allowedTypes.includes(file.type) && !file.name.endsWith('.csv') && !file.name.endsWith('.json')) {
    errors.push('不支持的文件格式，请上传CSV或JSON文件');
  }
  
  return {
    valid: errors.length === 0,
    errors,
  };
}

