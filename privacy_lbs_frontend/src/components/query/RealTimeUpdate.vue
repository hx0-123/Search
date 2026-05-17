<!--
  Real-time Update Component
  Continuous query driver: periodically triggers update_location API with current coordinates
  Location source:
    - Real-time GPS: uses browser Geolocation API to get real coordinates
    - Manual input: user enters longitude/latitude and clicks "Apply"
  Safe Zone optimization:
    - Frontend calculates distance locally first, if within safe radius skip backend request and directly update display distance
    - Only when leaving the safe circle does it initiate a full ciphertext query
-->
<template>
  <el-card class="realtime-update-card">
    <template #header>
      <div class="card-header">
        <span>Real-time Update</span>
        <el-switch
          v-model="enabled"
          @change="handleToggle"
          :disabled="!queryStore.queryId"
        />
      </div>
    </template>

    <div v-if="!queryStore.queryId" class="no-query-hint">
      <el-text type="info">Please execute a query first</el-text>
    </div>

    <div v-else>
      <el-form label-width="140px">

        <!-- Location source -->
        <el-form-item label="Location Source">
          <el-radio-group v-model="locationSource" @change="handleLocationSourceChange">
            <el-radio label="realtime">Real-time GPS</el-radio>
            <el-radio label="manual">Manual Input</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- Manual input fields -->
        <template v-if="locationSource === 'manual'">
          <el-form-item label="Longitude">
            <el-input-number
              v-model="manualLocation.longitude"
              :precision="6"
              :step="0.000001"
              :min="-180"
              :max="180"
              style="width: 100%"
              placeholder="Enter longitude"
            />
          </el-form-item>
          <el-form-item label="Latitude">
            <el-input-number
              v-model="manualLocation.latitude"
              :precision="6"
              :step="0.000001"
              :min="-90"
              :max="90"
              style="width: 100%"
              placeholder="Enter latitude"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="small" @click="applyManualLocation">
              Apply Location
            </el-button>
            <el-button size="small" @click="useCurrentLocation" :disabled="!navigator.geolocation" style="margin-left:8px">
              Use Current Location
            </el-button>
          </el-form-item>
        </template>

        <!-- Update interval -->
        <el-form-item label="Update Interval">
          <el-input-number
            v-model="interval"
            :min="1000"
            :max="60000"
            :step="1000"
            :precision="0"
            @change="restartIfEnabled"
          />
          <el-text type="info" size="small" style="margin-left: 8px">ms</el-text>
        </el-form-item>

        <!-- Status -->
        <el-form-item label="Status">
          <el-tag :type="enabled ? 'success' : 'info'">
            {{ enabled ? 'Enabled' : 'Disabled' }}
          </el-tag>
        </el-form-item>

        <el-form-item label="Update Count">
          <el-text>{{ updateCount }}</el-text>
        </el-form-item>

        <el-form-item label="Last Update">
          <el-text type="info" size="small">{{ lastUpdateTime || '—' }}</el-text>
        </el-form-item>

        <!-- Safe Zone status -->
        <el-form-item label="Safe Zone Status">
          <div class="safe-zone-info">
            <el-tag :type="safeZoneStatus === 'hit' ? 'success' : safeZoneStatus === 'miss' ? 'warning' : 'info'" size="small">
              {{ safeZoneStatusText }}
            </el-tag>
            <el-text v-if="safeZoneRadius > 0" type="info" size="small" style="margin-left:8px">
              Radius {{ safeZoneRadius.toFixed(0) }}m · Distance to Center {{ distToCenter.toFixed(0) }}m
            </el-text>
          </div>
        </el-form-item>

        <!-- Performance timing -->
        <el-form-item label="Performance Test">
          <el-text type="info" size="small">
            {{ perfText || '—' }}
          </el-text>
        </el-form-item>

      </el-form>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted, watch } from 'vue';
import { ElMessage } from 'element-plus';
import dayjs from 'dayjs';
import { useQueryStore } from '@/stores/query.store';
import { useResultStore } from '@/stores/result.store';
import { useMapStore } from '@/stores/map.store';

const queryStore  = useQueryStore();
const resultStore = useResultStore();
const mapStore    = useMapStore();

