<!-- 部分核心代码，展示结构 -->
<template>
  <div class="map-container" ref="mapContainer"></div>
  <!-- 地图交互控件、图例等将放在这里 -->
</template>

<script setup lang="ts">
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { ref, onMounted, onUnmounted, watch } from 'vue';
import type { QueryResult, SafeZone } from '@/types';

const props = defineProps<{
  initialCenter: [number, number]; // 初始中心点 [lng, lat]
  queryResults: QueryResult[];     // 查询结果
  userTrajectory: [number, number][]; // 用户轨迹
  safeZone?: SafeZone;             // 安全区域
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

  // 添加导航控件
  map.addControl(new mapboxgl.NavigationControl());

  // 地图加载完成后，初始化数据源和图层
  map.on('load', () => {
    initializeDataSources();
    renderAllLayers();
  });
});

// 核心函数：初始化地图数据源
function initializeDataSources() {
  if (!map) return;
  // 1. 为用户轨迹添加数据源
  if (!map.getSource('user-trajectory')) {
    map.addSource('user-trajectory', {
      type: 'geojson',
      data: {
        type: 'Feature',
        geometry: { type: 'LineString', coordinates: [] }
      }
    });
  }
  // 2. 为查询结果点（POI）添加数据源
  if (!map.getSource('query-results')) {
    map.addSource('query-results', {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features: []
      }
    });
  }
  // 3. 为安全区域添加数据源
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

// 监听数据变化，更新地图显示
watch(() => props.userTrajectory, (newTrajectory) => {
  updateTrajectoryOnMap(newTrajectory);
}, { deep: true });

// 更新轨迹图层
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