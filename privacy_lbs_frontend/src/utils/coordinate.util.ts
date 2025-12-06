/**
 * 坐标转换工具函数
 * 提供各种坐标系统之间的转换功能
 */

/**
 * 计算两点之间的距离（Haversine公式）
 * @param point1 第一个点 [longitude, latitude]
 * @param point2 第二个点 [longitude, latitude]
 * @returns 距离（米）
 */
export function calculateDistance(
  point1: [number, number],
  point2: [number, number]
): number {
  const R = 6371000; // 地球半径（米）
  const [lng1, lat1] = point1;
  const [lng2, lat2] = point2;
  
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lng2 - lng1);
  
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRadians(lat1)) *
      Math.cos(toRadians(lat2)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * 角度转弧度
 */
function toRadians(degrees: number): number {
  return degrees * (Math.PI / 180);
}

/**
 * 弧度转角度
 */
function toDegrees(radians: number): number {
  return radians * (180 / Math.PI);
}

/**
 * 计算两点之间的方位角（从point1到point2）
 * @param point1 起点 [longitude, latitude]
 * @param point2 终点 [longitude, latitude]
 * @returns 方位角（度，0-360）
 */
export function calculateBearing(
  point1: [number, number],
  point2: [number, number]
): number {
  const [lng1, lat1] = point1;
  const [lng2, lat2] = point2;
  
  const dLon = toRadians(lng2 - lng1);
  const lat1Rad = toRadians(lat1);
  const lat2Rad = toRadians(lat2);
  
  const y = Math.sin(dLon) * Math.cos(lat2Rad);
  const x =
    Math.cos(lat1Rad) * Math.sin(lat2Rad) -
    Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(dLon);
  
  let bearing = Math.atan2(y, x);
  bearing = toDegrees(bearing);
  bearing = (bearing + 360) % 360;
  
  return bearing;
}

/**
 * 根据起点、距离和方位角计算终点
 * @param start 起点 [longitude, latitude]
 * @param distance 距离（米）
 * @param bearing 方位角（度）
 * @returns 终点 [longitude, latitude]
 */
export function calculateDestination(
  start: [number, number],
  distance: number,
  bearing: number
): [number, number] {
  const R = 6371000; // 地球半径（米）
  const [lng1, lat1] = start;
  const lat1Rad = toRadians(lat1);
  const bearingRad = toRadians(bearing);
  const d = distance / R;
  
  const lat2Rad = Math.asin(
    Math.sin(lat1Rad) * Math.cos(d) +
      Math.cos(lat1Rad) * Math.sin(d) * Math.cos(bearingRad)
  );
  
  const lng2Rad =
    lng1 +
    Math.atan2(
      Math.sin(bearingRad) * Math.sin(d) * Math.cos(lat1Rad),
      Math.cos(d) - Math.sin(lat1Rad) * Math.sin(lat2Rad)
    );
  
  return [toDegrees(lng2Rad), toDegrees(lat2Rad)];
}

/**
 * 检查坐标是否在有效范围内
 * @param longitude 经度
 * @param latitude 纬度
 * @returns 是否有效
 */
export function isValidCoordinate(
  longitude: number,
  latitude: number
): boolean {
  return (
    longitude >= -180 &&
    longitude <= 180 &&
    latitude >= -90 &&
    latitude <= 90
  );
}

/**
 * 格式化距离显示
 * @param distance 距离（米）
 * @returns 格式化后的字符串
 */
export function formatDistance(distance: number): string {
  if (distance < 1000) {
    return `${Math.round(distance)}米`;
  } else if (distance < 10000) {
    return `${(distance / 1000).toFixed(1)}公里`;
  } else {
    return `${Math.round(distance / 1000)}公里`;
  }
}

/**
 * 将坐标数组转换为GeoJSON格式
 * @param coordinates 坐标数组 [[lng, lat], ...]
 * @returns GeoJSON格式的坐标
 */
export function toGeoJSONCoordinates(
  coordinates: [number, number][]
): [number, number][] {
  return coordinates.map(([lng, lat]) => [lng, lat]);
}

/**
 * 计算多边形的中心点
 * @param polygon 多边形坐标数组
 * @returns 中心点 [longitude, latitude]
 */
export function calculatePolygonCenter(
  polygon: [number, number][]
): [number, number] {
  let sumLng = 0;
  let sumLat = 0;
  
  for (const [lng, lat] of polygon) {
    sumLng += lng;
    sumLat += lat;
  }
  
  return [sumLng / polygon.length, sumLat / polygon.length];
}

