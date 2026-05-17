<!--
  Core Map Container Component
  Responsible for map initialization, basic interactions and layer management
-->
<template>
  <div class="secure-map-container" ref="mapContainer">
    <!-- Map Controls -->
    <div class="map-controls" v-if="mapLoaded">
      <el-button-group>
        <el-button :icon="ZoomIn" @click="zoomIn" size="small" circle />
        <el-button :icon="ZoomOut" @click="zoomOut" size="small" circle />
        <el-button :icon="Refresh" @click="resetView" size="small" circle />
      </el-button-group>
    </div>
    
    <!-- Map Legend -->
    <div class="map-legend" v-if="mapLoaded">
      <div class="legend-item">
        <span class="legend-color" style="background: #3b82f6;"></span>
        <span>Query Point</span>
      </div>
      <div class="legend-item">
        <span class="legend-color" style="background: #10b981;"></span>
        <span>Result Point</span>
      </div>
      <div class="legend-item">
        <span class="legend-color" style="background: #f59e0b;"></span>
        <span>User Trajectory</span>
      </div>
      <div class="legend-item" v-if="hasSafeZone">
        <span class="legend-color" style="background: #ef4444;"></span>
        <span>Safe Zone</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { ZoomIn, ZoomOut, Refresh } from '@element-plus/icons-vue';
import { useMapStore } from '@/stores/map.store';
import { env } from '@/config/env';
import { handleMapError, showError } from '@/utils/error-handler.util';
// Note: Layer components are registered as child components in HomeView, no need to import here
// They share the map instance through mapStore

const props = defineProps<{
  initialCenter?: [number, number];
  initialZoom?: number;
}>();

const mapStore = useMapStore();
const mapContainer = ref<HTMLElement>();
const mapLoaded = ref(false);
let map: mapboxgl.Map | null = null;
let moveTimer: number | null = null; // Map movement throttle timer
let moveEndHandler: (() => void) | null = null; // Moveend event handler
let isMapInitializing = false; // Flag to prevent multiple initializations

const hasSafeZone = computed(() => mapStore.safeZone !== null);

onMounted(() => {
  // CRITICAL: Delay map initialization significantly to allow UI to render first
  // This prevents blocking the main thread during initial page load
  // Use requestIdleCallback if available for better performance
  if ('requestIdleCallback' in window) {
    (window as any).requestIdleCallback(() => {
      initializeMap();
    }, { timeout: 1000 });
  } else {
    setTimeout(() => {
      initializeMap();
    }, 1000); // Increased delay to 1 second
  }
});

