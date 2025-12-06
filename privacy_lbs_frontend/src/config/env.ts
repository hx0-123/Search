/**
 * 环境变量配置
 * 统一管理所有环境变量
 */

export const env = {
  // Mapbox访问令牌
  mapboxToken: import.meta.env.VITE_MAPBOX_ACCESS_TOKEN || '',
  
  // 后端Django API基础地址
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api',
  
  // WebSocket服务器地址
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000/ws/query_updates/',
  
  // 是否为开发环境
  isDev: import.meta.env.DEV,
  
  // 是否为生产环境
  isProd: import.meta.env.PROD,
} as const

/**
 * 验证环境变量配置
 */
export function validateEnv(): { valid: boolean; errors: string[] } {
  const errors: string[] = []
  
  if (!env.mapboxToken || env.mapboxToken === 'pk.your_mapbox_token_here') {
    errors.push('Mapbox访问令牌未配置，请在.env.development中设置VITE_MAPBOX_ACCESS_TOKEN')
  }
  
  if (!env.apiBaseUrl) {
    errors.push('API基础地址未配置，请在.env.development中设置VITE_API_BASE_URL')
  }
  
  if (!env.wsUrl) {
    errors.push('WebSocket地址未配置，请在.env.development中设置VITE_WS_URL')
  }
  
  return {
    valid: errors.length === 0,
    errors,
  }
}

/**
 * 在开发环境下打印环境变量配置（不包含敏感信息）
 */
if (env.isDev) {
  const validation = validateEnv()
  if (!validation.valid) {
    console.warn('⚠️ 环境变量配置警告：')
    validation.errors.forEach(error => console.warn(`  - ${error}`))
  } else {
    console.log('✅ 环境变量配置正常')
    console.log(`  - API Base URL: ${env.apiBaseUrl}`)
    console.log(`  - WebSocket URL: ${env.wsUrl}`)
    console.log(`  - Mapbox Token: ${env.mapboxToken ? '已配置' : '未配置'}`)
  }
}





