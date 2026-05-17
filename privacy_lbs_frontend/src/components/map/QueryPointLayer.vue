<!--
  Query Point Layer Component
  Draws query point on the map
-->
<template>
  <!-- This component renders via map store and map instance, no template needed -->
</template>

<script setup lang="ts">
import { watch, onMounted, onUnmounted } from 'vue';
import mapboxgl from 'mapbox-gl';
import { useMapStore } from '@/stores/map.store';
import { useQueryStore } from '@/stores/query.store';

const mapStore = useMapStore();
const queryStore = useQueryStore();

let marker: mapboxgl.Marker | null = null;
let previousLocation: { longitude: number; latitude: number } | null = null;
let trajectoryMarkers: mapboxgl.Marker[] = []; // Store yellow trajectory markers

function updateQueryPoint() {
  const map = mapStore.mapInstance;
  if (!map || !mapStore.isMapLoaded) {
    console.log('[QueryPointLayer] Map not ready');
    return;
  }
  
  const location = queryStore.currentLocation;
  
  // Validate location
  if (!location || !location.longitude || !location.latitude) {
    console.log('[QueryPointLayer] Invalid location');
    return;
  }
  
  console.log(`[QueryPointLayer] Updating query point to: ${location.longitude}, ${location.latitude}`);
  
  // Check if location actually changed significantly
  const locationChanged = !previousLocation || 
    Math.abs(previousLocation.longitude - location.longitude) > 0.000001 ||
    Math.abs(previousLocation.latitude - location.latitude) > 0.000001;
  
  if (!locationChanged) {
    console.log('[QueryPointLayer] Location unchanged, skipping update');
    return;
  }
  
  // If location changed, save previous location and add yellow marker
  if (previousLocation) {
    try {
      const yellowMarker = new mapboxgl.Marker({
        color: '#fbbf24', // Yellow
        draggable: false,
      })
        .setLngLat([previousLocation.longitude, previousLocation.latitude])
        .addTo(map);
      
      trajectoryMarkers.push(yellowMarker);
      console.log('[QueryPointLayer] Yellow trajectory marker added');
    } catch (error) {
      console.error('Error creating yellow marker:', error);
    }
  }
  
  // Save current location as previous for next time
  previousLocation = {
    longitude: location.longitude,
    latitude: location.latitude,
  };
  
  // Remove old marker
  if (marker) {
    try {
      marker.remove();
      marker = null;
    } catch (error) {
      console.error('Error removing marker:', error);
    }
  }
  
  // Add new marker (blue)
  try {
    marker = new mapboxgl.Marker({
      color: '#3b82f6',
      draggable: true,
    })
      .setLngLat([location.longitude, location.latitude])
      .addTo(map);
    
    // Listen for drag events
    marker.on('dragend', () => {
      const lngLat = marker!.getLngLat();
      console.log(`[QueryPointLayer] Marker dragged to: ${lngLat.lng}, ${lngLat.lat}`);
      // Update location without triggering watch
      queryStore.setCurrentLocation({
        longitude: lngLat.lng,
        latitude: lngLat.lat,
      });
    });
    
    console.log('[QueryPointLayer] Blue marker created successfully');
  } catch (error) {
    console.error('Error creating blue marker:', error);
  }
  
  // CRITICAL FIX: Don't call map.flyTo() here!
  // Let the user manually pan the map or use mapStore.setCenter from other components
  // Calling flyTo here causes infinite loops with watch
}

// CRITICAL FIX: Simplified watch with strict debouncing
let locationUpdateTimer: number | null = null;

watch(
  () => [queryStore.currentLocation.longitude, queryStore.currentLocation.latitude],
  () => {
    // Clear any pending update
    if (locationUpdateTimer) {
      clearTimeout(locationUpdateTimer);
    }
    
    // Debounce update significantly
    locationUpdateTimer = window.setTimeout(() => {
      try {
        updateQueryPoint();
      } catch (error) {
        console.error('Error updating query point:', error);
      } finally {
        locationUpdateTimer = null;
      }
    }, 300); // 300ms debounce
  },
  { immediate: false }
);

// Watch map loading
watch(
  () => mapStore.isMapLoaded,
  (loaded) => {
    if (loaded) {
      console.log('[QueryPointLayer] Map loaded, updating query point');
      setTimeout(() => {
        updateQueryPoint();
      }, 500);
    }
  },
  { immediate: false }
);

onMounted(() => {
  console.log('[QueryPointLayer] Component mounted');
  
  if (mapStore.isMapLoaded) {
    setTimeout(() => {
      updateQueryPoint();
    }, 500);
  }
});

onUnmounted(() => {
  const map = mapStore.mapInstance;
  
  // Clean up blue marker
  if (marker) {
    marker.remove();
    marker = null;
  }
  
  // Clean up all yellow trajectory markers
  trajectoryMarkers.forEach(m => m.remove());
  trajectoryMarkers = [];
  
  // Clean up timer
  if (locationUpdateTimer) {
    clearTimeout(locationUpdateTimer);
    locationUpdateTimer = null;
  }
  
  console.log('[QueryPointLayer] Component unmounted, cleaned up');
});
</script>

