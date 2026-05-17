<template>
  <div class="demo-wrapper">
    <!-- Left collapsible query panel -->
    <div class="query-panel" :class="{ collapsed: isPanelCollapsed }">
      <div class="panel-header">
        <span class="panel-title">Query Parameters</span>
        <el-button
          :icon="isPanelCollapsed ? Expand : Fold"
          circle
          text
          size="small"
          @click="isPanelCollapsed = !isPanelCollapsed"
        />
      </div>

      <div v-if="!isPanelCollapsed" class="panel-content">

        <!-- ══════════════════════════════════════════════
             Public key application mask (covers entire panel-content)
             Displayed when status is 'none' or 'pending'
        ══════════════════════════════════════════════ -->
        <template v-if="demoApp.userApplyStatus !== 'approved'">
          <div class="apply-mask">
            <!-- Security badge -->
            <div class="apply-badge">
              <span class="apply-badge-dot"></span>
              Paillier Homomorphic Encryption System
            </div>

            <div class="apply-lock-icon">
              <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="12" y="28" width="40" height="28" rx="6" fill="rgba(56,189,248,0.12)" stroke="#38bdf8" stroke-width="2"/>
                <path d="M20 28V20a12 12 0 0 1 24 0v8" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round"/>
                <circle cx="32" cy="42" r="4" fill="#38bdf8"/>
                <line x1="32" y1="46" x2="32" y2="50" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round"/>
              </svg>
            </div>

            <div class="apply-title">No Encryption Query Permission</div>
            <div class="apply-desc">
              According to SKTAQ security protocol, end users must first apply for Paillier query public key (PK) from<br/>
              <strong>Data Owner (DO)</strong>,<br/>
              before initiating homomorphic encrypted queries.
            </div>

            <!-- 'none' status: show apply button -->
            <button
              v-if="demoApp.userApplyStatus === 'none'"
              class="apply-btn"
              @click="handleApplyKey"
            >
              <span class="apply-btn-icon">⚡</span>
              Apply for Paillier Query Public Key
            </button>

            <!-- 'pending' status: show waiting message -->
            <div v-else-if="demoApp.userApplyStatus === 'pending'" class="apply-pending">
              <span class="pending-spinner"></span>
              <span>Waiting for Data Owner (DO) approval...</span>
            </div>

            <!-- Status progress steps -->
            <div class="apply-steps">
              <div class="apply-step" :class="{ done: true }">
                <span class="step-dot step-dot-done"></span>
                <span>Client initiates request</span>
              </div>
              <div class="apply-step-line" :class="{ active: demoApp.userApplyStatus === 'pending' || demoApp.userApplyStatus === 'approved' }"></div>
              <div class="apply-step" :class="{ active: demoApp.userApplyStatus === 'pending' }">
                <span class="step-dot" :class="demoApp.userApplyStatus === 'pending' ? 'step-dot-active' : 'step-dot-idle'"></span>
                <span>DO Approval in Progress</span>
              </div>
              <div class="apply-step-line"></div>
              <div class="apply-step">
                <span class="step-dot step-dot-idle"></span>
                <span>Public Key Distribution</span>
              </div>
            </div>
          </div>
        </template>

        <!-- ══════════════════════════════════════════════
             Authorized status: show secure channel notice + normal query form
        ══════════════════════════════════════════════ -->
        <template v-else>
          <!-- Secure channel established banner -->
          <div class="secure-channel-banner">
            <div class="scb-left">
              <span class="scb-icon">🔓</span>
              <div class="scb-text">
                <div class="scb-title">Secure Channel Established</div>
                <div class="scb-desc">Public key (PK) loaded, coordinates and keywords will be automatically encrypted locally using Paillier homomorphic encryption</div>
              </div>
            </div>
            <div class="scb-badge">ENCRYPTED</div>
          </div>

          <QueryForm />

          <!-- Execute query button -->
          <div class="query-btn-wrap">
            <el-button type="primary" style="width: 100%" @click="handleQuery">
              <el-icon style="margin-right: 6px"><Search /></el-icon>
              Execute Encrypted Query
            </el-button>
          </div>

          <QueryProgressPanel />
          <RealTimeUpdate />
          <ResultList />
        </template>

      </div>
    </div>

    <!-- Right map area -->
    <div class="map-wrapper">
      <SecureMap />
      <QueryPointLayer v-if="mapStore.isMapLoaded" />
      <ResultMarkerLayer v-if="mapStore.isMapLoaded" />
      <SafeZoneLayer v-if="mapStore.isMapLoaded" />
      <RouteDetails />
      <!-- Cloud-fog collaborative terminal log -->
      <CloudFogTerminalLog ref="terminalLog" :query-fn="realQueryFn" @done="onQueryDone" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { Expand, Fold, Search } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import SecureMap from '@/components/map/SecureMap.vue';
