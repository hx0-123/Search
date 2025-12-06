<!--
  轨迹图层组件
  在地图上绘制用户轨迹
-->
<template>
  <!-- 此组件通过地图store和地图实例来渲染，不需要模板 -->
</template>

<script setup lang="ts">
import { watch, onMounted, onUnmounted } from 'vue';
import mapboxgl from 'mapbox-gl';
import { useMapStore } from '@/stores/map.store';

const mapStore = useMapStore();

let sourceId = 'user-trajectory';
let layerId = 'user-trajectory-layer';

function updateTrajectoryLayer() {
  const map = mapStore.mapInstance;
  if (!map || !mapStore.isMapLoaded) return;
  
  const coordinates = mapStore.trajectoryCoordinates;
  
  // 获取或创建数据源
  let source = map.getSource(sourceId) as mapboxgl.GeoJSONSource;
  
  if (!source) {
    // 创建数据源
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
    
    // 创建图层
    map.addLayer({
      id: layerId,
      type: 'line',
      source: sourceId,
      layout: {
        'line-join': 'round',
        'line-cap': 'round',
      },
      paint: {
        'line-color': '#f59e0b',
        'line-width': 3,
        'line-opacity': 0.8,
      },
    });
  }
  
  // 更新数据 - 绘制历史位置点数组作为轨迹线
  if (coordinates.length > 0) {
    // 如果只有一个点，创建一个包含该点的线段
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
  } else {
    source.setData({
      type: 'Feature',
      geometry: {
        type: 'LineString',
        coordinates: [],
      },
    });
  }
}

// 监听轨迹变化
watch(
  () => mapStore.trajectoryCoordinates,
  () => {
    updateTrajectoryLayer();
  },
  { deep: true }
);

// 监听地图加载
watch(
  () => mapStore.isMapLoaded,
  (loaded) => {
    if (loaded) {
      updateTrajectoryLayer();
    }
  }
);

onMounted(() => {
  if (mapStore.isMapLoaded) {
    updateTrajectoryLayer();
  }
});

onUnmounted(() => {
  const map = mapStore.mapInstance;
  if (map && map.getLayer(layerId)) {
    map.removeLayer(layerId);
  }
  if (map && map.getSource(sourceId)) {
    map.removeSource(sourceId);
  }
});
</script>

