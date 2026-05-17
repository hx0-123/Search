<template>
  <!-- Floating terminal log panel, fixed at bottom-right of map -->
  <Transition name="terminal-slide">
    <div v-if="visible" class="cftl-wrap">
      <!-- Title bar -->
      <div class="cftl-titlebar">
        <div class="cftl-dots">
          <span class="cftl-dot cftl-dot-red"></span>
          <span class="cftl-dot cftl-dot-yellow"></span>
          <span class="cftl-dot cftl-dot-green"></span>
        </div>
        <span class="cftl-title">CLOUD-FOG SECURE CHANNEL</span>
        <span class="cftl-status" :class="isDone ? 'cftl-status-done' : 'cftl-status-run'">
          {{ isDone ? 'DONE' : 'RUNNING' }}
        </span>
      </div>

      <!-- Log body -->
      <div class="cftl-body" ref="bodyRef">
        <div
          v-for="(line, idx) in lines"
          :key="idx"
          class="cftl-line"
          :class="lineClass(line.tag, line.highlight)"
        >
          <span class="cftl-tag">[{{ line.tag }}]</span>
          <span class="cftl-msg">{{ line.msg }}</span>
        </div>
        <!-- Blinking cursor -->
        <span v-if="!isDone" class="cftl-cursor">█</span>
      </div>

      <!-- Progress bar -->
      <div class="cftl-progress-bar">
        <div class="cftl-progress-fill" :style="{ width: progressPct + '%' }"></div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue';
import { useDemoAppStore } from '@/stores/useDemoStore';

// ── Props / Emits ─────────────────────────────────────────
const props = defineProps<{
  /** External: Real query Promise factory, triggers request when called */
  queryFn: () => Promise<any>;
}>();

const emit = defineEmits<{
  /** Triggered when log ends and real data returns, with backend results */
  (e: 'done', results: any): void;
}>();

// ── Store ─────────────────────────────────────────────────
const demoApp = useDemoAppStore();

// ── State ──────────────────────────────────────────────────
const visible     = ref(false);
const isDone      = ref(false);
const lines       = ref<{ tag: string; msg: string; highlight?: boolean }[]>([]);
const bodyRef     = ref<HTMLElement | null>(null);
const progressPct = ref(0);

// ── Log Script ──────────────────────────────────────────────
function buildScript(fogLevel: number): { tag: string; msg: string; highlight?: boolean }[] {
  const gridCount = fogLevel === 1 ? 4 : fogLevel === 2 ? 16 : 64;
  return [
    { tag: 'Client',   msg: 'Using local public key (PK) to perform Paillier homomorphic encryption on coordinates and keywords...' },
    { tag: 'Cloud C1', msg: 'Received ciphertext request, triggering KASTree Secure Spatial Pruning...' },
    { tag: 'Cloud C1 & Fog', msg: `Performing secure spatial pruning and text scoring in ciphertext state, routing task to Lv.${fogLevel} · ${gridCount} fog nodes...` },
    { tag: 'Fog Node', msg: 'Executing ciphertext similarity scoring on local R-Tree (SLL), returning encrypted Top-k candidates...' },
    { tag: 'Cloud C2', msg: 'Received encrypted Top-k candidates...', highlight: true },
    { tag: 'Cloud C2', msg: 'Permission verified: Calling physically isolated Paillier private key (SK) for final decryption...', highlight: true },
    { tag: 'Secure Channel', msg: 'Data desensitization completed, plaintext Top-k results returned to query terminal via TLS secure channel...', highlight: true },
    { tag: 'Client',   msg: 'Receiving and rendering plaintext query results.' },
  ];
}

// ── Auto scroll to bottom ──────────────────────────────────
async function scrollBottom() {
  await nextTick();
  if (bodyRef.value) {
    bodyRef.value.scrollTop = bodyRef.value.scrollHeight;
  }
}

// ── Tag color class mapping ────────────────────────────────
function lineClass(tag: string, highlight?: boolean) {
  if (highlight) return 'cftl-line-highlight';
  if (tag === 'Client')         return 'cftl-line-client';
  if (tag === 'Cloud C1')       return 'cftl-line-c1';
  if (tag === 'Cloud C1 & Fog') return 'cftl-line-c1';
  if (tag === 'Cloud C2')       return 'cftl-line-c2';
  if (tag === 'Fog Node')       return 'cftl-line-fog';
  if (tag === 'Secure Channel') return 'cftl-line-secure';
  return '';
}