const enabled        = ref(false);
const interval       = ref(5000);
const updateCount    = ref(0);
const lastUpdateTime = ref('');
const locationSource = ref<'realtime' | 'manual'>('realtime');
const manualLocation = ref({ longitude: 116.4074, latitude: 39.9042 });

// Safe Zone status
const safeZoneCenter = ref<{ longitude: number; latitude: number } | null>(null);
const safeZoneRadius = ref(0);   // Unit: meters
const distToCenter   = ref(0);   // Unit: meters
const safeZoneStatus = ref<'idle' | 'hit' | 'miss'>('idle');

// Performance timing
const perfText = ref('');

const safeZoneStatusText = computed(() => {
  if (safeZoneStatus.value === 'hit')  return 'Hit';
  if (safeZoneStatus.value === 'miss') return 'Miss';
  return 'Idle';
});

let timer: number | null = null;
let isUpdating = false;
const MIN_INTERVAL = 2000;
let _destroyed = false; // Whether component is unmounted
let _abortController: AbortController | null = null; // Abort controller for current request

// Auto stop when queryId disappears
watch(() => queryStore.queryId, (id) => { if (!id) stop(); });

// ── Haversine distance (meters) ──────────────────────────────────────
function haversineDistance(
  lon1: number, lat1: number,
  lon2: number, lat2: number
): number {
  const R = 6_371_000;
  const toRad = (d: number) => d * Math.PI / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// ── Core: Perform one location update ────────────────────────────────────
async function tick(location: { longitude: number; latitude: number }) {
  if (!queryStore.queryId || isUpdating || _destroyed) return;

  const t0 = performance.now();

  // ── Safe Zone local prediction ──────────────────────────────────────
  if (safeZoneCenter.value && safeZoneRadius.value > 0) {
    const dist = haversineDistance(
      safeZoneCenter.value.longitude, safeZoneCenter.value.latitude,
      location.longitude,             location.latitude
    );
    distToCenter.value = dist;

    if (dist <= safeZoneRadius.value) {
      // Inside safe zone: only update map marker, no request sent
      safeZoneStatus.value = 'hit';
      queryStore.setCurrentLocation(location);
      lastUpdateTime.value = dayjs().format('HH:mm:ss');
      const tEnd = performance.now();
      perfText.value = `[Safe Zone HIT] Frontend: ${(tEnd - t0).toFixed(1)}ms | Backend: Skipped`;
      console.log(`[Performance] Safe Zone HIT | Frontend: ${(tEnd - t0).toFixed(1)}ms | Distance to Center: ${dist.toFixed(1)}m / ${safeZoneRadius.value}m`);
      return;
    }
    // Outside safe zone, proceed with full query
    safeZoneStatus.value = 'miss';
  }

  isUpdating = true;
  const tEncStart = performance.now();

  // Cancel previous pending request
  if (_abortController) {
    _abortController.abort();
  }
  _abortController = new AbortController();
  const { signal } = _abortController;

  // Set timeout protection: each request waits max 8 seconds, prevents blocking main thread
  const timeoutPromise = new Promise<never>((_, reject) =>
    setTimeout(() => reject(new Error('Request timeout')), 8000)
  );

  try {
    if (_destroyed) return; // Check again to prevent component unmounted during wait

    // Update store → trigger map blue marker movement
    queryStore.setCurrentLocation(location);

    const tEncEnd = performance.now();

    const tBackendStart = performance.now();
    // Use Promise.race to ensure max wait of 8 seconds
    const results = await Promise.race([
      queryStore.update({
        longitude: location.longitude,
        latitude:  location.latitude,
        timestamp: Date.now(),
      }, signal),
      timeoutPromise,
    ]);
    const tBackendEnd = performance.now();

    if (_destroyed) return; // Check again after request completes

    // Update Safe Zone
    const storeSafeZone = queryStore.safeZone;
    if (storeSafeZone) {
      safeZoneCenter.value = storeSafeZone.center;
      safeZoneRadius.value = storeSafeZone.radius ?? 1000;
      distToCenter.value   = 0;
    } else if (!safeZoneCenter.value) {
      safeZoneCenter.value = { longitude: location.longitude, latitude: location.latitude };
      safeZoneRadius.value = 1000;
    }

    const tRenderStart = performance.now();
    if (results && (results as any[]).length > 0) {
      resultStore.updateResults(results as any[]);
    }
    const tRenderEnd = performance.now();

    updateCount.value++;
    lastUpdateTime.value = dayjs().format('HH:mm:ss');

    const encMs     = (tEncEnd     - tEncStart).toFixed(1);
    const backendMs = (tBackendEnd - tBackendStart).toFixed(1);
    const renderMs  = (tRenderEnd  - tRenderStart).toFixed(1);
    perfText.value  = `[Frontend] Encrypt: ${encMs}ms | Backend: ${backendMs}ms | Render: ${renderMs}ms`;
    console.log(`[Performance] Frontend Encrypt: ${encMs}ms | Backend Query: ${backendMs}ms | UI Render: ${renderMs}ms`);

  } catch (e: any) {
    if (_destroyed) return; // Ignore all errors after unmount
    const msg = e?.response?.data?.error || e?.message || 'Unknown error';
    if (msg !== 'Request Timeout') {
      ElMessage.error(`Update failed: ${msg}`);
    } else {
      console.warn('[RealTimeUpdate] tick timeout, skipping this update');
    }
    if (e?.response?.status === 400) stop();
  } finally {
    isUpdating = false;
  }
}

// ── GPS Mode: Fetch location once then trigger tick ────────────────────────
function fetchGPSAndTick() {
  if (!navigator.geolocation) {
    tick(queryStore.currentLocation);
    return;
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      tick({
        longitude: pos.coords.longitude,
        latitude:  pos.coords.latitude,
      });
    },
    () => {
      tick(queryStore.currentLocation);
    },
    { enableHighAccuracy: false, timeout: 5000, maximumAge: 10000 }
  );
}

