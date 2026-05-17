/**
 * Map State Management
 * Manage map-related state including map instance, layers, views, etc.
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { SpatialObject, TrajectoryPoint, SafeZone } from '@/types';
import mapboxgl from 'mapbox-gl';

export const useMapStore = defineStore('map', () => {
  // Map instance
  const mapInstance = ref<mapboxgl.Map | null>(null);
  
  // Map center point
  const center = ref<[number, number]>([116.4074, 39.9042]); // Default: Beijing
  
  // Map zoom level
  const zoom = ref<number>(12);
  
  // User trajectory
  const userTrajectory = ref<TrajectoryPoint[]>([]);
  
  // Safe zone
  const safeZone = ref<SafeZone | null>(null);
  
  // Currently selected spatial object
  const selectedObject = ref<SpatialObject | null>(null);
  
  // Whether map is loaded
  const isMapLoaded = ref<boolean>(false);
  
  // Current view state (for saving and restoring view)
  const currentView = computed(() => ({
    center: center.value,
    zoom: zoom.value,
  }));
  
  // Computed property: Trajectory coordinates array
  const trajectoryCoordinates = computed<[number, number][]>(() => {
    return userTrajectory.value.map(point => [
      point.longitude,
      point.latitude,
    ]);
  });
  
  // Computed property: Whether has trajectory data
  const hasTrajectory = computed(() => {
    return userTrajectory.value.length > 0;
  });
  
  /**
   * Set map instance
   */
  function setMapInstance(map: mapboxgl.Map) {
    mapInstance.value = map;
    // Force set as loaded since setMapInstance is only called after map 'load' event
    isMapLoaded.value = true;
  }
  
  // Flag to prevent infinite loops between map events and store updates
  // CRITICAL: Use a more robust flag management system
  let isUpdatingFromMap = false;
  let updateTimer: number | null = null;
  
  /**
   * Update map center point
   */
  function setCenter(lng: number, lat: number, skipMapUpdate = false) {
    // Always update the store value first
    center.value = [lng, lat];
    
    // If skipMapUpdate is true, don't update the map (called from map move event)
    if (skipMapUpdate) {
      return;
    }
    
    // If already updating from map, don't trigger another update
    if (isUpdatingFromMap) {
      console.log('[map.store] Skipping setCenter - already updating from map');
      return;
    }
    
    // If no map instance, nothing to do
    if (!mapInstance.value) {
      console.log('[map.store] Skipping setCenter - no map instance');
      return;
    }
    
    // Clear any pending update timer
    if (updateTimer) {
      cancelAnimationFrame(updateTimer);
      updateTimer = null;
    }
    
    console.log(`[map.store] setCenter called: ${lng}, ${lat}`);
    
    // CRITICAL FIX: Don't set isUpdatingFromMap flag here
    // This was causing the map to become unresponsive
    // The flag should only be set when responding to map move events
    
    // Use requestAnimationFrame to defer map updates
    updateTimer = requestAnimationFrame(() => {
      if (!mapInstance.value) {
        updateTimer = null;
        return;
      }
      
      try {
        const currentCenter = mapInstance.value.getCenter();
        
        // Only update if actually different (with small tolerance)
        const centerDiff = Math.abs(currentCenter.lng - lng) + Math.abs(currentCenter.lat - lat);
        if (centerDiff > 0.0001) {
          console.log(`[map.store] Flying to: ${lng}, ${lat}`);
          mapInstance.value.flyTo({
            center: [lng, lat],
            duration: 800,
          });
        } else {
          console.log('[map.store] Center unchanged, skipping flyTo');
        }
      } catch (error) {
        console.warn('[map.store.setCenter] Error updating map center:', error);
      } finally {
          updateTimer = null;
      }
    });
  }
  
  /**
   * Update map zoom level
   */
  function setZoom(level: number, skipMapUpdate = false) {
    // Always update the store value first
    zoom.value = level;
    
    // If skipMapUpdate is true, don't update the map (called from map move event)
    if (skipMapUpdate) {
      return;
    }
    
    // If already updating from map, don't trigger another update
    if (isUpdatingFromMap) {
      console.log('[map.store] Skipping setZoom - already updating from map');
      return;
    }
    
    // If no map instance, nothing to do
    if (!mapInstance.value) {
      console.log('[map.store] Skipping setZoom - no map instance');
      return;
    }
    
    // Clear any pending update timer
    if (updateTimer) {
      cancelAnimationFrame(updateTimer);
      updateTimer = null;
    }
    
    console.log(`[map.store] setZoom called: ${level}`);
    
    // CRITICAL FIX: Don't set isUpdatingFromMap flag here
    // This was causing the map to become unresponsive
    
    // Use requestAnimationFrame to defer map updates
    updateTimer = requestAnimationFrame(() => {
      if (!mapInstance.value) {
        updateTimer = null;
        return;
      }
      
      try {
        // Only update if actually different
        const currentZoom = mapInstance.value.getZoom();
        if (Math.abs(currentZoom - level) > 0.01) {
          console.log(`[map.store] Zooming to: ${level}`);
          mapInstance.value.flyTo({
            zoom: level,
            duration: 500,
          });
        } else {
          console.log('[map.store] Zoom unchanged, skipping flyTo');
        }
      } catch (error) {
        console.warn('[map.store.setZoom] Error updating map zoom:', error);
      } finally {
          updateTimer = null;
      }
    });
  }
  
  /**
   * Add trajectory point
   */
  function addTrajectoryPoint(point: TrajectoryPoint) {
    userTrajectory.value.push(point);
  }
  
  /**
   * Clear trajectory
   */
  function clearTrajectory() {
    userTrajectory.value = [];
  }
  
  /**
   * Set safe zone
   */
  function setSafeZone(zone: SafeZone | null) {
    safeZone.value = zone;
  }
  
  /**
   * Set selected spatial object
   */
  function setSelectedObject(object: SpatialObject | null) {
    selectedObject.value = object;
    if (object && mapInstance.value) {
      // Move to selected object position
      setCenter(object.location.longitude, object.location.latitude);
    }
  }
  
  /**
   * Reset map state
   */
  function reset() {
    center.value = [116.4074, 39.9042];
    zoom.value = 12;
    userTrajectory.value = [];
    safeZone.value = null;
    selectedObject.value = null;
    // Reset update flag
    isUpdatingFromMap = false;
    if (updateTimer) {
      cancelAnimationFrame(updateTimer);
      updateTimer = null;
    }
  }
  
  /**
   * Check if updating from map event (for debugging)
   */
  function isUpdatingFromMapEvent(): boolean {
    return isUpdatingFromMap;
  }
  
  return {
    // State
    mapInstance,
    center,
    zoom,
    userTrajectory,
    safeZone,
    selectedObject,
    isMapLoaded,
    // Computed properties
    trajectoryCoordinates,
    hasTrajectory,
    currentView, // Export current view state
    // Methods
    setMapInstance,
    setCenter,
    setZoom,
    addTrajectoryPoint,
    clearTrajectory,
    setSafeZone,
    setSelectedObject,
    reset,
    isUpdatingFromMapEvent, // Export for debugging
  };
});