// ── Main entry: Call this method externally to trigger the entire process ────────────
async function run() {
  // Reset
  lines.value       = [];
  isDone.value      = false;
  progressPct.value = 0;
  visible.value     = true;

  const script   = buildScript(demoApp.fogLevel);
  const INTERVAL = 800; // ms per line

  // Start real request simultaneously (silent, don't wait)
  const queryPromise = props.queryFn();

  // Print log line by line
  for (let i = 0; i < script.length; i++) {
    await new Promise<void>(r => setTimeout(r, INTERVAL));
    lines.value.push(script[i]);
    progressPct.value = Math.round(((i + 1) / script.length) * 90);
    scrollBottom();
  }

  // Wait for real request to complete (whichever finishes later: logs or request)
  let results: any = null;
  try {
    results = await queryPromise;
  } catch (e) {
    console.error('[CloudFogTerminalLog] queryFn error:', e);
  }

  // Complete
  progressPct.value = 100;
  isDone.value      = true;

  // Wait 600ms for user to see DONE, then collapse
  await new Promise<void>(r => setTimeout(r, 600));
  visible.value = false;

  // Notify parent component to render results
  emit('done', results);
}

// Expose for parent component to call
defineExpose({ run });
</script>

<style scoped>
/* ── Outer Container ── */
.cftl-wrap {
  position: absolute;
  bottom: 24px;
  right: 24px;
  width: 480px;
  max-width: calc(100vw - 48px);
  background: #0a0f1a;
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(56, 189, 248, 0.08);
  z-index: 9999;
  font-family: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
}

/* ── Title Bar ── */
.cftl-titlebar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  background: #111827;
  border-bottom: 1px solid #1e3a5f;
}
.cftl-dots {
  display: flex;
  gap: 5px;
  flex-shrink: 0;
}
.cftl-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.cftl-dot-red    { background: #f87171; }
.cftl-dot-yellow { background: #fbbf24; }
.cftl-dot-green  { background: #34d399; }

.cftl-title {
  flex: 1;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #475569;
  text-transform: uppercase;
}
.cftl-status {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 1.5px;
  padding: 2px 7px;
  border-radius: 3px;
}
.cftl-status-run  { background: rgba(56,189,248,0.15); color: #38bdf8; }
.cftl-status-done { background: rgba(52,211,153,0.15); color: #34d399; }

/* ── Log Body ── */
.cftl-body {
  padding: 12px 14px;
  min-height: 120px;
  max-height: 240px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
  scrollbar-width: thin;
  scrollbar-color: #1e3a5f transparent;
}
.cftl-body::-webkit-scrollbar { width: 4px; }
.cftl-body::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 2px; }

.cftl-line {
  display: flex;
  gap: 8px;
  font-size: 12px;
  line-height: 1.6;
  animation: fadeInLine 0.25s ease;
}
@keyframes fadeInLine {
  from { opacity: 0; transform: translateX(-6px); }
  to   { opacity: 1; transform: translateX(0); }
}

.cftl-tag {
  flex-shrink: 0;
  font-weight: 700;
  min-width: 80px;
}
.cftl-msg {
  color: #94a3b8;
}

/* Node colors */
.cftl-line-client .cftl-tag  { color: #34d399; }
.cftl-line-c1    .cftl-tag  { color: #38bdf8; }
.cftl-line-c2    .cftl-tag  { color: #818cf8; }
.cftl-line-fog   .cftl-tag  { color: #fbbf24; }
.cftl-line-secure .cftl-tag { color: #f472b6; }

.cftl-line-client .cftl-msg  { color: #6ee7b7; }
.cftl-line-c1    .cftl-msg   { color: #7dd3fc; }
.cftl-line-c2    .cftl-msg   { color: #a5b4fc; }
.cftl-line-fog   .cftl-msg   { color: #fde68a; }
.cftl-line-secure .cftl-msg  { color: #f9a8d4; }

/* C2 decryption highlight */
.cftl-line-highlight {
  background: rgba(129, 140, 248, 0.08);
  border-left: 2px solid #818cf8;
  padding-left: 6px;
  border-radius: 0 4px 4px 0;
  margin-left: -6px;
}
.cftl-line-highlight .cftl-tag { color: #818cf8; }
.cftl-line-highlight .cftl-msg { color: #c7d2fe; font-weight: 600; }

/* Cursor */
.cftl-cursor {
  font-size: 12px;
  color: #34d399;
  animation: blink 0.8s step-end infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0; }
}

/* ── Progress Bar ── */
.cftl-progress-bar {
  height: 3px;
  background: #1e293b;
}
.cftl-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #38bdf8, #34d399);
  transition: width 0.4s ease;
  border-radius: 0 2px 2px 0;
}

/* ── Enter/Leave Animation ── */
.terminal-slide-enter-active,
.terminal-slide-leave-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
.terminal-slide-enter-from,
.terminal-slide-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.97);
}
</style>
