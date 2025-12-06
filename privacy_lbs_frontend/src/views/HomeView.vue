<!--
  主界面视图
  包含地图和侧边栏
-->
<template>
  <div class="home-view">
    <div class="main-container">
      <!-- 侧边栏 -->
      <div class="sidebar">
        <!-- 查询表单 -->
        <QueryForm />
        
        <!-- 实时更新 -->
        <RealTimeUpdate />
        
        <!-- 结果列表 -->
        <ResultList />
      </div>
      
      <!-- 地图区域 -->
      <div class="map-area">
        <SecureMap
          :initial-center="mapStore.center"
          :initial-zoom="mapStore.zoom"
        />
        
        <!-- 地图图层组件 -->
        <QueryPointLayer />
        <ResultMarkerLayer />
        <TrajectoryLayer />
        <SafeZoneLayer />
      </div>
    </div>
    
    <!-- 路线详情抽屉 -->
    <RouteDetails />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import SecureMap from '@/components/map/SecureMap.vue';
import QueryPointLayer from '@/components/map/QueryPointLayer.vue';
import ResultMarkerLayer from '@/components/map/ResultMarkerLayer.vue';
import TrajectoryLayer from '@/components/map/TrajectoryLayer.vue';
import SafeZoneLayer from '@/components/map/SafeZoneLayer.vue';
import QueryForm from '@/components/query/QueryForm.vue';
import RealTimeUpdate from '@/components/query/RealTimeUpdate.vue';
import ResultList from '@/components/results/ResultList.vue';
import RouteDetails from '@/components/results/RouteDetails.vue';
import { useMapStore } from '@/stores/map.store';
import { useQueryStore } from '@/stores/query.store';
import { useResultStore } from '@/stores/result.store';

const mapStore = useMapStore();
const queryStore = useQueryStore();
const resultStore = useResultStore();

onMounted(() => {
  console.log('HomeView 组件已挂载');
  console.log('MapStore:', mapStore);
  console.log('QueryStore:', queryStore);
  
  // 初始化：尝试获取用户位置
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        console.log('获取位置成功:', position.coords);
        mapStore.setCenter(
          position.coords.longitude,
          position.coords.latitude
        );
        queryStore.setCurrentLocation({
          longitude: position.coords.longitude,
          latitude: position.coords.latitude,
        });
      },
      (error) => {
        console.warn('获取位置失败:', error);
      }
    );
  } else {
    console.warn('浏览器不支持地理位置API');
  }
});

onUnmounted(() => {
  // 清理：取消查询
  if (queryStore.queryId) {
    queryStore.cancel();
  }
});
</script>

<style scoped>
.home-view {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.main-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.sidebar {
  width: 400px;
  min-width: 350px;
  max-width: 500px;
  height: 100%;
  overflow-y: auto;
  padding: 16px;
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
}

.map-area {
  flex: 1;
  position: relative;
  height: 100%;
  overflow: hidden;
}

/* 响应式设计 - 平板 */
@media (max-width: 1024px) and (min-width: 769px) {
  .sidebar {
    width: 350px;
    min-width: 300px;
  }
}

/* 响应式设计 - 移动端 */
@media (max-width: 768px) {
  .main-container {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    max-width: 100%;
    height: 45%;
    max-height: 50vh;
    border-right: none;
    border-bottom: 1px solid #e4e7ed;
    padding: 12px;
  }
  
  .map-area {
    height: 55%;
    min-height: 50vh;
  }
}

/* 小屏幕移动端 */
@media (max-width: 480px) {
  .sidebar {
    height: 50%;
    max-height: 50vh;
    padding: 8px;
  }
  
  .map-area {
    height: 50%;
    min-height: 50vh;
  }
}

/* 滚动条样式 */
.sidebar::-webkit-scrollbar {
  width: 6px;
}

.sidebar::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.sidebar::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.sidebar::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>

