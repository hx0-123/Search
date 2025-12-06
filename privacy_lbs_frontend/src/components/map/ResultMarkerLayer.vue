<!--
  结果标记图层组件
  在地图上绘制Top-K查询结果
-->
<template>
  <!-- 此组件通过地图store和地图实例来渲染，不需要模板 -->
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed } from 'vue';
import mapboxgl from 'mapbox-gl';
import { useMapStore } from '@/stores/map.store';
import { useResultStore } from '@/stores/result.store';
import { clusterResults, shouldCluster } from '@/utils/cluster.util';
import type { QueryResult } from '@/types';
import type { ClusterPoint } from '@/utils/cluster.util';

const mapStore = useMapStore();
const resultStore = useResultStore();

const markers = ref<mapboxgl.Marker[]>([]);
const popups = ref<mapboxgl.Popup[]>([]);
const useClustering = ref(true); // 是否启用聚类

// 计算是否应该使用聚类
const shouldUseClustering = computed(() => {
  if (!mapStore.mapInstance) return false;
  return shouldCluster(
    resultStore.sortedResults.length,
    mapStore.mapInstance.getZoom()
  );
});

function updateResultMarkers() {
  const map = mapStore.mapInstance;
  if (!map || !mapStore.isMapLoaded) return;
  
  // 清除旧标记
  clearMarkers();
  
  const results = resultStore.sortedResults;
  const zoom = map.getZoom();
  
  // 决定是否使用聚类
  const enableClustering = useClustering.value && shouldUseClustering.value;
  const displayPoints = enableClustering
    ? clusterResults(results, zoom)
    : results.map(result => ({
        id: result.id,
        longitude: result.spatialObject.location.longitude,
        latitude: result.spatialObject.location.latitude,
        result: result,
      }));
  
  // 创建新标记
  displayPoints.forEach((point, index) => {
    const isCluster = 'count' in point && point.count !== undefined;
    
    if (isCluster) {
      // 创建聚类标记
      const cluster = point as ClusterPoint;
      const [lng, lat] = [cluster.longitude, cluster.latitude];
      
      const marker = new mapboxgl.Marker({
        color: '#f59e0b',
        scale: 1.2,
      })
        .setLngLat([lng, lat])
        .addTo(map);
      
      // 创建聚类弹出窗口
      const popup = new mapboxgl.Popup({ offset: 25 })
        .setHTML(`
          <div class="cluster-popup">
            <h4>聚类点</h4>
            <p>包含 <strong>${cluster.count}</strong> 个结果</p>
            <p>点击查看详情</p>
          </div>
        `);
      
      marker.setPopup(popup);
      
      // 点击聚类时放大地图
      marker.getElement().addEventListener('click', () => {
        map.flyTo({
          center: [lng, lat],
          zoom: Math.min(zoom + 2, 18),
          duration: 500,
        });
      });
      
      markers.value.push(marker);
    } else {
      // 创建普通结果标记
      const result = (point as ClusterPoint).result!;
      if (!result) return;
      
      const { spatialObject } = result;
      const [lng, lat] = [spatialObject.location.longitude, spatialObject.location.latitude];
      
      // 判断是否为选中的结果
      const isSelected = result.id === resultStore.selectedResult?.id;
      
      // 创建标记（选中时使用不同颜色）
      const marker = new mapboxgl.Marker({
        color: isSelected ? '#409eff' : '#10b981',
        scale: isSelected ? 1.0 : 0.8,
      })
        .setLngLat([lng, lat])
        .addTo(map);
      
      // 创建弹出窗口
      const popup = new mapboxgl.Popup({ offset: 25 })
        .setHTML(`
          <div class="result-popup">
            <h4>${spatialObject.name}</h4>
            <p>${spatialObject.description || ''}</p>
            <p><strong>评分:</strong> ${result.score.toFixed(2)}</p>
            <p><strong>距离:</strong> ${(result.distance / 1000).toFixed(2)}km</p>
            <p><strong>排名:</strong> ${index + 1}</p>
          </div>
        `);
      
      marker.setPopup(popup);
      
      // 点击标记时选中结果，并高亮地图上的位置
      marker.getElement().addEventListener('click', () => {
        resultStore.setSelectedResult(result);
        // 移动地图到该位置
        map.flyTo({
          center: [lng, lat],
          zoom: Math.max(map.getZoom(), 14),
          duration: 500,
        });
      });
      
      markers.value.push(marker);
    }
  });
}

function clearMarkers() {
  markers.value.forEach(marker => marker.remove());
  popups.value.forEach(popup => popup.remove());
  markers.value = [];
  popups.value = [];
}

// 监听结果变化
watch(
  () => resultStore.sortedResults,
  () => {
    updateResultMarkers();
  },
  { deep: true }
);

// 监听地图缩放变化，重新计算聚类
watch(
  () => mapStore.mapInstance?.getZoom(),
  () => {
    if (mapStore.isMapLoaded && shouldUseClustering.value) {
      updateResultMarkers();
    }
  }
);

// 监听选中结果变化，更新标记高亮
watch(
  () => resultStore.selectedResult,
  (selectedResult) => {
    if (!mapStore.mapInstance || !mapStore.isMapLoaded) return;
    
    // 重新绘制标记以更新高亮状态
    updateResultMarkers();
  },
  { deep: true }
);

// 监听地图加载
watch(
  () => mapStore.isMapLoaded,
  (loaded) => {
    if (loaded) {
      updateResultMarkers();
    }
  }
);

onMounted(() => {
  if (mapStore.isMapLoaded) {
    updateResultMarkers();
  }
});

onUnmounted(() => {
  clearMarkers();
});
</script>

<style>
.result-popup {
  min-width: 200px;
}

.result-popup h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
}

.result-popup p {
  margin: 4px 0;
  font-size: 14px;
  color: #666;
}

.cluster-popup {
  min-width: 150px;
  text-align: center;
}

.cluster-popup h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #f59e0b;
}

.cluster-popup p {
  margin: 4px 0;
  font-size: 14px;
  color: #666;
}
</style>

