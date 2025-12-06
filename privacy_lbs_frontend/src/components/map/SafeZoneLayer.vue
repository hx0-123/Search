<!--
  安全区域图层组件
  在地图上绘制安全区域
-->
<template>
  <!-- 此组件通过地图store和地图实例来渲染，不需要模板 -->
</template>

<script setup lang="ts">
import { watch, onMounted, onUnmounted } from 'vue';
import mapboxgl from 'mapbox-gl';
import { useMapStore } from '@/stores/map.store';
import { useQueryStore } from '@/stores/query.store';
import { calculateDestination } from '@/utils/coordinate.util';

const mapStore = useMapStore();
const queryStore = useQueryStore();

let sourceId = 'safe-zone';
let layerId = 'safe-zone-layer';

function updateSafeZoneLayer() {
  const map = mapStore.mapInstance;
  if (!map || !mapStore.isMapLoaded) return;
  
  const safeZone = mapStore.safeZone;
  
  // 获取或创建数据源
  let source = map.getSource(sourceId) as mapboxgl.GeoJSONSource;
  
  if (!source) {
    // 创建数据源
    map.addSource(sourceId, {
      type: 'geojson',
      data: {
        type: 'Feature',
        geometry: {
          type: 'Polygon',
          coordinates: [],
        },
      },
    });
    
    source = map.getSource(sourceId) as mapboxgl.GeoJSONSource;
    
    // 创建填充图层
    map.addLayer({
      id: layerId,
      type: 'fill',
      source: sourceId,
      paint: {
        'fill-color': '#ef4444',
        'fill-opacity': 0.2,
      },
    });
    
    // 创建边框图层
    map.addLayer({
      id: `${layerId}-border`,
      type: 'line',
      source: sourceId,
      paint: {
        'line-color': '#ef4444',
        'line-width': 2,
        'line-opacity': 0.8,
      },
    });
  }
  
  // 更新数据 - 优先使用mapStore中的安全区域，如果没有则使用queryStore中的
  const safeZoneData = safeZone || queryStore.safeZone;
  
  if (safeZoneData) {
    let polygon: [number, number][];
    
    // 如果已有多边形数据，直接使用
    if (safeZoneData.polygon && safeZoneData.polygon.length > 0) {
      polygon = safeZoneData.polygon;
    } else if (safeZoneData.radius) {
      // 如果有半径，生成圆形多边形
      const center: [number, number] = [
        safeZoneData.center.longitude,
        safeZoneData.center.latitude,
      ];
      const radius = safeZoneData.radius;
      
      // 生成圆形多边形（使用32个点）
      const points: [number, number][] = [];
      for (let i = 0; i < 32; i++) {
        const angle = (i / 32) * 360;
        const point = calculateDestination(center, radius || 1000, angle);
        points.push(point);
      }
      // 闭合多边形
      points.push(points[0]);
      polygon = points;
    } else {
      // 没有有效数据，清空
      source.setData({
        type: 'Feature',
        geometry: {
          type: 'Polygon',
          coordinates: [],
        },
      });
      return;
    }
    
    source.setData({
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [polygon],
      },
      properties: {
        name: (safeZoneData as any).name || '安全区域',
        radius: safeZoneData.radius,
      },
    });
  } else {
    source.setData({
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [],
      },
    });
  }
}

// 监听安全区域变化（同时监听mapStore和queryStore）
watch(
  () => [mapStore.safeZone, queryStore.safeZone],
  () => {
    updateSafeZoneLayer();
  },
  { deep: true }
);

// 监听地图加载
watch(
  () => mapStore.isMapLoaded,
  (loaded) => {
    if (loaded) {
      updateSafeZoneLayer();
    }
  }
);

onMounted(() => {
  if (mapStore.isMapLoaded) {
    updateSafeZoneLayer();
  }
});

onUnmounted(() => {
  const map = mapStore.mapInstance;
  if (map && map.getLayer(`${layerId}-border`)) {
    map.removeLayer(`${layerId}-border`);
  }
  if (map && map.getLayer(layerId)) {
    map.removeLayer(layerId);
  }
  if (map && map.getSource(sourceId)) {
    map.removeSource(sourceId);
  }
});
</script>

