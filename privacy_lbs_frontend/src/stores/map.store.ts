/**
 * 地图状态管理
 * 管理地图相关的状态，包括地图实例、图层、视图等
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { SpatialObject, TrajectoryPoint, SafeZone } from '@/types';
import mapboxgl from 'mapbox-gl';

export const useMapStore = defineStore('map', () => {
  // 地图实例
  const mapInstance = ref<mapboxgl.Map | null>(null);
  
  // 地图中心点
  const center = ref<[number, number]>([116.4074, 39.9042]); // 默认北京
  
  // 地图缩放级别
  const zoom = ref<number>(12);
  
  // 用户轨迹
  const userTrajectory = ref<TrajectoryPoint[]>([]);
  
  // 安全区域
  const safeZone = ref<SafeZone | null>(null);
  
  // 当前选中的空间对象
  const selectedObject = ref<SpatialObject | null>(null);
  
  // 地图是否已加载
  const isMapLoaded = ref<boolean>(false);
  
  // 当前视图状态（用于保存和恢复视图）
  const currentView = computed(() => ({
    center: center.value,
    zoom: zoom.value,
  }));
  
  // 计算属性：轨迹坐标数组
  const trajectoryCoordinates = computed<[number, number][]>(() => {
    return userTrajectory.value.map(point => [
      point.longitude,
      point.latitude,
    ]);
  });
  
  // 计算属性：是否有轨迹数据
  const hasTrajectory = computed(() => {
    return userTrajectory.value.length > 0;
  });
  
  /**
   * 设置地图实例
   */
  function setMapInstance(map: mapboxgl.Map) {
    mapInstance.value = map;
    map.on('load', () => {
      isMapLoaded.value = true;
    });
  }
  
  /**
   * 更新地图中心点
   */
  function setCenter(lng: number, lat: number) {
    center.value = [lng, lat];
    if (mapInstance.value) {
      mapInstance.value.flyTo({
        center: [lng, lat],
        duration: 1000,
      });
    }
  }
  
  /**
   * 更新地图缩放级别
   */
  function setZoom(level: number) {
    zoom.value = level;
    if (mapInstance.value) {
      mapInstance.value.flyTo({
        zoom: level,
        duration: 500,
      });
    }
  }
  
  /**
   * 添加轨迹点
   */
  function addTrajectoryPoint(point: TrajectoryPoint) {
    userTrajectory.value.push(point);
  }
  
  /**
   * 清空轨迹
   */
  function clearTrajectory() {
    userTrajectory.value = [];
  }
  
  /**
   * 设置安全区域
   */
  function setSafeZone(zone: SafeZone | null) {
    safeZone.value = zone;
  }
  
  /**
   * 设置选中的空间对象
   */
  function setSelectedObject(object: SpatialObject | null) {
    selectedObject.value = object;
    if (object && mapInstance.value) {
      // 移动到选中对象的位置
      setCenter(object.location.longitude, object.location.latitude);
    }
  }
  
  /**
   * 重置地图状态
   */
  function reset() {
    center.value = [116.4074, 39.9042];
    zoom.value = 12;
    userTrajectory.value = [];
    safeZone.value = null;
    selectedObject.value = null;
  }
  
  return {
    // 状态
    mapInstance,
    center,
    zoom,
    userTrajectory,
    safeZone,
    selectedObject,
    isMapLoaded,
    // 计算属性
    trajectoryCoordinates,
    hasTrajectory,
    currentView, // 导出当前视图状态
    // 方法
    setMapInstance,
    setCenter,
    setZoom,
    addTrajectoryPoint,
    clearTrajectory,
    setSafeZone,
    setSelectedObject,
    reset,
  };
});