import QueryPointLayer from '@/components/map/QueryPointLayer.vue';
import ResultMarkerLayer from '@/components/map/ResultMarkerLayer.vue';
import SafeZoneLayer from '@/components/map/SafeZoneLayer.vue';
import QueryForm from '@/components/query/QueryForm.vue';
import QueryProgressPanel from '@/components/query/QueryProgressPanel.vue';
import RealTimeUpdate from '@/components/query/RealTimeUpdate.vue';
import ResultList from '@/components/results/ResultList.vue';
import RouteDetails from '@/components/results/RouteDetails.vue';
import CloudFogTerminalLog from '@/components/query/CloudFogTerminalLog.vue';
import { useMapStore } from '@/stores/map.store';
import { useQueryStore } from '@/stores/query.store';
import { useResultStore } from '@/stores/result.store';
import { useDemoAppStore } from '@/stores/useDemoStore';

const mapStore    = useMapStore();
const queryStore  = useQueryStore();
const resultStore = useResultStore();
const demoApp     = useDemoAppStore();
const isPanelCollapsed = ref(false);
const terminalLog = ref<InstanceType<typeof CloudFogTerminalLog> | null>(null);

/** End user initiates public key application */
function handleApplyKey() {
  demoApp.applyForKey();
  ElMessage({
    message: 'Public key application submitted, please wait for Data Owner (DO) approval',
    type: 'info',
    duration: 3000,
  });
}

/** Real query factory function, passed to CloudFogTerminalLog */
function realQueryFn(): Promise<any> {
  if (!queryStore.isQueryValid) {
    return Promise.reject(new Error('Please fill in complete query information'));
  }
  return queryStore.submit();
}

/** Render real backend data after log ends (already decrypted by C2 in backend, frontend renders plaintext directly) */
function onQueryDone(results: any) {
  if (results) {
    resultStore.setResults(results);
    ElMessage.success('Query completed, plaintext results safely returned');
  }
}

/** Push query architecture logs to global log queue sequentially (simulate processing timing of each node) */
function pushQueryLogs() {
  const fogCount = demoApp.fogLevel === 1 ? 4 : demoApp.fogLevel === 2 ? 16 : 64;
  const logs: Array<{ delay: number; node: import('@/stores/useDemoStore').LogNode; action: string; status: import('@/stores/useDemoStore').LogStatus }> = [
    { delay: 0,    node: 'User',      action: 'Initiated secure continuous spatial keyword query q_i, coordinates and keywords encrypted locally with Paillier public key (PK)', status: 'success' },
    { delay: 800,  node: 'Cloud C1',  action: `Receives ciphertext query vector, executes secure spatial pruning based on SGL index, routes candidate set to ${fogCount} fog nodes...`, status: 'success' },
    { delay: 2000, node: 'Fog Array', action: `[${fogCount} nodes in parallel] Receives candidate set, executes secure text similarity based on SLL, returns ciphertext scoring vector...`, status: 'success' },
    { delay: 3400, node: 'Cloud C2',  action: 'Receives Fog ciphertext scores, calls Paillier private key (SK) to execute SecureCompare protocol and Top-k descending sort, decrypts in physically isolated environment...', status: 'success' },
    { delay: 4600, node: 'User',      action: 'Receives plaintext Top-k results decrypted by C2, transmitted via TLS secure channel, rendered to map and result list.', status: 'success' },
  ];
  logs.forEach(({ delay, node, action, status }) => {
    setTimeout(() => demoApp.addSystemLog({ node, action, status }), delay);
  });
}

/** Click "Execute Query": pop up terminal log first, silently send request in log */
async function handleQuery() {
  if (!queryStore.isQueryValid) {
    ElMessage.warning('Please fill in complete query information');
    return;
  }
  // First push global logs (connect to Dashboard)
  pushQueryLogs();
  // Then trigger terminal log animation (realQueryFn will be called internally)
  terminalLog.value?.run();
}

onMounted(() => {
  console.log('[DemoView] Component mounted');
  mapStore.isMapLoaded = false;
});

onUnmounted(() => {
  if (queryStore.queryId) {
    queryStore.cancel();
  }
});
</script>

<style scoped>
.demo-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  overflow: hidden;
  gap: 0;
}

/* Left query panel */
.query-panel {
  width: 380px;
  flex-shrink: 0;
  background: #0d1117;
  border-right: 1px solid #1e293b;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.3s ease;
}

