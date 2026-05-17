<!--
  Result Marker Layer Component
  Directly renders plaintext POI markers (Cloud C2 has completed Paillier decryption on backend)
-->
<template>
  <!-- This component operates via map instance, no template DOM needed -->
</template>

<script setup lang="ts">
import { watch, onMounted, onUnmounted } from 'vue';
import mapboxgl from 'mapbox-gl';
import { useMapStore } from '@/stores/map.store';
import { useResultStore } from '@/stores/result.store';

const mapStore    = useMapStore();
const resultStore = useResultStore();

let markers: mapboxgl.Marker[] = [];

function updateResultMarkers() {
  const map = mapStore.mapInstance;
  if (!map || !mapStore.isMapLoaded) return;

  const results = resultStore.sortedResults;

  // Clear old markers
  markers.forEach(m => { try { m.remove(); } catch {} });
  markers = [];

  if (!results || results.length === 0) return;

  const limitedResults = results.slice(0, 20);

  limitedResults.forEach((result, index) => {
    try {
      const location = result.spatialObject?.location;
      if (
        !location ||
        location.longitude == null ||
        location.latitude  == null ||
        isNaN(location.longitude) ||
        isNaN(location.latitude)  ||
        Math.abs(location.latitude)  > 90  ||
        Math.abs(location.longitude) > 180
      ) {
        console.warn(`[ResultMarkerLayer] Skip invalid location #${index + 1}:`, location);
        return;
      }

      // Plaintext name (C2 decrypted, use directly)
      const rawName = (result.spatialObject.name ?? '').trim();
      const isObjectId = /^[0-9a-f-]{32,}$/i.test(rawName);
      const displayName = isObjectId || !rawName ? `POI #${index + 1}` : rawName;

      // Score values
      const overallScore  = typeof result.score         === 'number' ? result.score.toFixed(2)         : '—';
      const textScore     = typeof result.textScore     === 'number' ? result.textScore.toFixed(2)     : '—';
      const distanceScore = typeof result.distanceScore === 'number' ? result.distanceScore.toFixed(2) : '—';
      const distanceLabel = typeof result.distance      === 'number'
        ? (result.distance >= 1000 ? `${(result.distance / 1000).toFixed(1)} km` : `${result.distance} m`)
        : '—';
      const barW = typeof result.score === 'number' ? Math.round(result.score * 100) : 0;

      // Marker element
      const el = document.createElement('div');
      el.className = 'result-marker';
      Object.assign(el.style, {
        backgroundColor: '#10b981',
        width: '20px',
        height: '20px',
        borderRadius: '50%',
        border: '2px solid white',
        cursor: 'pointer',
        boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
      });

      const marker = new mapboxgl.Marker(el)
        .setLngLat([location.longitude, location.latitude])
        .addTo(map);

      el.addEventListener('click', () => {
        resultStore.setSelectedResult(result);

        new mapboxgl.Popup({ offset: 25, maxWidth: '240px' })
          .setLngLat([location.longitude, location.latitude])
          .setHTML(`
            <div style="font-family:'PingFang SC','Microsoft YaHei',sans-serif;padding:10px 12px;min-width:200px">
              <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px">
                <span style="background:#10b981;color:#fff;font-size:11px;font-weight:700;border-radius:3px;padding:1px 6px">#${index + 1}</span>
                <strong style="font-size:13px;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#1e293b">${displayName}</strong>
              </div>
              <div style="background:#f1f5f9;border-radius:4px;overflow:hidden;height:6px;margin-bottom:8px">
                <div style="width:${barW}%;height:100%;background:linear-gradient(90deg,#10b981,#059669);border-radius:4px"></div>
              </div>
              <table style="width:100%;font-size:12px;border-collapse:collapse">
                <tr><td style="color:#64748b;padding:2px 0">Overall Score</td><td style="text-align:right;font-weight:700;color:#10b981">${overallScore}</td></tr>
                <tr><td style="color:#64748b;padding:2px 0">Text Score</td><td style="text-align:right;color:#38bdf8">${textScore}</td></tr>
                <tr><td style="color:#64748b;padding:2px 0">Distance Score</td><td style="text-align:right;color:#a78bfa">${distanceScore}</td></tr>
                <tr><td style="color:#64748b;padding:2px 0">Actual Distance</td><td style="text-align:right;color:#94a3b8">${distanceLabel}</td></tr>
              </table>
              ${result.spatialObject.description
                ? `<div style="margin-top:7px;padding-top:7px;border-top:1px solid #e2e8f0;font-size:11px;color:#64748b;line-height:1.5">${result.spatialObject.description}</div>`
                : ''}
            </div>
          `)
          .addTo(map);
      });

      markers.push(marker);
    } catch (error) {
      console.error(`[ResultMarkerLayer] Create marker failed #${index}:`, error);
    }
  });
}

let updateTimer: number | null = null;

watch(
  () => resultStore.sortedResults,
  (newResults) => {
    if (updateTimer) clearTimeout(updateTimer);
    updateTimer = window.setTimeout(() => {
      try { updateResultMarkers(); } catch (e) { console.error(e); } finally { updateTimer = null; }
    }, 300);
  },
  { immediate: false, deep: false }
);

watch(
  () => mapStore.isMapLoaded,
  (loaded) => { if (loaded) setTimeout(() => updateResultMarkers(), 500); },
  { immediate: false }
);

onMounted(() => {
  if (mapStore.isMapLoaded) setTimeout(() => updateResultMarkers(), 500);
});

onUnmounted(() => {
  if (updateTimer) { clearTimeout(updateTimer); updateTimer = null; }
  markers.forEach(m => { try { m.remove(); } catch {} });
  markers = [];
});
</script>

<style scoped>
/* Marker styles controlled via inline style */
</style>
