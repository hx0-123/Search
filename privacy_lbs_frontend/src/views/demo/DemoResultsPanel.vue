<template>
  <div class="demo-panel">
    <div class="panel-title"><span>📍</span>Query Results</div>
    <div class="results-layout">
      <!-- Map placeholder -->
      <div class="map-mock">
        <svg viewBox="0 0 400 300" class="mock-svg">
          <rect width="400" height="300" fill="#0d1424" rx="8" />
          <g stroke="#1e3a5f" stroke-width="0.5">
            <line v-for="x in 20" :key="'v'+x" :x1="x*20" y1="0" :x2="x*20" y2="300" />
            <line v-for="y in 15" :key="'h'+y" x1="0" :y1="y*20" x2="400" :y2="y*20" />
          </g>
          <!-- Safe Zone -->
          <circle cx="200" cy="150" r="80" fill="rgba(96,165,250,0.08)" stroke="#3b82f6" stroke-width="1.5" stroke-dasharray="5 3" />
          <!-- Query point -->
          <circle cx="200" cy="150" r="8" fill="#3b82f6" />
          <circle cx="200" cy="150" r="16" fill="rgba(59,130,246,0.2)" />
          <!-- POI markers (appear one by one) -->
          <transition-group name="poi-pop">
            <g v-for="poi in visiblePOIs" :key="poi.id">
              <circle :cx="poi.x" :cy="poi.y" r="7" fill="#34d399" />
              <text :x="poi.x + 10" :y="poi.y + 4" font-size="9" fill="#94a3b8">{{ poi.name }}</text>
            </g>
          </transition-group>
          <!-- Label -->
          <text x="200" y="85" font-size="10" fill="#60a5fa" text-anchor="middle">Safe Zone r=1000m</text>
        </svg>
      </div>
      <!-- Results list -->
      <div class="result-list">
        <div
          v-for="(r, idx) in visiblePOIs" :key="r.id"
          class="result-item"
          :style="{ animationDelay: idx * 0.08 + 's' }"
        >
          <span class="r-rank">#{{ idx + 1 }}</span>
          <div class="r-body">
            <span class="r-name">{{ r.name }}</span>
            <div class="r-bars">
              <el-progress :percentage="r.score" :stroke-width="5" :show-text="false" color="#34d399" style="flex:1" />
              <span class="r-score">{{ r.score }}</span>
            </div>
            <span class="r-meta">{{ r.dist }} m · {{ r.cat }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
const ALL_POIS = [
  { id:1, name:'Da Dong Roast Duck', x:230, y:130, score:95, dist:280,  cat:'Restaurant' },
  { id:2, name:'Quan Jude Peking Duck', x:170, y:170, score:91, dist:340,  cat:'Restaurant' },
  { id:3, name:'Haidilao Hotpot', x:250, y:180, score:88, dist:520,  cat:'Hotpot' },
  { id:4, name:'McDonald', x:155, y:130, score:82, dist:680,  cat:'Fast Food' },
  { id:5, name:'Starbucks', x:210, y:100, score:79, dist:750,  cat:'Coffee' },
  { id:6, name:'Pizza Hut', x:240, y:210, score:75, dist:820,  cat:'Western' },
  { id:7, name:'KFC', x:178, y:195, score:72, dist:900,  cat:'Fast Food' },
  { id:8, name:'Heytea', x:225, y:145, score:68, dist:950,  cat:'Tea' },
  { id:9, name:'Ippudo Ramen', x:160, y:155, score:65, dist:1050, cat:'Japanese' },
  { id:10,name:'Waipojia', x:195, y:210, score:61, dist:1200, cat:'Chinese' },
];
const visiblePOIs = ref<typeof ALL_POIS>([]);
onMounted(() => {
  ALL_POIS.forEach((p, i) => setTimeout(() => visiblePOIs.value.push(p), 200 + i * 250));
});
</script>

<style scoped>
.demo-panel { padding: 24px; display: flex; flex-direction: column; gap: 16px; height: 100%; }
.panel-title { font-size: 20px; font-weight: 700; color: #60a5fa; display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.results-layout { display: flex; gap: 16px; flex: 1; overflow: hidden; }
.map-mock { flex: 1; border-radius: 10px; overflow: hidden; border: 1px solid #1e3a5f; }
.mock-svg { width: 100%; height: 100%; }
.result-list { width: 220px; flex-shrink: 0; display: flex; flex-direction: column; gap: 6px; overflow-y: auto; }
.result-item {
  background: #0d1424; border: 1px solid #1e3a5f; border-radius: 8px;
  padding: 8px 10px; display: flex; gap: 8px; align-items: center;
  animation: slideIn 0.3s ease both;
}
@keyframes slideIn { from { opacity:0; transform:translateX(16px); } }
.r-rank { font-size: 13px; font-weight: 700; color: #60a5fa; min-width: 24px; text-align: center; }
.r-body { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.r-name { font-size: 12px; color: #e2e8f0; font-weight: 500; }
.r-bars { display: flex; align-items: center; gap: 6px; }
.r-score { font-size: 11px; color: #34d399; font-variant-numeric: tabular-nums; min-width: 24px; }
.r-meta { font-size: 10px; color: #475569; }
.poi-pop-enter-active { transition: all 0.3s cubic-bezier(0.34,1.56,0.64,1); }
.poi-pop-enter-from { opacity: 0; transform: scale(0); }
</style>






