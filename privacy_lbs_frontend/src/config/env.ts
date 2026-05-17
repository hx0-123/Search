/**
 * Environment Variable Configuration
 * Unified management of all environment variables
 */

export const env = {
  // Mapbox access token
  mapboxToken: import.meta.env.VITE_MAPBOX_ACCESS_TOKEN || '',
  
  // Backend Django API base URL
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api',
  
  // WebSocket server address
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000/ws/query_updates/',
  
  // Whether it's development environment
  isDev: import.meta.env.DEV,
  
  // Whether it's production environment
  isProd: import.meta.env.PROD,
} as const

/**
 * Validate environment variable configuration
 */
export function validateEnv(): { valid: boolean; errors: string[] } {
  const errors: string[] = []
  
  if (!env.mapboxToken || env.mapboxToken === 'pk.your_mapbox_token_here') {
    errors.push('Mapbox access token not configured, please set VITE_MAPBOX_ACCESS_TOKEN in .env.development')
  }
  
  if (!env.apiBaseUrl) {
    errors.push('API base URL not configured, please set VITE_API_BASE_URL in .env.development')
  }
  
  if (!env.wsUrl) {
    errors.push('WebSocket URL not configured, please set VITE_WS_URL in .env.development')
  }
  
  return {
    valid: errors.length === 0,
    errors,
  }
}

/**
 * Print environment variable configuration in development environment (excluding sensitive information)
 * Defer validation significantly to avoid blocking initial render
 */
if (env.isDev) {
  // Use requestIdleCallback or significant delay to avoid blocking initialization
  if ('requestIdleCallback' in window) {
    (window as any).requestIdleCallback(() => {
      const validation = validateEnv()
      if (!validation.valid) {
        console.warn('⚠️ Environment variable configuration warning:')
        validation.errors.forEach(error => console.warn(`  - ${error}`))
      } else {
        console.log('✅ Environment variable configuration normal')
        console.log(`  - API Base URL: ${env.apiBaseUrl}`)
        console.log(`  - WebSocket URL: ${env.wsUrl}`)
        console.log(`  - Mapbox Token: ${env.mapboxToken ? 'Configured' : 'Not configured'}`)
      }
    }, { timeout: 2000 });
  } else {
    setTimeout(() => {
      const validation = validateEnv()
      if (!validation.valid) {
        console.warn('⚠️ Environment variable configuration warning:')
        validation.errors.forEach(error => console.warn(`  - ${error}`))
      } else {
        console.log('✅ Environment variable configuration normal')
        console.log(`  - API Base URL: ${env.apiBaseUrl}`)
        console.log(`  - WebSocket URL: ${env.wsUrl}`)
        console.log(`  - Mapbox Token: ${env.mapboxToken ? 'Configured' : 'Not configured'}`)
      }
    }, 500); // Increased delay
  }
}





