<!-- Partial core code showing structure -->
<template>
  <div class="map-container" ref="mapContainer"></div>
  <!-- Map interaction controls, legend, etc. will be placed here -->
</template>

<script setup lang="ts">
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { ref, onMounted, onUnmounted, watch } from 'vue';
import type { QueryResult, SafeZone } from '@/types';

const props = defineProps<{
  initialCenter: [number, number]; // Initial center [lng, lat]
  queryResults: QueryResult[];     // Query results
  userTrajectory: [number, number][]; // User trajectory
  safeZone?: SafeZone;             // Safe zone
}>();

const mapContainer = ref<HTMLElement>();
let map: mapboxgl.Map | null = null;

onMounted(() => {
  if (!mapContainer.value) return;
  mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;

  map = new mapboxgl.Map({
    container: mapContainer.value,
    style: 'mapbox://styles/mapbox/streets-v12',
    center: props.initialCenter,
    zoom: 12
  });

  // Add navigation control
  map.addControl(new mapboxgl.NavigationControl());

  // After map loads, initialize data sources and layers
  map.on('load', () => {
    initializeDataSources();
    renderAllLayers();
  });
});

// Core function: Initialize map data sources
function initializeDataSources() {
  if (!map) return;
  // 1. Add data source for user trajectory
  if (!map.getSource('user-trajectory')) {
    map.addSource('user-trajectory', {
      type: 'geojson',
      data: {
        type: 'Feature',
        geometry: { type: 'LineString', coordinates: [] }
      }
    });
  }
  // 2. Add data source for query results (POI)
  if (!map.getSource('query-results')) {
    map.addSource('query-results', {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features: []
      }
    });
  }
  // 3. Add data source for safe zone
  if (!map.getSource('safe-zone')) {
    map.addSource('safe-zone', {
      type: 'geojson',
      data: {
        type: 'Feature',
        geometry: { type: 'Polygon', coordinates: [] }
      }
    });
  }
}

// Watch for data changes and update map display
watch(() => props.userTrajectory, (newTrajectory) => {
  updateTrajectoryOnMap(newTrajectory);
}, { deep: true });

// Update trajectory layer
function updateTrajectoryOnMap(trajectory: [number, number][]) {
  const source = map?.getSource('user-trajectory') as mapboxgl.GeoJSONSource;
  if (source) {
    source.setData({
      type: 'Feature',
      geometry: {
        type: 'LineString',
        coordinates: trajectory
      }
    });
  }
}
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 600px;
  border-radius: 8px;
  overflow: hidden;
}
</style>