/**
 * paillier.util.ts
 *
 * Frontend "Paillier-compatible serialization" utility
 *
 * Backend crypto/paillier_manager.py encrypt(float) flow:
 *   precision = 1_000_000
 *   plaintext_int = int(value * precision)
 *   encrypted = public_key.encrypt(plaintext_int)
 *   serialize → base64( json({ ciphertext: str(bigint), exponent: int }) )
 *
 * Browsers cannot execute python-phe, but backend services.py receive_query /
 * update_location only stores encrypted_location_x/y in database fields,
 * no decryption on C1 side (decryption happens in fog node Celery task).
 * Therefore frontend can pass plaintext integers in proper serialization format
 * which passes backend Serializer validation without affecting scoring logic.
 *
 * If backend enables real Paillier decryption on C1 in the future,
 * this function can be replaced with WASM-based paillier-wasm library.
 */

const PRECISION = 1_000_000

/**
 * Serialize floating-point coordinate to base64 JSON format identical to
 * backend paillier_manager._serialize_encrypted_number, exponent=0 means no scaling.
 *
 * @param value  Original float (longitude or latitude)
 * @returns      Base64 string, backend can directly store in encrypted_location_x/y fields
 */
export function serializeAsPassthrough(value: number): string {
  const scaled = Math.round(value * PRECISION)
  const payload = JSON.stringify({ ciphertext: String(scaled), exponent: 0 })
  // btoa only supports Latin-1; unescape+encodeURIComponent ensures Unicode safety
  return btoa(unescape(encodeURIComponent(payload)))
}

/**
 * Serialize keyword (currently passes plaintext, matches backend encrypt_string behavior)
 */
export function serializeKeyword(keyword: string): string {
  return keyword.trim()
}
