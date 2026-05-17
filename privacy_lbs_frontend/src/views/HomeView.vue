<template>
  <div class="cockpit">
    <!-- CRT scanline -->
    <div class="scanline"></div>

    <!-- Background topology (decorative layer) -->
    <div class="topo-bg">
      <svg viewBox="0 0 800 500" preserveAspectRatio="xMidYMid slice" class="topo-svg-bg">
        <defs>
          <pattern id="sg" width="24" height="24" patternUnits="userSpaceOnUse">
            <path d="M24 0L0 0 0 24" fill="none" stroke="rgba(37,99,235,0.08)" stroke-width="0.5"/>
          </pattern>
          <pattern id="bg" width="120" height="120" patternUnits="userSpaceOnUse">
            <rect width="120" height="120" fill="url(#sg)"/>
            <path d="M120 0L0 0 0 120" fill="none" stroke="rgba(37,99,235,0.14)" stroke-width="1"/>
          </pattern>
          <radialGradient id="sweep" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="rgba(56,189,248,0.18)"/>
            <stop offset="100%" stop-color="rgba(56,189,248,0)"/>
          </radialGradient>
        </defs>
        <rect width="800" height="500" fill="url(#bg)"/>
        <!-- Rotating sweep circle -->
        <circle cx="400" cy="250" :r="sweepR" fill="none" stroke="rgba(56,189,248,0.12)" stroke-width="1" stroke-dasharray="6 4"/>
        <circle cx="400" cy="250" :r="sweepR * 0.65" fill="none" stroke="rgba(56,189,248,0.08)" stroke-width="0.5"/>
        <!-- Connection lines -->
        <g stroke="rgba(37,99,235,0.25)" stroke-width="0.8" stroke-dasharray="5 4">
          <line v-for="e in topoEdges" :key="e.id"
            :x1="bgNodes[e.from].x" :y1="bgNodes[e.from].y"
            :x2="bgNodes[e.to].x"   :y2="bgNodes[e.to].y"/>
        </g>
        <!-- Data packets -->
        <circle v-for="p in packets" :key="p.id" :cx="p.x" :cy="p.y" r="2.5" fill="#38bdf8" opacity="0.6"/>
        <!-- Nodes -->
        <g v-for="n in bgNodes" :key="n.id">
          <circle :cx="n.x" :cy="n.y" :r="n.pulse" fill="none" :stroke="n.color" stroke-width="0.8" opacity="0.18"/>
          <circle :cx="n.x" :cy="n.y" :r="n.r" :fill="n.fill" :stroke="n.color" stroke-width="1"/>
          <text :x="n.x" :y="n.y+4" text-anchor="middle" font-size="7" :fill="n.color" font-family="monospace">{{n.abbr}}</text>
        </g>
        <!-- Sweep ray -->
        <line :x1="400" :y1="250"
          :x2="400 + sweepR * Math.cos(sweepAngle)"
          :y2="250 + sweepR * Math.sin(sweepAngle)"
          stroke="rgba(56,189,248,0.35)" stroke-width="1.5"/>
      </svg>
    </div>

    <!-- Top status bar -->
    <header class="hdr">
      <div class="hdr-left">
        <span class="hdr-dot"></span>
        <span class="hdr-sys">SYSTEM NOMINAL</span>
        <span class="hdr-sep">|</span>
        <span class="hdr-proto">PAILLIER-2048</span>
        <span class="hdr-sep">|</span>
        <span class="hdr-proj">PROJECT: SKTAQ-CN-2026</span>
      </div>
      <div class="hdr-right">
        <span class="hdr-nodes">FOG NODES: <em>{{ fogNodes }}/16</em></span>
        <span class="hdr-sep">|</span>
        <span class="hdr-enc">ENC: <em>PROTECTED</em></span>
        <span class="hdr-sep">|</span>
        <span class="hdr-time">{{ clock }}</span>
      </div>
    </header>

    <!-- Main content area -->
    <div class="hero-wrap">
      <!-- Main title -->
      <div class="hero-title-block">
        <div class="hero-badge">RESEARCH PROTOTYPE v2.0 · ENCRYPTION STATUS: PROTECTED</div>
        <h1 class="hero-title">
          <span class="glitch" data-text="SKTAQ">SKTAQ</span>
        </h1>
        <p class="hero-sub">Privacy-Preserving Spatial Keyword Query System in Cloud-Fog Collaborative Environment</p>
        <p class="hero-desc">Research Demo Platform Based on Paillier Homomorphic Encryption and Distributed KASTree Index</p>
        <div class="hero-tags">
          <span class="htag">Paillier Encryption</span>
          <span class="htag">KASTree Index</span>
          <span class="htag">Cloud-Fog Collaboration</span>
          <span class="htag">Safe Zone</span>
          <span class="htag">Continuous Spatial Query</span>
        </div>
      </div>

      <!-- Four entry cards -->
      <div class="entry-grid">
        <div v-for="(card, idx) in cards" :key="card.name"
          class="entry-card"
          :class="'card-' + card.color"
          @click="handleNav(card.route)"
        >
          <div class="card-num">[0{{ idx+1 }}]</div>
          <div class="card-icon" v-html="card.svg"></div>
          <div class="card-role">{{ card.role }}</div>
          <div class="card-title">{{ card.title }}</div>
          <div class="card-desc">{{ card.desc }}</div>
          <div class="card-footer">
            <span class="card-state" :class="card.stateType">{{ card.state }}</span>
            <svg class="card-arrow" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M4 10h12M10 4l6 6-6 6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </div>
      </div>

      <!-- Bottom decorative bar -->
      <div class="bottom-bar">
        <span class="bb-item">ENCRYPTION STATUS: PROTECTED</span>
        <span class="bb-sep">·</span>
        <span class="bb-item">NODES: 16/16 ACTIVE</span>
        <span class="bb-sep">·</span>
        <span class="bb-item">ALGO: PAILLIER-2048 + KASTREE</span>
        <span class="bb-sep">·</span>
        <span class="bb-item">REGION: CN-EAST · FOG CLUSTER A</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
