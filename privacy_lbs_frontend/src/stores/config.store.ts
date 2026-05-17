/**
 * System Configuration Store
 * Manages encryption config, SafeZone settings, weight strategies, and persists to localStorage
 * generateKeyPair is connected to backend POST /api/data/keygen/
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { generateKeyPair as apiGenerateKeyPair, getKeyPairStatus } from '@/services/config.service'
import type { KeyPairInfo } from '@/services/config.service'

const STORAGE_KEY = 'sktaq_config'

export const useConfigStore = defineStore('config', () => {
  // ── Encryption Config ──────────────────────────────────────────
  const keySize = ref<512 | 1024 | 2048>(1024)
  const keysGenerated = ref(false)
  const keyGenTimeMs = ref(0)
  const keyDigest = ref('')          // Public key fingerprint (first 16 hex chars)
  const activeKeypair = ref<KeyPairInfo | null>(null)
  // Private key only kept in memory, not persisted to localStorage, regenerate after page refresh
  const privateKeyRaw = ref<string>('')

  // ── Safe Zone Config ──────────────────────────────────────────
  const safeZoneRadius = ref(1000)
  const updateInterval = ref(5000)
  const simulateMovement = ref(false)

  // ── Weight Strategy ───────────────────────────────────────────
  const alpha = ref(0.6)

  // ── Estimate Encryption Time ──────────────────────────────────
  function estimateEncryptionMs(dataCount = 100): number {
    const base: Record<number, number> = { 512: 8, 1024: 35, 2048: 180 }
    return Math.round((base[keySize.value] ?? 35) * Math.log2(dataCount + 1))
  }

  // ── Generate Key Pair from Backend ────────────────────────────
  async function generateKeyPair(): Promise<void> {
    keysGenerated.value = false
    privateKeyRaw.value = ''
    const start = Date.now()
    const data = await apiGenerateKeyPair(keySize.value)
    keyGenTimeMs.value = data.keypair.gen_time_ms || (Date.now() - start)
    keysGenerated.value = true
    keyDigest.value = data.keypair.public_key_digest
    activeKeypair.value = data.keypair
    // Private key only kept in memory, not written to localStorage
    if (data.private_key) {
      privateKeyRaw.value = data.private_key
    }
    // Public key already stored in localStorage('sktaq_public_key') by config.service
  }

  // ── Download Private Key as JSON File ──────────────────────────
  function downloadPrivateKey(): void {
    if (!privateKeyRaw.value) {
      throw new Error('Private key does not exist, please generate key pair first')
    }
    const payload = {
      algorithm: 'Paillier',
      key_size: keySize.value,
      public_key_digest: keyDigest.value,
      private_key: privateKeyRaw.value,
      generated_at: new Date().toISOString(),
      warning: 'Please keep this file secure. This system does not store private keys in the cloud. Only authorized users with this file can decrypt query results.',
    }
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `private_key_${keyDigest.value?.slice(0, 8) ?? 'sktaq'}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // ── Sync Key Status from Backend (Called on Page Init) ────────
  async function syncKeyStatus(): Promise<void> {
    try {
      const res = await getKeyPairStatus()
      if (res.exists && res.keypair) {
        keysGenerated.value = true
        keyDigest.value = res.keypair.public_key_digest
        keySize.value = res.keypair.key_size
        keyGenTimeMs.value = res.keypair.gen_time_ms
        activeKeypair.value = res.keypair
      } else {
        keysGenerated.value = false
        keyDigest.value = ''
        activeKeypair.value = null
      }
    } catch {
      // Silently fail if network unavailable, keep local state
    }
  }

  // ── Persistence ────────────────────────────────────────────────
  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      keySize: keySize.value,
      safeZoneRadius: safeZoneRadius.value,
      updateInterval: updateInterval.value,
      alpha: alpha.value,
    }))
  }

  function load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (!raw) return
      const cfg = JSON.parse(raw)
      if ([512, 1024, 2048].includes(cfg.keySize)) keySize.value = cfg.keySize
      if (cfg.safeZoneRadius >= 500 && cfg.safeZoneRadius <= 2000) safeZoneRadius.value = cfg.safeZoneRadius
      if (cfg.updateInterval >= 1000 && cfg.updateInterval <= 10000) updateInterval.value = cfg.updateInterval
      if (cfg.alpha >= 0 && cfg.alpha <= 1) alpha.value = cfg.alpha
    } catch { /* ignore */ }
  }

  function restoreDefaults() {
    keySize.value = 1024
    safeZoneRadius.value = 1000
    updateInterval.value = 5000
    alpha.value = 0.6
    keysGenerated.value = false
    keyGenTimeMs.value = 0
    keyDigest.value = ''
    activeKeypair.value = null
    simulateMovement.value = false
  }

  load()

  return {
    keySize, keysGenerated, keyGenTimeMs, keyDigest, activeKeypair,
    privateKeyRaw,
    safeZoneRadius, updateInterval, simulateMovement, alpha,
    estimateEncryptionMs, generateKeyPair, downloadPrivateKey, syncKeyStatus,
    save, load, restoreDefaults,
  }
})