function initializeMap() {
  // Prevent multiple initializations
  if (isMapInitializing || map) {
    return;
  }
  isMapInitializing = true;
  
  // Removed excessive logging to improve performance
  
  if (!mapContainer.value) {
    setTimeout(() => {
      console.error('Map container element does not exist');
    }, 0);
    isMapInitializing = false;
    return;
  }
  
  // Set Mapbox access token
  mapboxgl.accessToken = env.mapboxToken;
  
  if (!mapboxgl.accessToken || mapboxgl.accessToken === 'pk.your_mapbox_token_here') {
    setTimeout(() => {
      console.error('Mapbox access token not configured');
    }, 0);
    const errorInfo = handleMapError(new Error('Mapbox access token not configured'));
    showError(errorInfo, true);
    // Even without Token, show a placeholder
    if (mapContainer.value) {
      mapContainer.value.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; height: 100%; background: #f5f5f5; color: #666;">
          <div style="text-align: center;">
            <h3>Map Loading Failed</h3>
            <p>Please configure Mapbox access token</p>
            <p style="font-size: 12px; color: #999;">Set VITE_MAPBOX_ACCESS_TOKEN in .env.development</p>
          </div>
        </div>
      `;
    }
    isMapInitializing = false;
    return;
  }
  
  // Use requestIdleCallback if available, otherwise setTimeout
  const initMap = () => {
    if (map) return; // Already initialized
    
    try {
      // Initialize map with performance optimizations for non-GPU systems
      // CRITICAL: Use default center/zoom, don't interact with store during init
      const defaultCenter: [number, number] = [116.4074, 39.9042];
      const defaultZoom = 12;
      
      map = new mapboxgl.Map({
        container: mapContainer.value!,
        style: 'mapbox://styles/mapbox/streets-v12',
        center: defaultCenter, // Use default, don't read from store
        zoom: defaultZoom, // Use default, don't read from store
        antialias: false, // Disable antialiasing for better performance without GPU
        renderWorldCopies: false, // Disable for better performance
        preserveDrawingBuffer: false, // Disable for better performance
        fadeDuration: 0, // Disable fade animations for instant rendering
        maxPitch: 0, // Disable 3D for better performance
      });
      
      // Listen for map errors
      map.on('error', (e) => {
        const errorInfo = handleMapError(e.error || e);
        showError(errorInfo, true);
      });
      
      // Add navigation controls (defer to avoid blocking)
      setTimeout(() => {
        if (map) {
          map.addControl(new mapboxgl.NavigationControl(), 'top-right');
        }
      }, 100);
      
      // Add fullscreen control (defer to avoid blocking)
      setTimeout(() => {
        if (map) {
          map.addControl(new mapboxgl.FullscreenControl(), 'top-right');
        }
      }, 200);
      
      // Map loaded
      map.on('load', () => {
        console.log('[SecureMap] Map load event fired');
        mapLoaded.value = true;
        
        // CRITICAL: Delay store interaction to avoid blocking
        setTimeout(() => {
          console.log('[SecureMap] Setting map instance in store');
          mapStore.setMapInstance(map!);
          isMapInitializing = false; // Reset flag after map loads
          
          // After map loads, ensure all layer components can initialize correctly
          // Layer components will auto-initialize by watching isMapLoaded state
          setTimeout(() => {
            console.log('[SecureMap] Map loaded, layer components can start initializing');
          }, 0);
        }, 100); // Delay store interaction
        
        // Note: moveend listener is DISABLED for testing
      });
      
      // Handle map errors
      map.on('error', () => {
        isMapInitializing = false; // Reset flag on error
      });
      
      // TEMPORARILY DISABLED: Comment out all move/moveend event listeners to test
      // This will help identify if move events are causing the freeze
      /*
      // CRITICAL: Use 'moveend' instead of 'move' to only update when movement completes
      // This prevents infinite loops and reduces update frequency significantly
      // Define moveend handler (but don't attach it yet)
      moveEndHandler = () => {
        if (!map) return;
        
        // CRITICAL: Check if store is currently updating map to prevent loops
        if (mapStore.isUpdatingFromMapEvent && mapStore.isUpdatingFromMapEvent()) {
          return; // Store is updating map, skip this event
        }
        
        // Use requestAnimationFrame to defer update
        if (moveTimer) {
          cancelAnimationFrame(moveTimer);
        }
        
        moveTimer = requestAnimationFrame(() => {
          if (!map) {
            moveTimer = null;
            return;
          }
          
          // Double-check flag before updating
          if (mapStore.isUpdatingFromMapEvent && mapStore.isUpdatingFromMapEvent()) {
            moveTimer = null;
            return;
          }
          
          try {
            const center = map.getCenter();
            const zoom = map.getZoom();
            
            // CRITICAL: Use skipMapUpdate=true to prevent infinite loop
            // This only updates the store, doesn't trigger map.flyTo()
            mapStore.setCenter(center.lng, center.lat, true);
            mapStore.setZoom(zoom, true);
          } catch (error) {
            console.warn('Error updating store from map moveend:', error);
          } finally {
            moveTimer = null;
          }
        });
      };
      
      // Delay adding moveend listener significantly to avoid blocking initialization
      // Wait for map to be fully loaded and stable (at least 2 seconds after initialization)
      setTimeout(() => {
        if (map && map.loaded() && moveEndHandler) {
          map.on('moveend', moveEndHandler);
        }
      }, 2000); // Wait 2 seconds after map initialization
      */
      
      // Map initialized, move events DISABLED for testing
    } catch (error: any) {
      const errorInfo = handleMapError(error);
      showError(errorInfo, true);
      return;
    }
  };
  
  // Use requestIdleCallback if available for better performance
  if ('requestIdleCallback' in window) {
    (window as any).requestIdleCallback(initMap, { timeout: 1000 });
  } else {
    setTimeout(initMap, 100);
  }
}

onUnmounted(() => {
  // Clean up timer
  if (moveTimer) {
    cancelAnimationFrame(moveTimer);
    moveTimer = null;
  }
  
  // Remove moveend listener
  if (map && moveEndHandler) {
    map.off('moveend', moveEndHandler);
    moveEndHandler = null;
  }
  
  if (map) {
    map.remove();
    map = null;
  }

  // Reset map loaded state to ensure layer components reinitialize on next page entry
  mapStore.isMapLoaded = false;
  mapStore.mapInstance = null as any;
});

// Zoom controls
function zoomIn() {
  if (map) {
    map.zoomIn();
  }
}

function zoomOut() {
  if (map) {
    map.zoomOut();
  }
}

function resetView() {
  if (map && mapStore.isMapLoaded) {
    // CRITICAL: Temporarily disable move event updates to prevent loop
    // Use direct map methods instead of store methods to avoid triggering updates
    try {
      map.flyTo({
        center: mapStore.center,
        zoom: mapStore.zoom,
        duration: 1000,
      });
      // After flyTo completes, the move event will update the store
      // The store's isUpdatingFromMap flag should handle this correctly
    } catch (error) {
      console.warn('Error resetting map view:', error);
    }
  }
}
</script>

<style scoped>
.secure-map-container {
  width: 100%;
  height: 100%;
  position: relative;
  border-radius: 8px;
  overflow: hidden;
}

.map-controls {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 10;
  background: white;
  border-radius: 8px;
  padding: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.map-legend {
  position: absolute;
  bottom: 16px;
  left: 16px;
  z-index: 10;
  background: white;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  font-size: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.legend-item:last-child {
  margin-bottom: 0;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: inline-block;
}
</style>