function handleNav(name: string) { router.push({ name }); }

// Clock
const clock = ref('');
function updateClock() {
  clock.value = new Date().toISOString().replace('T',' ').slice(0,19) + ' UTC';
}

const fogNodes = ref(16);

// Entry cards
const cards = [
  {
    name: 'config', route: 'config',
    role: 'DO Role · Security Init',
    title: 'Paillier Key Generation',
    desc: 'Configure 1024/2048-bit key pair, initialize homomorphic encryption foundation, distribute public/private keys to cloud and fog nodes.',
    color: 'blue', state: '● Ready', stateType: 'ok',
    svg: `<svg viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5">
      <rect x="8" y="19" width="24" height="16" rx="2"/>
      <path d="M13 19v-6a7 7 0 0 1 14 0v6" stroke-linecap="round"/>
      <circle cx="20" cy="27" r="2.5" fill="currentColor"/>
      <path d="M20 29.5v3" stroke-linecap="round"/>
    </svg>`,
  },
  {
    name: 'dashboard', route: 'dashboard',
    role: 'DO Role · Data Distribution',
    title: 'Encrypted Data Import',
    desc: 'Upload raw CSV, build KASTree index locally, homomorphic encryption then sync to cloud and fog nodes.',
    color: 'cyan', state: '● Pending Upload', stateType: 'warn',
    svg: `<svg viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5">
      <rect x="5" y="7" width="30" height="7" rx="1.5"/>
      <rect x="5" y="17" width="30" height="7" rx="1.5"/>
      <rect x="5" y="27" width="30" height="7" rx="1.5"/>
      <circle cx="10" cy="10.5" r="1.5" fill="currentColor"/>
      <circle cx="10" cy="20.5" r="1.5" fill="currentColor"/>
      <path d="M24 30l3 3 7-7" stroke-linecap="round" stroke-linejoin="round" stroke="#34d399"/>
    </svg>`,
  },
  {
    name: 'demo', route: 'demo',
    role: 'User Role · Query Terminal',
    title: 'Real-time Privacy Query',
    desc: 'Enter map workspace, execute continuous spatial keyword queries, monitor Safe Zone boundaries and result updates in real-time.',
    color: 'violet', state: '● Online', stateType: 'ok',
    svg: `<svg viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5">
      <circle cx="18" cy="18" r="10"/>
      <path d="M26 26l7 7" stroke-linecap="round"/>
      <circle cx="18" cy="18" r="4" stroke-dasharray="3 2"/>
      <circle cx="18" cy="18" r="1.5" fill="currentColor"/>
    </svg>`,
  },
  {
    name: 'analysis', route: 'analysis',
    role: 'Admin Role · Performance Audit',
    title: 'Experimental Results Analysis',
    desc: 'View query latency distribution, Safe Zone hit rate trends, pruning efficiency and other core research evaluation metrics.',
    color: 'amber', state: '● Normal', stateType: 'ok',
    svg: `<svg viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5">
      <rect x="4" y="5" width="32" height="26" rx="2"/>
      <path d="M4 31l9-10 7 5 8-12 7 7" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M4 35h32" stroke-linecap="round"/>
    </svg>`,
  },
];

