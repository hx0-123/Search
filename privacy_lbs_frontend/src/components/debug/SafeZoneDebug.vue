<template>
  <div style="position: fixed; bottom: 20px; right: 20px; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); z-index: 1000; max-width: 300px;">
    <h4 style="margin: 0 0 10px 0; font-size: 14px; font-weight: bold;">🔍 Safe Zone Debug</h4>
    
    <div style="margin-bottom: 10px; font-size: 12px;">
      <strong>Store Status:</strong><br>
      <span v-if="queryStore.safeZone">
        ✅ Safe Zone Data<br>
        Center: {{ queryStore.safeZone.center.longitude.toFixed(4) }}, {{ queryStore.safeZone.center.latitude.toFixed(4) }}<br>
        Radius: {{ queryStore.safeZone.radius }}m
      </span>
      <span v-else style="color: #999;">❌ No safe zone data</span>
    </div>
    
    <div style="margin-bottom: 10px; font-size: 12px;">
      <strong>Event Trigger Count:</strong> {{ eventCount }}
    </div>
    
    <div style="margin-bottom: 10px; font-size: 12px;">
      <strong>Listener Count:</strong> {{ listenerCount }}
    </div>
    
    <div style="margin-bottom: 10px; font-size: 12px;">
      <strong>Test Status:</strong> {{ testStatus }}
    </div>
    
    <button 
      @click="testDirectCall" 
      style="width: 100%; padding: 8px; background: #10b981; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; margin-bottom: 5px;"
    >
      🎯 Direct Call Test (HTML Marker)
    </button>
    
    <button 
      @click="testManualTrigger" 
      :disabled="isTestRunning"
      style="width: 100%; padding: 8px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; margin-bottom: 5px;"
    >
      {{ isTestRunning ? '⏳ Manual Trigger Test: Running...' : '🧪 Manual Trigger Test' }}
    </button>
    
    <button 
      @click="clearSafeZone" 
      style="width: 100%; padding: 8px; background: #ef4444; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;"
    >
      🗑️ Clear the safe zone
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import mapboxgl from 'mapbox-gl';
import { useQueryStore } from '@/stores/query.store';
import { useMapStore } from '@/stores/map.store';
import { eventBus, Events } from '@/utils/event-bus';

const queryStore = useQueryStore();
const mapStore = useMapStore();
const eventCount = ref(0);
const listenerCount = ref(0);
const testStatus = ref('Not Tested');
const isTestRunning = ref(false);

// Update listener count
const updateListenerCount = () => {
  listenerCount.value = eventBus.getListenerCount(Events.SAFE_ZONE_UPDATED);
};

const handleSafeZoneUpdate = (data: any) => {
  eventCount.value++;
  console.log('[SafeZoneDebug] Event received:', data);
};

// Directly call map operations, use HTML Marker (not dependent on GPU)
let testMarker: any = null;

const testDirectCall = async () => {
  testStatus.value = 'Direct Call Test: Start...';
  console.log('[SafeZoneDebug] === Direct Call Test (HTML Marker) ===');
  
  await new Promise(resolve => setTimeout(resolve, 100));
  
  const map = mapStore.mapInstance;
  if (!map) {
    testStatus.value = '❌ Map not loaded';
    console.error('[SafeZoneDebug] Map not loaded');
    return;
  }
  
  testStatus.value = 'Direct Call Test: Create HTML Marker...';
  console.log('[SafeZoneDebug] Map exists, creating HTML marker...');
  
  try {
    // Clean up old marker
    if (testMarker) {
      testMarker.remove();
      testMarker = null;
    }
    
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Create HTML element (not dependent on WebGL/GPU)
    const el = document.createElement('div');
    el.style.width = '200px';
    el.style.height = '200px';
    el.style.borderRadius = '50%';
    el.style.backgroundColor = 'rgba(16, 185, 129, 0.3)';
    el.style.border = '3px solid rgba(16, 185, 129, 0.8)';
    el.style.pointerEvents = 'none';
    
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Create Marker (using HTML, not dependent on GPU)
    testMarker = new mapboxgl.Marker({
      element: el,
      anchor: 'center',
    })
      .setLngLat([queryStore.currentLocation.longitude, queryStore.currentLocation.latitude])
      .addTo(map);
    
    testStatus.value = '✅ Direct Call Test: Success';
    console.log('[SafeZoneDebug] Direct test successful (HTML Marker)');
  } catch (error) {
    testStatus.value = '❌ Direct Call Test Failed: ' + error;
    console.error('[SafeZoneDebug] Direct test error:', error);
  }
};

