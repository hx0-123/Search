<!--
  Trajectory Layer Component
  Draws user trajectory on the map
-->
<template>
  <!-- This component renders via map store and map instance, no template needed -->
</template>

<script setup lang="ts">
import { watch, onMounted, onUnmounted } from 'vue';
import mapboxgl from 'mapbox-gl';
import { useMapStore } from '@/stores/map.store';

const mapStore = useMapStore();

let sourceId = 'user-trajectory';
let layerId = 'user-trajectory-layer';
let pointsSourceId = 'user-trajectory-points';
let pointsLayerId = 'user-trajectory-points-layer';

function updateTrajectoryLayer() {
  const map = mapStore.mapInstance;
  if (!map || !mapStore.isMapLoaded) return;
  
  const coordinates = mapStore.trajectoryCoordinates;
  
  // Get or create trajectory line source
  let source = map.getSource(sourceId) as mapboxgl.GeoJSONSource;
  
  if (!source) {
    // Create trajectory line source
    map.addSource(sourceId, {
      type: 'geojson',
      data: {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates: [],
        },
      },
    });
    
    source = map.getSource(sourceId) as mapboxgl.GeoJSONSource;
    
    // Create trajectory line layer (orange line)
    map.addLayer({
      id: layerId,
      type: 'line',
      source: sourceId,
      layout: {
        'line-join': 'round',
        'line-cap': 'round',
      },
      paint: {
        'line-color': '#f59e0b', // Orange
        'line-width': 3,
        'line-opacity': 0.8,
      },
    });
    
    // Create trajectory point source (yellow markers)
    map.addSource(pointsSourceId, {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features: [],
      },
    });
    
    // Create trajectory point layer (yellow circles)
    map.addLayer({
      id: pointsLayerId,
      type: 'circle',
      source: pointsSourceId,
      paint: {
        'circle-color': '#fbbf24', // Yellow
        'circle-radius': 6,
        'circle-stroke-width': 2,
        'circle-stroke-color': '#ffffff',
      },
    });
  }
  
  // Update trajectory line data
  if (coordinates.length > 0) {
    const lineCoordinates = coordinates.length === 1 
      ? [coordinates[0], coordinates[0]] 
      : coordinates;
    
    source.setData({
      type: 'Feature',
      geometry: {
        type: 'LineString',
        coordinates: lineCoordinates,
      },
      properties: {
        pointCount: coordinates.length,
      },
    });
    
    // Update trajectory point data (yellow markers)
    const pointsSource = map.getSource(pointsSourceId) as mapboxgl.GeoJSONSource;
    if (pointsSource) {
      pointsSource.setData({
        type: 'FeatureCollection',
        features: coordinates.map((coord, index) => ({
          type: 'Feature',
          geometry: {
            type: 'Point',
            coordinates: coord,
          },
          properties: {
            index,
            timestamp: mapStore.userTrajectory[index]?.timestamp || Date.now(),
          },
        })),
      });
    }
  } else {
    source.setData({
      type: 'Feature',
      geometry: {
        type: 'LineString',
        coordinates: [],
      },
    });
    
    const pointsSource = map.getSource(pointsSourceId) as mapboxgl.GeoJSONSource;
    if (pointsSource) {
      pointsSource.setData({
        type: 'FeatureCollection',
        features: [],
      });
    }
  }
}

// Watch trajectory length changes to update layer when new points are added
let lastTrajectoryLength = 0;
let updateTimer: number | null = null;

function debouncedUpdateTrajectoryLayer() {
  if (updateTimer) {
    cancelAnimationFrame(updateTimer);
  }
  updateTimer = requestAnimationFrame(() => {
    updateTrajectoryLayer();
    updateTimer = null;
  });
}

// Watch trajectory length changes (only when length changes, not on every computed recalculation)
watch(
  () => mapStore.userTrajectory.length,
  (newLength) => {
    if (newLength !== lastTrajectoryLength) {
      lastTrajectoryLength = newLength;
      debouncedUpdateTrajectoryLayer();
    }
  },
  { immediate: false }
);

// Watch map loading
watch(
  () => mapStore.isMapLoaded,
  (loaded) => {
    if (loaded) {
      setTimeout(() => {
        debouncedUpdateTrajectoryLayer();
      }, 1000);
    }
  },
  { immediate: false }
);

onMounted(() => {
  // Initialize length
  lastTrajectoryLength = mapStore.userTrajectory.length;
  
  // Defer initial update
  setTimeout(() => {
    if (mapStore.isMapLoaded) {
      debouncedUpdateTrajectoryLayer();
    }
  }, 2000);
});

onUnmounted(() => {
  const map = mapStore.mapInstance;
  if (map) {
    if (map.getLayer(layerId)) {
      map.removeLayer(layerId);
    }
    if (map.getLayer(pointsLayerId)) {
      map.removeLayer(pointsLayerId);
    }
    if (map.getSource(sourceId)) {
      map.removeSource(sourceId);
    }
    if (map.getSource(pointsSourceId)) {
      map.removeSource(pointsSourceId);
    }
  }
});
</script>