// Background topology nodes
const bgNodes = [
  { id:0, x:400, y:250, r:14, pulse:22, label:'MU', abbr:'MU', color:'#38bdf8', fill:'rgba(56,189,248,0.12)' },
  { id:1, x:400, y:110, r:11, pulse:18, label:'CS', abbr:'CS', color:'#818cf8', fill:'rgba(129,140,248,0.12)' },
  { id:2, x:230, y:175, r: 9, pulse:15, label:'FA', abbr:'FA', color:'#34d399', fill:'rgba(52,211,153,0.12)' },
  { id:3, x:570, y:175, r: 9, pulse:15, label:'FB', abbr:'FB', color:'#34d399', fill:'rgba(52,211,153,0.12)' },
  { id:4, x:230, y:330, r: 9, pulse:15, label:'FC', abbr:'FC', color:'#34d399', fill:'rgba(52,211,153,0.12)' },
  { id:5, x:570, y:330, r: 9, pulse:15, label:'FD', abbr:'FD', color:'#34d399', fill:'rgba(52,211,153,0.12)' },
  { id:6, x:400, y:390, r: 9, pulse:15, label:'DO', abbr:'DO', color:'#fb923c', fill:'rgba(251,146,60,0.12)' },
];
const topoEdges = [
  {id:'e01',from:0,to:1},{id:'e02',from:0,to:2},{id:'e03',from:0,to:3},
  {id:'e04',from:1,to:2},{id:'e05',from:1,to:3},{id:'e06',from:1,to:4},{id:'e07',from:1,to:5},
  {id:'e08',from:2,to:4},{id:'e09',from:3,to:5},{id:'e10',from:6,to:1},
  {id:'e11',from:6,to:2},{id:'e12',from:6,to:3},
];

// Pulse animation
const pulseDir = bgNodes.map(() => 1);
function animatePulse() {
  bgNodes.forEach((n,i) => {
    n.pulse += pulseDir[i] * 0.3;
    if (n.pulse > n.r+14) pulseDir[i]=-1;
    if (n.pulse < n.r+3)  pulseDir[i]= 1;
  });
}

// Scan circle
const sweepAngle = ref(0);
const sweepR = ref(160);
function animateSweep() {
  sweepAngle.value += 0.025;
  sweepR.value = 155 + Math.sin(sweepAngle.value * 0.5) * 10;
}

// Data packet particles
interface Packet { id:number; edgeIdx:number; t:number; x:number; y:number; }
const packets = ref<Packet[]>([]);
let pktId = 0;
function spawnPacket() {
  const ei = Math.floor(Math.random() * topoEdges.length);
  const from = bgNodes[topoEdges[ei].from];
  packets.value.push({id:pktId++, edgeIdx:ei, t:0, x:from.x, y:from.y});
}
function movePackets() {
  packets.value = packets.value.filter(p => p.t < 1).map(p => {
    p.t += 0.016;
    const e = topoEdges[p.edgeIdx];
    const f = bgNodes[e.from], t = bgNodes[e.to];
    p.x = f.x + (t.x - f.x) * p.t;
    p.y = f.y + (t.y - f.y) * p.t;
    return p;
  });
}

const timers: number[] = [];
onMounted(() => {
  updateClock();
  timers.push(window.setInterval(updateClock, 1000));
  timers.push(window.setInterval(() => { animatePulse(); animateSweep(); movePackets(); }, 40));
  timers.push(window.setInterval(spawnPacket, 700));
});
onUnmounted(() => { timers.forEach(clearInterval); });
</script>

<style scoped>
* { box-sizing: border-box; margin: 0; padding: 0; }

.cockpit {
  width: 100vw;
  height: 100vh;
  background: #020b18;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  font-family: 'Roboto Mono', 'JetBrains Mono', 'Courier New', monospace;
  color: #94a3b8;
}

/* CRT scanline */
.scanline {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 200;
  opacity: 0.3;
  background: repeating-linear-gradient(
    0deg, transparent, transparent 3px,
    rgba(0,0,0,0.06) 3px, rgba(0,0,0,0.06) 4px
  );
}