.query-panel.collapsed {
  width: 0;
  border-right: none;
}

.panel-header {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid #1e293b;
  flex-shrink: 0;
  background: #111827;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  position: relative;
}

.panel-content > * {
  flex-shrink: 0;
}

/* Right map area */
.map-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
}

/* ════════════════════════════════════════════
   Public key application mask
════════════════════════════════════════════ */
.apply-mask {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 32px 20px;
  text-align: center;
  min-height: 420px;
}

.apply-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1.5px;
  color: #38bdf8;
  background: rgba(56,189,248,0.08);
  border: 1px solid rgba(56,189,248,0.2);
  border-radius: 20px;
  padding: 4px 12px;
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
}
.apply-badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #38bdf8;
  box-shadow: 0 0 6px #38bdf8;
  animation: applyPulse 1.2s ease-in-out infinite;
}
@keyframes applyPulse {
  0%,100% { opacity:1; box-shadow: 0 0 6px #38bdf8; }
  50%      { opacity:0.4; box-shadow: 0 0 2px #38bdf8; }
}

.apply-lock-icon {
  width: 80px;
  height: 80px;
  background: rgba(56,189,248,0.06);
  border: 1px solid rgba(56,189,248,0.15);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}
.apply-lock-icon svg { width: 100%; height: 100%; }

.apply-title {
  font-size: 16px;
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: 0.5px;
}

.apply-desc {
  font-size: 12px;
  color: #64748b;
  line-height: 1.8;
}
.apply-desc strong { color: #94a3b8; }

/* Apply button */
.apply-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.15s;
  box-shadow: 0 4px 20px rgba(56,189,248,0.3);
  letter-spacing: 0.5px;
}
.apply-btn:hover {
  opacity: 0.88;
  transform: translateY(-1px);
}
.apply-btn:active { transform: translateY(0); }
.apply-btn-icon { font-size: 14px; }

/* Pending status */
.apply-pending {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  background: rgba(251,191,36,0.08);
  border: 1px solid rgba(251,191,36,0.2);
  border-radius: 8px;
  font-size: 12px;
  color: #fbbf24;
  font-weight: 600;
}
.pending-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(251,191,36,0.3);
  border-top-color: #fbbf24;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Progress steps */
.apply-steps {
  display: flex;
  align-items: center;
  gap: 0;
  margin-top: 4px;
}
.apply-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: #334155;
  font-weight: 600;
  letter-spacing: 0.5px;
}
.apply-step.done span:last-child { color: #38bdf8; }
.apply-step.active span:last-child { color: #fbbf24; }
.apply-step-line {
  width: 36px;
  height: 1px;
  background: #1e293b;
  margin: 0 6px;
  margin-bottom: 14px;
  transition: background 0.3s;
}
.apply-step-line.active { background: rgba(251,191,36,0.4); }
.step-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: block;
}
.step-dot-done   { background: #38bdf8; box-shadow: 0 0 6px #38bdf8; }
.step-dot-active { background: #fbbf24; box-shadow: 0 0 6px #fbbf24; animation: applyPulse 1s ease-in-out infinite; }
.step-dot-idle   { background: #1e293b; border: 1px solid #334155; }

/* ════════════════════════════════════════════
   Authorized: Secure channel banner
════════════════════════════════════════════ */
.secure-channel-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: rgba(52,211,153,0.07);
  border: 1px solid rgba(52,211,153,0.25);
  border-radius: 10px;
  gap: 10px;
}
.scb-left {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.scb-icon { font-size: 18px; flex-shrink: 0; }
.scb-text { display: flex; flex-direction: column; gap: 2px; }
.scb-title {
  font-size: 12px;
  font-weight: 700;
  color: #34d399;
}
.scb-desc {
  font-size: 11px;
  color: #6ee7b7;
  line-height: 1.5;
}
.scb-badge {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 1.5px;
  color: #34d399;
  background: rgba(52,211,153,0.12);
  border: 1px solid rgba(52,211,153,0.3);
  border-radius: 4px;
  padding: 3px 7px;
  flex-shrink: 0;
  font-family: 'JetBrains Mono', monospace;
}

/* Query button wrapper */
.query-btn-wrap { position: relative; }

/* Responsive */
@media (max-width: 1024px) {
  .query-panel { width: 320px; }
}
@media (max-width: 768px) {
  .demo-wrapper { flex-direction: column; }
  .query-panel { width: 100%; height: 40%; border-right: none; border-bottom: 1px solid #1e293b; }
  .query-panel.collapsed { width: 100%; height: 0; border-bottom: none; }
  .map-wrapper { height: 60%; }
}
</style> 