<!--
  Safe Zone Layer Component
  Rendered using HTML Marker, no GPU/WebGL dependency
  Supports dynamic resizing based on map zoom level
-->
<template>
  <!-- Render circle using HTML elements, no WebGL dependency -->
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import mapboxgl from 'mapbox-gl';
import { useMapStore } from '@/stores/map.store';
import { eventBus, Events } from '@/utils/event-bus';

const mapStore = useMapStore();
let currentMarker: mapboxgl.Marker | null = null;
let currentSafeZone: {
  center: { longitude: number; latitude: number };
  radius: number;
} | null = null;

/**
 * Convert meters to pixels (based on current zoom level and latitude)
 */
function metersToPixels(meters: number, latitude: number, zoom: number): number {
  // Mapbox pixel calculation formula
  // At zoom level 0, 1 pixel = 156543.03392 meters at equator
  const metersPerPixel = 156543.03392 * Math.cos(latitude * Math.PI / 180) / Math.pow(2, zoom);
  return meters / metersPerPixel;
}

/**
 * Update circle size (based on current zoom level)
 */
function updateCircleSize() {
  if (!currentMarker || !currentSafeZone) {
    return;
  }
  
  const map = mapStore.mapInstance;
  if (!map) {
    return;
  }
  
  const zoom = map.getZoom();
  const pixelRadius = metersToPixels(
    currentSafeZone.radius,
    currentSafeZone.center.latitude,
    zoom
  );
  
  // Get marker element and update size
  const el = currentMarker.getElement();
  const size = pixelRadius * 2; // Diameter
  
  el.style.width = `${size}px`;
  el.style.height = `${size}px`;
  
  console.log(`[SafeZoneLayer] Updated circle size: ${size}px (zoom: ${zoom.toFixed(2)})`);
}

/**
 * Render safe zone using HTML Marker
 * No GPU/WebGL dependency
 */
function updateSafeZoneLayer(safeZoneData?: {
  center: { longitude: number; latitude: number };
  radius?: number;
  polygon?: [number, number][];
} | null) {
  console.log('[SafeZoneLayer] === updateSafeZoneLayer START (HTML Mode) ===');
  
  const map = mapStore.mapInstance;
  if (!map || !mapStore.isMapLoaded) {
    console.log('[SafeZoneLayer] Map not ready, aborting');
    return;
  }
  
  console.log('[SafeZoneLayer] Map is ready');
  console.log('[SafeZoneLayer] Safe zone data:', safeZoneData);
  
  try {
    // Clean up old marker and zoom listener
    if (currentMarker) {
      console.log('[SafeZoneLayer] Removing old marker');
      const oldMap = mapStore.mapInstance;
      if (oldMap) oldMap.off('zoom', updateCircleSize);
      currentMarker.remove();
      currentMarker = null;
      currentSafeZone = null;
    }
    
    // Return if no data
    if (!safeZoneData || !safeZoneData.center || !safeZoneData.radius) {
      console.log('[SafeZoneLayer] No valid data');
      return;
    }
    
    console.log('[SafeZoneLayer] Creating HTML marker...');
    console.log('[SafeZoneLayer] Center:', safeZoneData.center);
    console.log('[SafeZoneLayer] Radius:', safeZoneData.radius, 'meters');
    
    // Save current safe zone data
    currentSafeZone = {
      center: safeZoneData.center,
        radius: safeZoneData.radius,
    };
    
    // Calculate initial pixel size
    const zoom = map.getZoom();
    const pixelRadius = metersToPixels(
      safeZoneData.radius,
      safeZoneData.center.latitude,
      zoom
    );
    const size = pixelRadius * 2; // Diameter
    
    console.log('[SafeZoneLayer] Initial size:', size, 'px at zoom', zoom.toFixed(2));
    
    // Create HTML element
    const el = document.createElement('div');
    el.className = 'safe-zone-marker';
    el.style.width = `${size}px`;
    el.style.height = `${size}px`;
    el.style.borderRadius = '50%';
    el.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
    el.style.border = '2px solid rgba(239, 68, 68, 0.8)';
    el.style.pointerEvents = 'none';
    el.style.transition = 'width 0.2s ease, height 0.2s ease'; // Smooth transition
    
    // Create Marker (using HTML element, no WebGL dependency)
    currentMarker = new mapboxgl.Marker({
      element: el,
      anchor: 'center',
    })
      .setLngLat([safeZoneData.center.longitude, safeZoneData.center.latitude])
      .addTo(map);
        
    // Listen to map zoom event for dynamic resizing
    map.on('zoom', updateCircleSize);
    
    console.log('[SafeZoneLayer] HTML marker created successfully');
    console.log('[SafeZoneLayer] === SUCCESS ===');
  } catch (error) {
    console.error('[SafeZoneLayer] === ERROR ===', error);
  }
}

// Event handler functions
const handleSafeZoneUpdate = (safeZoneData: any) => {
  console.log('[SafeZoneLayer] === Event Received (HTML Mode) ===');
  console.log('[SafeZoneLayer] Data:', JSON.stringify(safeZoneData));

  // Delay execution to avoid blocking
  setTimeout(() => {
    if (!mapStore.isMapLoaded || !mapStore.mapInstance) {
      console.log('[SafeZoneLayer] Map not ready, skipping update');
      return;
    }
    
    try {
      console.log('[SafeZoneLayer] Calling updateSafeZoneLayer...');
      updateSafeZoneLayer(safeZoneData);
      console.log('[SafeZoneLayer] updateSafeZoneLayer completed');
    } catch (error) {
      console.error('[SafeZoneLayer] Error in updateSafeZoneLayer:', error);
    }
  }, 100);
};

onMounted(() => {
  console.log('[SafeZoneLayer] Component mounted (HTML Mode with dynamic sizing)');
  
  // Subscribe to safe zone update event
  eventBus.on(Events.SAFE_ZONE_UPDATED, handleSafeZoneUpdate);
  
  console.log('[SafeZoneLayer] Event subscription complete');
});

onUnmounted(() => {
  console.log('[SafeZoneLayer] Component unmounting');
  
  // Unsubscribe from events
  eventBus.off(Events.SAFE_ZONE_UPDATED, handleSafeZoneUpdate);
  
  // Remove map zoom listener
  const map = mapStore.mapInstance;
  if (map) {
    map.off('zoom', updateCircleSize);
  }
  
  // Clean up marker
  if (currentMarker) {
    currentMarker.remove();
    currentMarker = null;
    currentSafeZone = null;
  }
  
  console.log('[SafeZoneLayer] Cleanup complete');
});
</script>

<style scoped>
/* Styles are inline on elements */
</style>
