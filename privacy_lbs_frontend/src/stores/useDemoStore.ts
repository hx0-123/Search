/**
 * useDemoStore.ts
 * Cloud-Fog Collaborative Demo Global State
 * - isKeyGenerated    : Whether DO has generated Paillier key pair
 * - userApplyStatus   : End user's public key application status ('none' | 'pending' | 'approved')
 * - fogLevel          : Fog node quadtree grid division level (1=4 grids | 2=16 grids | 3=64 grids)
 * - systemLogs        : Global architecture logs (written during query execution, read by Dashboard in real-time)
 *
 * Security Model Description:
 *   - Private Key (SK) is only held by DO and Cloud C2, never touched by frontend/mobile
 *   - Regular users must first apply for public key (PK) from DO, and can only initiate encrypted queries after DO approval
 */
import { defineStore } from 'pinia';
import { ref } from 'vue';

export type UserApplyStatus = 'none' | 'pending' | 'approved';
export type LogNode   = 'User' | 'Cloud C1' | 'Cloud C2' | 'Fog Array';
export type LogStatus = 'pending' | 'success' | 'error';

export interface SystemLog {
  id: string;
  timestamp: Date;
  node: LogNode;
  action: string;
  status: LogStatus;
}

export const useDemoAppStore = defineStore('demoApp', () => {
  /** Whether DO has generated Paillier global key pair */
  const isKeyGenerated = ref<boolean>(false);

  /**
   * End user's public key application status
   * 'none'     → Not applied yet
   * 'pending'  → Applied, waiting for DO review
   * 'approved' → Approved by DO, public key issued, can initiate encrypted queries
   */
  const userApplyStatus = ref<UserApplyStatus>('none');

  /**
   * Fog node quadtree grid division level
   * 1 → 4  grids (Lv.1)
   * 2 → 16 grids (Lv.2)
   * 3 → 64 grids (Lv.3)
   */
  const fogLevel = ref<number>(2);

  /**
   * Global architecture logs
   * - Written by query terminal (DemoView) during query execution
   * - Read and rendered in real-time by node monitor (DashboardView)
   * - Maximum 50 entries, oldest automatically discarded when exceeded
   */
  const systemLogs = ref<SystemLog[]>([]);

  // -- State Operations ----------------------------------------

  /** Mark key generation complete (called by ConfigView after successful key generation) */
  function markKeyGenerated() {
    isKeyGenerated.value = true;
  }

  /** End user initiates public key application */
  function applyForKey() {
    if (userApplyStatus.value === 'none') {
      userApplyStatus.value = 'pending';
    }
  }

  /**
   * DO reviews public key application
   * @param approved - true to approve and issue public key; false to reject
   */
  function reviewKeyRequest(approved: boolean) {
    if (userApplyStatus.value === 'pending') {
      userApplyStatus.value = approved ? 'approved' : 'none';
    }
  }

  /** Set fog node level */
  function setFogLevel(val: number) {
    if (val >= 1 && val <= 3) fogLevel.value = val;
  }

  /** Reset end user application status (used when DO revokes authorization) */
  function revokeAccess() {
    userApplyStatus.value = 'none';
  }

  /**
   * Append an architecture log to global log queue
   * Automatically removes oldest entry when exceeding 50 entries
   */
  function addSystemLog(entry: Omit<SystemLog, 'id' | 'timestamp'>) {
    const log: SystemLog = {
      id: `log-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      timestamp: new Date(),
      ...entry,
    };
    systemLogs.value.unshift(log); // New logs inserted at head (reverse order)
    if (systemLogs.value.length > 50) {
      systemLogs.value.pop();
    }
  }

  /** Clear all logs */
  function clearSystemLogs() {
    systemLogs.value = [];
  }

  return {
    isKeyGenerated,
    userApplyStatus,
    fogLevel,
    systemLogs,
    markKeyGenerated,
    applyForKey,
    reviewKeyRequest,
    setFogLevel,
    revokeAccess,
    addSystemLog,
    clearSystemLogs,
  };
});
