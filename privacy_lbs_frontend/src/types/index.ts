/**
 * TypeScript Type Definitions
 * Define all interfaces and types used in the system
 */

/**
 * Spatial Object (POI)
 */
export interface SpatialObject {
  id: string;
  name: string;
  description?: string;
  location: {
    longitude: number;
    latitude: number;
  };
  category?: string;
  tags?: string[];
  attributes?: Record<string, any>;
}

/**
 * Query Parameters
 */
export interface Query {
  id?: string;
  text: string; // Query text
  location: {
    longitude: number;
    latitude: number;
  };
  alpha: number; // Text-distance weight (0-1)
  k: number; // Top-K results count
  radius?: number; // Query radius (optional)
  timestamp?: number; // Query timestamp
}

/**
 * Query Result
 */
export interface QueryResult {
  id: string;
  spatialObject: SpatialObject;
  score: number; // Overall score
  textScore?: number; // Text similarity score
  distanceScore?: number; // Distance score
  distance: number; // Distance (meters)
  encryptedScore?: string; // Encrypted score (from server)
}

/**
 * Safe Zone
 */
export interface SafeZone {
  id: string;
  name: string;
  center: {
    longitude: number;
    latitude: number;
  };
  radius: number; // Radius (meters)
  polygon?: [number, number][]; // Polygon boundary (optional)
}

/**
 * User Trajectory Point
 */
export interface TrajectoryPoint {
  longitude: number;
  latitude: number;
  timestamp: number;
  speed?: number;
  heading?: number;
}

/**
 * Route Planning Result
 */
export interface RoutePlan {
  id: string;
  waypoints: SpatialObject[];
  totalDistance: number; // Total distance (meters)
  totalTime: number; // Estimated total time (seconds)
  polyline: [number, number][]; // Route polyline
  steps?: RouteStep[];
}

/**
 * Route Step
 */
export interface RouteStep {
  instruction: string;
  distance: number;
  duration: number;
  polyline: [number, number][];
}

/**
 * Real-time Location Update
 */
export interface RealTimeLocation {
  longitude: number;
  latitude: number;
  timestamp: number;
  accuracy?: number;
}

/**
 * Query Status
 */
export enum QueryStatus {
  IDLE = 'idle',
  PENDING = 'pending',
  PROCESSING = 'processing',
  SUCCESS = 'success',
  ERROR = 'error',
}

/**
 * API Response Base Structure
 */
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

/**
 * Paginated Response
 */
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * WebSocket Message Types
 */
export interface WebSocketMessage {
  type: 'query_update' | 'result_update' | 'error' | 'status';
  payload: any;
  timestamp: number;
}

// ─────────────────────────────────────────────────────────────
// Additional Types (added in refactoring)
// ─────────────────────────────────────────────────────────────

/**
 * Point of Interest (POI)
 */
export interface POI {
  id: string;
  name: string;
  lng: number;
  lat: number;
  keywords: string[];
  category?: string;
}

/**
 * Query History Item
 * Written by recordHistory() in query.store.ts
 */
export interface QueryHistoryItem {
  /** Unique ID */
  id: string;
  /** Query timestamp */
  timestamp: Date;
  /** Keyword list (tokenized from query text) */
  keywords: string[];
  /** Query location [longitude, latitude] */
  location: [number, number];
  /** Query radius (meters) */
  radius: number;
  /** Text-distance weight (0-1) */
  alpha: number;
  /** End-to-end query latency (milliseconds) */
  latencyMs: number;
  /** Whether this query hit the safe zone cache */
  safeZoneHit: boolean;
  /** Number of results returned */
  resultCount: number;
}

/**
 * Paillier Homomorphic Encryption Configuration
 */
export interface EncryptionConfig {
  /** Encryption algorithm, currently fixed to Paillier */
  algorithm: 'Paillier';
  /** Key length (bits) */
  keySize: 512 | 1024 | 2048;
  /** Encryption time (milliseconds) */
  encryptionTimeMs: number;
  /** Key size (MB) */
  keySizeMB: number;
}

