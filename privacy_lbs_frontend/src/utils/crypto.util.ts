/**
 * Frontend encryption utility functions
 * Note: Only non-sensitive frontend operations (like hashing) are included here.
 * Actual encryption/decryption operations are done on the backend.
 */

/**
 * Calculate simple hash value for string (for non-sensitive use)
 * @param str Input string
 * @returns Hash value
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
 * Generate unique ID (for frontend temporary identification)
 * @param prefix Prefix
 * @returns Unique ID
 */
export function generateId(prefix: string = 'id'): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 9);
  return `${prefix}_${timestamp}_${random}`;
}

/**
 * Preprocess query text (remove whitespace, lowercase, etc.)
 * @param text Original text
 * @returns Processed text
 */
export function preprocessQueryText(text: string): string {
  return text.trim().toLowerCase();
}

/**
 * Validate query parameters
 * @param query Query object
 * @returns Whether valid
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
 * Base64 encode data (for non-sensitive data transmission)
 * @param data Data to encode
 * @returns Base64 encoded string
 */
export function encodeBase64(data: string): string {
  return btoa(encodeURIComponent(data));
}

/**
 * Decode Base64 encoded data
 * @param encoded Encoded string
 * @returns Decoded string
 */
export function decodeBase64(encoded: string): string {
  return decodeURIComponent(atob(encoded));
}

