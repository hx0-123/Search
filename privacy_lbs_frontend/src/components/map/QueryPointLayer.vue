<!--
  查询点图层组件
  在地图上绘制查询点
-->
<template>
  <!-- 此组件通过地图store和地图实例来渲染，不需要模板 -->
</template>

<script setup lang="ts">
import { watch, onMounted, onUnmounted } from 'vue';
import mapboxgl from 'mapbox-gl';
import { useMapStore } from '@/stores/map.store';
import { useQueryStore } from '@/stores/query.store';

const mapStore = useMapStore();
const queryStore = useQueryStore();

let marker: mapboxgl.Marker | null = null;

function updateQueryPoint() {
  const map = mapStore.mapInstance;
  if (!map || !mapStore.isMapLoaded) return;
  
  const location = queryStore.currentLocation;
  
  // 移除旧标记
  if (marker) {
    marker.remove();
    marker = null;
  }
  
  // 添加新标记
  if (location.longitude && location.latitude) {
    marker = new mapboxgl.Marker({
      color: '#3b82f6',
      draggable: true,
    })
      .setLngLat([location.longitude, location.latitude])
      .addTo(map);
    
    // 监听拖拽事件
    marker.on('dragend', () => {
      const lngLat = marker!.getLngLat();
      queryStore.setCurrentLocation({
        longitude: lngLat.lng,
        latitude: lngLat.lat,
      });
    });
  }
}

// 监听位置变化
watch(
  () => queryStore.currentLocation,
  () => {
    updateQueryPoint();
  },
  { deep: true }
);

// 监听地图加载
watch(
  () => mapStore.isMapLoaded,
  (loaded) => {
    if (loaded) {
      updateQueryPoint();
    }
  }
);

onMounted(() => {
  if (mapStore.isMapLoaded) {
    updateQueryPoint();
  }
});

onUnmounted(() => {
  if (marker) {
    marker.remove();
    marker = null;
  }
});
</script>

