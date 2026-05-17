/**
 * Config Service
 * Backend Paillier key management API
 */
import { api } from './api.client'

// ── Type Definitions ────────────────────────────────────────────
export interface KeyPairInfo {
  id: number
  key_size: 512 | 1024 | 2048
  public_key_digest: string   // First 16 hex fingerprint
  gen_time_ms: number
  is_active: boolean
  created_at: string
}

export interface KeyPairStatusResponse {
  exists: boolean
  keypair: KeyPairInfo | null
}

export interface KeyGenResponse {
  message: string
  public_key: string          // Base64 serialized public key, stored in localStorage
  private_key: string         // Base64 serialized private key, returned once at generation, kept in memory
  keypair: KeyPairInfo
}

/**
 * Get current active key pair status
 * GET /api/data/keypair/
 */
export async function getKeyPairStatus(): Promise<KeyPairStatusResponse> {
  const res = await api.get<KeyPairStatusResponse>('/data/keypair/')
  return res as unknown as KeyPairStatusResponse
}

/**
 * Generate new Paillier key pair on server
 * POST /api/data/keygen/
 */
export async function generateKeyPair(keySize: 512 | 1024 | 2048 = 1024): Promise<KeyGenResponse> {
  const res = await api.post<KeyGenResponse>('/data/keygen/', { key_size: keySize })
  const data = res as unknown as KeyGenResponse
  // Persist public key to localStorage for upload flow
  if (data.public_key) {
    localStorage.setItem('sktaq_public_key', data.public_key)
  }
  return data
}