const testManualTrigger = async () => {
  if (isTestRunning.value) return;
  
  isTestRunning.value = true;
  testStatus.value = 'Manual Trigger Test: Start...';
  console.log('[SafeZoneDebug] === Manual Trigger Start ===');
  
  await new Promise(resolve => setTimeout(resolve, 200));
  
  testStatus.value = 'Manual Trigger Test: Read Current Location...';
  console.log('[SafeZoneDebug] Current location:', queryStore.currentLocation);
  
  await new Promise(resolve => setTimeout(resolve, 200));
  
  testStatus.value = 'Manual Trigger Test: Prepare Data...';
  const testData = {
    center: {
      longitude: queryStore.currentLocation.longitude,
      latitude: queryStore.currentLocation.latitude,
    },
    radius: 1000,
  };
  console.log('[SafeZoneDebug] Test data prepared:', testData);
  
  await new Promise(resolve => setTimeout(resolve, 200));
  
  testStatus.value = 'Manual Trigger Test: Update Store...';
  console.log('[SafeZoneDebug] About to call setSafeZone...');
  
  // Instead of calling setSafeZone directly, modify store value directly
  // Avoid issues caused by triggering events
  try {
    // Set value directly without triggering events
    queryStore.safeZone = testData;
    console.log('[SafeZoneDebug] Store updated directly');
    
    await new Promise(resolve => setTimeout(resolve, 200));
    
    testStatus.value = 'Manual Trigger Test: Trigger Event Manual...';
    console.log('[SafeZoneDebug] About to emit event...');
    console.log('[SafeZoneDebug] Event name:', Events.SAFE_ZONE_UPDATED);
    console.log('[SafeZoneDebug] Event data:', testData);
    
    // Check if there are listeners
    console.log('[SafeZoneDebug] Checking event bus...');
    
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Manually trigger event
    console.log('[SafeZoneDebug] Calling eventBus.emit...');
    eventBus.emit(Events.SAFE_ZONE_UPDATED, testData);
    console.log('[SafeZoneDebug] eventBus.emit returned');
    
    await new Promise(resolve => setTimeout(resolve, 500));
    
    testStatus.value = '✅ Manual Trigger Test: Success';
    console.log('[SafeZoneDebug] === Manual Trigger End ===');
  } catch (error) {
    testStatus.value = '❌ Error: ' + error;
    console.error('[SafeZoneDebug] Error:', error);
  }
  
  setTimeout(() => {
    isTestRunning.value = false;
  }, 1000);
};

const clearSafeZone = () => {
  console.log('[SafeZoneDebug] Clearing safe zone');
  testStatus.value = '✅ Clear Safe Zone: Success';
  queryStore.safeZone = null;
};

onMounted(() => {
  console.log('[SafeZoneDebug] Mounted, subscribing to events');
  console.log('[SafeZoneDebug] Current listeners:', eventBus.getAllListeners());
  
  eventBus.on(Events.SAFE_ZONE_UPDATED, handleSafeZoneUpdate);
  
  updateListenerCount();
  console.log('[SafeZoneDebug] After subscription, listener count:', listenerCount.value);
  
  // Periodically update listener count
  const interval = setInterval(updateListenerCount, 1000);
  
  // Cleanup timer
  onUnmounted(() => {
    clearInterval(interval);
  });
});

onUnmounted(() => {
  console.log('[SafeZoneDebug] Unmounting, unsubscribing from events');
  eventBus.off(Events.SAFE_ZONE_UPDATED, handleSafeZoneUpdate);
  updateListenerCount();
});
</script>

