/**
 * 前端加密工具函数
 * 注意：这里只包含非敏感的前端加密操作（如哈希），
 * 真正的加密解密操作在后端完成
 */

/**
 * 计算字符串的简单哈希值（用于非敏感用途）
 * @param str 输入字符串
 * @returns 哈希值
 */
export function simpleHash(str: string): string {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return Math.abs(hash).toString(16);
}

/**
 * 生成唯一ID（用于前端临时标识）
 * @param prefix 前缀
 * @returns 唯一ID
 */
export function generateId(prefix: string = 'id'): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 9);
  return `${prefix}_${timestamp}_${random}`;
}

/**
 * 对查询文本进行预处理（去除空格、转小写等）
 * @param text 原始文本
 * @returns 处理后的文本
 */
export function preprocessQueryText(text: string): string {
  return text.trim().toLowerCase();
}

/**
 * 验证查询参数是否有效
 * @param query 查询对象
 * @returns 是否有效
 */
export function validateQuery(query: {
  text?: string;
  location?: { longitude: number; latitude: number };
  alpha?: number;
  k?: number;
}): boolean {
  if (!query.text || query.text.trim().length === 0) {
    return false;
  }
  
  if (!query.location || 
      typeof query.location.longitude !== 'number' ||
      typeof query.location.latitude !== 'number') {
    return false;
  }
  
  if (query.alpha !== undefined && (query.alpha < 0 || query.alpha > 1)) {
    return false;
  }
  
  if (query.k !== undefined && (query.k < 1 || query.k > 100)) {
    return false;
  }
  
  return true;
}

/**
 * 对数据进行Base64编码（用于非敏感数据传输）
 * @param data 要编码的数据
 * @returns Base64编码字符串
 */
export function encodeBase64(data: string): string {
  return btoa(encodeURIComponent(data));
}

/**
 * 对Base64编码的数据进行解码
 * @param encoded 编码的字符串
 * @returns 解码后的字符串
 */
export function decodeBase64(encoded: string): string {
  return decodeURIComponent(atob(encoded));
}