/* Background topology layer */
.topo-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  opacity: 0.55;
}
.topo-svg-bg {
  width: 100%;
  height: 100%;
}

/* Top status bar */
.hdr {
  position: relative;
  z-index: 10;
  height: 36px;
  background: rgba(4,15,30,0.85);
  border-bottom: 1px solid rgba(37,99,235,0.25);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
  backdrop-filter: blur(8px);
}
.hdr-left, .hdr-right { display:flex; align-items:center; gap:10px; }
.hdr-dot { width:7px; height:7px; border-radius:50%; background:#34d399; box-shadow:0 0 6px #34d399; animation:blink 2s infinite; flex-shrink:0; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
.hdr-sys   { font-size:13px; color:#34d399; letter-spacing:2px; }
.hdr-proto { font-size:13px; color:#818cf8; letter-spacing:1px; }
.hdr-proj  { font-size:11px; color:#1e3a5f; letter-spacing:1px; }
.hdr-sep   { color:#1e3a5f; }
.hdr-nodes { font-size:13px; color:#64748b; }
.hdr-nodes em { color:#38bdf8; font-style:normal; }
.hdr-enc   { font-size:13px; color:#64748b; }
.hdr-enc em { color:#34d399; font-style:normal; }
.hdr-time  { font-size:13px; color:#334155; font-variant-numeric:tabular-nums; }

/* Main content area */
.hero-wrap {
  position: relative;
  z-index: 10;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 40px 16px;
  gap: 32px;
  overflow-y: auto;
}

/* Hero title section */
.hero-title-block {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.hero-badge {
  font-size: 12px;
  letter-spacing: 3px;
  color: #3b82f6;
  border: 1px solid rgba(59,130,246,0.3);
  border-radius: 2px;
  padding: 5px 18px;
  background: rgba(59,130,246,0.06);
  text-transform: uppercase;
}

/* Glitch title effect */
.hero-title {
  font-size: clamp(52px, 9vw, 110px);
  font-weight: 900;
  line-height: 1;
  letter-spacing: 8px;
  color: #f1f5f9;
  text-transform: uppercase;
  position: relative;
}
.glitch {
  position: relative;
  display: inline-block;
}
.glitch::before,
.glitch::after {
  content: attr(data-text);
  position: absolute;
  inset: 0;
  font-weight: 900;
  letter-spacing: 8px;
}
.glitch::before {
  color: #38bdf8;
  animation: glitch1 3.5s infinite;
  clip-path: polygon(0 0, 100% 0, 100% 35%, 0 35%);
}
.glitch::after {
  color: #818cf8;
  animation: glitch2 3.5s infinite;
  clip-path: polygon(0 65%, 100% 65%, 100% 100%, 0 100%);
}
@keyframes glitch1 {
  0%,90%,100% { transform: translate(0); opacity:0; }
  92%  { transform: translate(-3px, 1px); opacity:0.7; }
  94%  { transform: translate(3px,-1px); opacity:0.7; }
  96%  { transform: translate(-2px, 0);  opacity:0.7; }
  98%  { transform: translate(0);        opacity:0; }
}
@keyframes glitch2 {
  0%,88%,100% { transform: translate(0); opacity:0; }
  90%  { transform: translate(3px,-1px); opacity:0.6; }
  93%  { transform: translate(-3px,1px); opacity:0.6; }
  97%  { transform: translate(2px, 0);   opacity:0; }
}

.hero-sub {
  font-size: clamp(20px, 2.8vw, 32px);
  font-weight: 600;
  color: #93c5fd;
  font-family: 'PingFang SC','Microsoft YaHei',sans-serif;
  letter-spacing: 2px;
}
.hero-desc {
  font-size: 15px;
  color: #64748b;
  font-family: 'PingFang SC','Microsoft YaHei',sans-serif;
  letter-spacing: 0.5px;
}
.hero-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}
.htag {
  font-size: 13px;
  padding: 4px 14px;
  border: 1px solid rgba(37,99,235,0.3);
  color: #64748b;
  background: rgba(37,99,235,0.06);
  font-family: 'PingFang SC','Microsoft YaHei',sans-serif;
}

/* Four entry cards */
.entry-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  width: 100%;
  max-width: 1100px;
}
.entry-card {
  position: relative;
  padding: 22px 18px 16px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 8px;
  backdrop-filter: blur(16px);
  background: rgba(4, 15, 30, 0.55);
  border: 1px solid rgba(37,99,235,0.2);
  transition: transform 0.25s cubic-bezier(0.34,1.56,0.64,1),
              box-shadow 0.25s ease,
              border-color 0.25s ease;
  overflow: hidden;
}
.entry-card::before {
  content: '';
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 0.3s;
  border-radius: 4px;
}
.entry-card:hover { transform: translateY(-5px) scale(1.02); }
.entry-card:hover::before { opacity: 1; }

/* Color theme */
.card-blue { border-color: rgba(59,130,246,0.25); }
.card-blue:hover { border-color: rgba(59,130,246,0.65); box-shadow: 0 0 28px rgba(59,130,246,0.2), 0 8px 24px rgba(0,0,0,0.5); }
.card-blue::before { background: radial-gradient(circle at top left, rgba(59,130,246,0.1) 0%, transparent 60%); }
.card-blue .card-icon { color: #60a5fa; }
.card-blue .card-title { color: #93c5fd; }
.card-blue .card-num  { color: #1d4ed8; }
.card-blue .card-arrow { color: #60a5fa; }

.card-cyan { border-color: rgba(6,182,212,0.25); }
.card-cyan:hover { border-color: rgba(6,182,212,0.65); box-shadow: 0 0 28px rgba(6,182,212,0.18), 0 8px 24px rgba(0,0,0,0.5); }
.card-cyan::before { background: radial-gradient(circle at top left, rgba(6,182,212,0.1) 0%, transparent 60%); }
.card-cyan .card-icon { color: #22d3ee; }
.card-cyan .card-title { color: #67e8f9; }
.card-cyan .card-num  { color: #0e7490; }
.card-cyan .card-arrow { color: #22d3ee; }

.card-violet { border-color: rgba(139,92,246,0.25); }
.card-violet:hover { border-color: rgba(139,92,246,0.65); box-shadow: 0 0 28px rgba(139,92,246,0.2), 0 8px 24px rgba(0,0,0,0.5); }
.card-violet::before { background: radial-gradient(circle at top left, rgba(139,92,246,0.1) 0%, transparent 60%); }
.card-violet .card-icon { color: #a78bfa; }
.card-violet .card-title { color: #c4b5fd; }
.card-violet .card-num  { color: #6d28d9; }
.card-violet .card-arrow { color: #a78bfa; }

.card-amber { border-color: rgba(245,158,11,0.25); }
.card-amber:hover { border-color: rgba(245,158,11,0.65); box-shadow: 0 0 28px rgba(245,158,11,0.18), 0 8px 24px rgba(0,0,0,0.5); }
.card-amber::before { background: radial-gradient(circle at top left, rgba(245,158,11,0.1) 0%, transparent 60%); }
.card-amber .card-icon { color: #fbbf24; }
.card-amber .card-title { color: #fcd34d; }
.card-amber .card-num  { color: #92400e; }
.card-amber .card-arrow { color: #fbbf24; }

.card-num {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 2px;
  opacity: 0.8;
}
.card-icon {
  width: 44px;
  height: 44px;
}
.card-icon :deep(svg) { width: 44px; height: 44px; }
.card-role {
  font-size: 11px;
  color: #475569;
  letter-spacing: 1px;
  text-transform: uppercase;
  font-family: 'PingFang SC','Microsoft YaHei',sans-serif;
}
.card-title {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
}
.card-desc {
  font-size: 13px;
  color: #64748b;
  line-height: 1.75;
  font-family: 'PingFang SC','Microsoft YaHei',sans-serif;
  flex: 1;
}
.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 10px;
  border-top: 1px solid rgba(255,255,255,0.05);
}
.card-state {
  font-size: 12px;
  font-family: monospace;
}
.card-state.ok   { color: #34d399; }
.card-state.warn { color: #f59e0b; }
.card-arrow { width: 18px; height: 18px; transition: transform 0.2s; }
.entry-card:hover .card-arrow { transform: translateX(4px); }

/* Bottom decoration bar */
.bottom-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 9px;
  color: #1e3a5f;
  letter-spacing: 1px;
  font-family: monospace;
  flex-wrap: wrap;
  justify-content: center;
}
.bb-sep { color: #0f2440; }

/* Responsive */
@media (max-width: 1000px) {
  .entry-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .entry-grid { grid-template-columns: 1fr; }
  .hero-wrap { padding: 16px 20px 12px; gap: 20px; }
}
</style>
