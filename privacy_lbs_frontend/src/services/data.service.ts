/**
 * Data Service
 * Backend data upload (CSV adapter) and statistics API
 */
import { api } from './api.client'

// ── Type Definitions ────────────────────────────────────────────
export interface StatisticsResponse {
  total_objects: number
  data_owner_count: number
  last_upload_time: string | null
  index: {
    build_status: 'not_started' | 'building' | 'completed' | 'failed'
    ktree_depth: number
    ktree_node_count: number
    ktree_leaf_count: number
    assettree_size: number
    build_completed_at: string | null
    spatial_domain: {
      x_min: number
      x_max: number
      y_min: number
      y_max: number
    }
  } | null
  keypair: {
    key_size: number
    public_key_digest: string
    created_at: string
    gen_time_ms: number
  } | null
}

export interface UploadResult {
  message: string
  owner_id: string
  objects_count: number
  index_built: boolean
  parsed_rows: number
  skipped_rows: number
  parse_warnings?: string[]
  index_metadata?: {
    ktree_depth: number
    ktree_node_count: number
    ktree_leaf_count: number
    assettree_size: number
  }
}

/**
 * CSV file upload (calls adapter endpoint)
 * POST /api/data_owner/upload/
 *
 * @param file       .csv file
 * @param onProgress Upload progress callback 0-100
 * @param ownerId    Data owner ID (default: default_owner)
 */
export async function uploadCSV(
  file: File,
  onProgress?: (pct: number) => void,
  ownerId = 'default_owner',
): Promise<UploadResult> {
  // Backend automatically detects active KeyPair, no need to attach public key
  const formData = new FormData()
  formData.append('file', file)
  formData.append('owner_id', ownerId)

  const res = await api.post<UploadResult>('/data_owner/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000, // 10 minutes: Paillier encryption of large datasets takes time
    onUploadProgress: (evt) => {
      if (evt.total && onProgress) {
        onProgress(Math.round((evt.loaded / evt.total) * 100))
      }
    },
  })
  return res as unknown as UploadResult
}

/**
 * Get data statistics
 * GET /api/data/statistics/
 */
export async function getDataStatistics(): Promise<StatisticsResponse> {
  const res = await api.get<StatisticsResponse>('/data/statistics/')
  return res as unknown as StatisticsResponse
}

/**
 * Validate CSV file format (frontend only)
 */
export function validateDataFile(file: File): { valid: boolean; errors: string[] } {
  const errors: string[] = []
  const maxSize = 100 * 1024 * 1024 // 100 MB
  if (file.size > maxSize) errors.push(`File size exceeds limit (max ${maxSize / 1024 / 1024} MB)`)
  if (!file.name.toLowerCase().endsWith('.csv')) errors.push('Only .csv format is supported')
  return { valid: errors.length === 0, errors }
}
