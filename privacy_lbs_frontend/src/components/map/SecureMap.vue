<!--
  核心地图容器组件
  负责地图的初始化、基础交互和图层管理
-->
<template>
  <div class="secure-map-container" ref="mapContainer">
    <!-- 地图控件 -->
    <div class="map-controls" v-if="mapLoaded">
      <el-button-group>
        <el-button :icon="ZoomIn" @click="zoomIn" size="small" circle />
        <el-button :icon="ZoomOut" @click="zoomOut" size="small" circle />
        <el-button :icon="Refresh" @click="resetView" size="small" circle />
      </el-button-group>
    </div>
    
    <!-- 地图图例 -->
    <div class="map-legend" v-if="mapLoaded">
      <div class="legend-item">
        <span class="legend-color" style="background: #3b82f6;"></span>
        <span>查询点</span>
      </div>
      <div class="legend-item">
        <span class="legend-color" style="background: #10b981;"></span>
        <span>结果点</span>
      </div>
      <div class="legend-item">
        <span class="legend-color" style="background: #f59e0b;"></span>
        <span>用户轨迹</span>
      </div>
      <div class="legend-item" v-if="hasSafeZone">
        <span class="legend-color" style="background: #ef4444;"></span>
        <span>安全区域</span>
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
// 注意：图层组件在HomeView中作为子组件注册，这里不需要导入
// 它们通过mapStore共享地图实例

const props = defineProps<{
  initialCenter?: [number, number];
  initialZoom?: number;
}>();

const mapStore = useMapStore();
const mapContainer = ref<HTMLElement>();
const mapLoaded = ref(false);
let map: mapboxgl.Map | null = null;

const hasSafeZone = computed(() => mapStore.safeZone !== null);

onMounted(() => {
  console.log('SecureMap 组件已挂载');
  console.log('Mapbox Token:', env.mapboxToken ? '已配置' : '未配置');
  
  if (!mapContainer.value) {
    console.error('地图容器元素不存在');
    return;
  }
  
  // 设置Mapbox访问令牌
  mapboxgl.accessToken = env.mapboxToken;
  
  if (!mapboxgl.accessToken || mapboxgl.accessToken === 'pk.your_mapbox_token_here') {
    console.error('Mapbox访问令牌未配置');
    const errorInfo = handleMapError(new Error('Mapbox访问令牌未配置'));
    showError(errorInfo, true);
    // 即使没有Token，也显示一个占位符
    if (mapContainer.value) {
      mapContainer.value.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; height: 100%; background: #f5f5f5; color: #666;">
          <div style="text-align: center;">
            <h3>地图加载失败</h3>
            <p>请配置 Mapbox 访问令牌</p>
            <p style="font-size: 12px; color: #999;">在 .env.development 中设置 VITE_MAPBOX_ACCESS_TOKEN</p>
          </div>
        </div>
      `;
    }
    return;
  }
  
  try {
    // 初始化地图
    map = new mapboxgl.Map({
      container: mapContainer.value,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: props.initialCenter || mapStore.center,
      zoom: props.initialZoom || mapStore.zoom,
      antialias: true,
    });
    
    // 监听地图错误
    map.on('error', (e) => {
      const errorInfo = handleMapError(e.error || e);
      showError(errorInfo, true);
    });
  } catch (error: any) {
    const errorInfo = handleMapError(error);
    showError(errorInfo, true);
    return;
  }
  
  // 添加导航控件
  map.addControl(new mapboxgl.NavigationControl(), 'top-right');
  
  // 添加全屏控件
  map.addControl(new mapboxgl.FullscreenControl(), 'top-right');
  
  // 地图加载完成
  map.on('load', () => {
    mapLoaded.value = true;
    mapStore.setMapInstance(map!);
    
    // 地图加载完成后，确保所有图层组件能够正确初始化
    // 图层组件会通过watch监听isMapLoaded状态来自动初始化
    console.log('地图加载完成，图层组件可以开始初始化');
  });
  
  // 监听地图移动
  map.on('move', () => {
    if (map) {
      const center = map.getCenter();
      mapStore.setCenter(center.lng, center.lat);
      mapStore.setZoom(map.getZoom());
    }
  });
});

onUnmounted(() => {
  if (map) {
    map.remove();
    map = null;
  }
});

// 缩放控制
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
  if (map) {
    map.flyTo({
      center: mapStore.center,
      zoom: mapStore.zoom,
      duration: 1000,
    });
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