// ── Start / Stop ──────────────────────────────────────────────
function start() {
  if (timer) clearInterval(timer);
  enabled.value = true;
  const effectiveInterval = Math.max(interval.value, MIN_INTERVAL);

  if (locationSource.value === 'realtime') {
    fetchGPSAndTick();
    timer = window.setInterval(fetchGPSAndTick, effectiveInterval);
  } else {
    tick(manualLocation.value);
    timer = window.setInterval(() => tick(manualLocation.value), effectiveInterval);
  }
}

function stop() {
  if (timer) { clearInterval(timer); timer = null; }
  enabled.value = false;
}

function restartIfEnabled() {
  if (enabled.value) { stop(); start(); }
}

function handleToggle(val: boolean) {
  queryStore.setRealTimeUpdate(val);
  val ? start() : stop();
}

function handleLocationSourceChange() {
  if (enabled.value) { stop(); start(); }
}

function applyManualLocation() {
  queryStore.setCurrentLocation({
    longitude: manualLocation.value.longitude,
    latitude:  manualLocation.value.latitude,
  });
  ElMessage.success(`Location updated: ${manualLocation.value.longitude.toFixed(5)}, ${manualLocation.value.latitude.toFixed(5)}`);
}

async function useCurrentLocation() {
  if (!navigator.geolocation) {
    ElMessage.warning('Geolocation not supported by browser');
    return;
  }
  try {
    const pos = await new Promise<GeolocationPosition>((resolve, reject) =>
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: false, timeout: 5000, maximumAge: 60000,
      })
    );
    manualLocation.value = {
      longitude: pos.coords.longitude,
      latitude:  pos.coords.latitude,
    };
    queryStore.setCurrentLocation(manualLocation.value);
    ElMessage.success('Location updated: current');
  } catch (e: any) {
    ElMessage.error(`Update failed: ${e?.message || 'Unknown error'}`);
  }
}

onUnmounted(() => {
  _destroyed = true;
  isUpdating = false;
  // Actively cancel all ongoing network requests, release browser connection slots
  if (_abortController) {
    _abortController.abort();
    _abortController = null;
  }
  stop();
});
</script>

<style scoped>
.realtime-update-card { flex-shrink: 0; }
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.no-query-hint {
  text-align: center;
  padding: 20px;
}
.safe-zone-info {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}
</style>
