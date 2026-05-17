/**
 * Geographic calculation utility functions (merged version)
 * Merged from geo-simple.util.ts + simple-geo.util.ts
 *
 * Grouped by functionality:
 *  1. Distance Calculation
 *  2. Coordinate Conversion
 *  3. Geometric Operations
 *  4. Polygon Generation
 */

// ─────────────────────────────────────────────────────────────
// 1. Distance Calculation
// ─────────────────────────────────────────────────────────────

/** Earth mean radius (meters) */
const EARTH_RADIUS_M = 6371000;

/** Convert degrees to radians (internal helper) */
function toRad(deg: number): number {
  return (deg * Math.PI) / 180;
}

/**
 * Haversine formula: Calculate spherical distance between two points
 * @param lng1 Starting longitude (degrees)
 * @param lat1 Starting latitude (degrees)
 * @param lng2 Ending longitude (degrees)
 * @param lat2 Ending latitude (degrees)
 * @returns Distance (meters)
 */
export function haversineDistance(
  lng1: number,
  lat1: number,
  lng2: number,
  lat2: number
): number {
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.sin(dLng / 2) *
      Math.sin(dLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return EARTH_RADIUS_M * c;
}

/**
 * Calculate distance between two points (array parameter version, convenience alias for haversineDistance)
 * @param point1 [longitude, latitude]
 * @param point2 [longitude, latitude]
 * @returns Distance (meters)
 */
export function calculateDistance(
  point1: [number, number],
  point2: [number, number]
): number {
  return haversineDistance(point1[0], point1[1], point2[0], point2[1]);
}

/**
 * Calculate bearing from point1 to point2 (clockwise from true north)
 * @param lng1 Starting longitude
 * @param lat1 Starting latitude
 * @param lng2 Ending longitude
 * @param lat2 Ending latitude
 * @returns Bearing (0–360°)
 */
export function bearingTo(
  lng1: number,
  lat1: number,
  lng2: number,
  lat2: number
): number {
  const dLng = toRad(lng2 - lng1);
  const lat1Rad = toRad(lat1);
  const lat2Rad = toRad(lat2);
  const y = Math.sin(dLng) * Math.cos(lat2Rad);
  const x =
    Math.cos(lat1Rad) * Math.sin(lat2Rad) -
    Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(dLng);
  return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360;
}

// ─────────────────────────────────────────────────────────────
// 2. Coordinate Conversion
// ─────────────────────────────────────────────────────────────

/**
 * Convert meter offsets to latitude/longitude offsets
 * @param centerLat Reference latitude (degrees)
 * @param offsetXMeters East-west offset (meters, positive east)
 * @param offsetYMeters North-south offset (meters, positive north)
 * @returns [deltaLng, deltaLat] Lat/lng offsets (degrees)
 */
export function metersToLatLngDelta(
  centerLat: number,
  offsetXMeters: number,
  offsetYMeters: number
): [number, number] {
  const metersPerDegreeLat = 111320;
  const metersPerDegreeLng = 111320 * Math.cos(toRad(centerLat));
  return [
    offsetXMeters / metersPerDegreeLng,
    offsetYMeters / metersPerDegreeLat,
  ];
}

/**
 * Convert lat/lng to Web Mercator (EPSG:3857)
 * @param lng Longitude (degrees)
 * @param lat Latitude (degrees)
 * @returns [x, y] (meters)
 */
export function lngLatToMercator(lng: number, lat: number): [number, number] {
  const x = (lng * Math.PI * EARTH_RADIUS_M) / 180;
  const y =
    Math.log(Math.tan(((90 + lat) * Math.PI) / 360)) *
    (EARTH_RADIUS_M * (180 / Math.PI)) *
    (Math.PI / 180);
  return [x, y];
}

/**
 * Convert Web Mercator (EPSG:3857) to lat/lng
 * @param x Mercator X (meters)
 * @param y Mercator Y (meters)
 * @returns [lng, lat] (degrees)
 */
export function mercatorToLngLat(x: number, y: number): [number, number] {
  const lng = (x / EARTH_RADIUS_M) * (180 / Math.PI);
  const lat =
    (Math.atan(Math.exp(y / EARTH_RADIUS_M)) * 360) / Math.PI - 90;
  return [lng, lat];
}

// ─────────────────────────────────────────────────────────────
// 3. Geometric Operations
// ─────────────────────────────────────────────────────────────

/**
 * Check if point is inside circular area
 * @param point   Point to check [longitude, latitude]
 * @param center  Circle center [longitude, latitude]
 * @param radiusM Circle radius (meters)
 * @returns true if point is inside circle (including boundary)
 */
export function isPointInCircle(
  point: [number, number],
  center: [number, number],
  radiusM: number
): boolean {
  return calculateDistance(point, center) <= radiusM;
}

/**
 * Check if point is inside polygon (Ray-casting algorithm)
 * @param point   Point to check [longitude, latitude]
 * @param polygon Polygon vertex array (does not need to be closed)
 * @returns true if point is inside polygon
 */
export function isPointInPolygon(
  point: [number, number],
  polygon: [number, number][]
): boolean {
  const [px, py] = point;
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i];
    const [xj, yj] = polygon[j];
    const intersect =
      yi > py !== yj > py && px < ((xj - xi) * (py - yi)) / (yj - yi) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}

/**
 * Calculate approximate centroid of polygon
 * @param polygon Polygon vertex array
 * @returns [longitude, latitude]
 */
export function polygonCentroid(polygon: [number, number][]): [number, number] {
  const n = polygon.length;
  if (n === 0) return [0, 0];
  const sum = polygon.reduce(
    (acc, [lng, lat]) => [acc[0] + lng, acc[1] + lat],
    [0, 0]
  );
  return [sum[0] / n, sum[1] / n];
}

/**
 * Calculate midpoint between two points
 * @param p1 [longitude, latitude]
 * @param p2 [longitude, latitude]
 * @returns [longitude, latitude]
 */
export function midpoint(
  p1: [number, number],
  p2: [number, number]
): [number, number] {
  return [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2];
}

// ─────────────────────────────────────────────────────────────
// 4. Polygon Generation
// ─────────────────────────────────────────────────────────────

/**
 * Generate approximate polygon for a circle (for map rendering)
 *
 * Two legacy function names are preserved (generateCirclePolygon),
 * both numPoints/points parameters are supported.
 *
 * @param center         Circle center [longitude, latitude]
 * @param radiusInMeters Radius (meters)
 * @param numPoints      Number of polygon points (default 32, more = smoother)
 * @returns Closed polygon coordinate array
 */
export function generateCirclePolygon(
  center: [number, number],
  radiusInMeters: number,
  numPoints: number = 32
): [number, number][] {
  const [centerLng, centerLat] = center;
  const latRadians = toRad(centerLat);
  const metersPerDegreeLat = 111320;
  const metersPerDegreeLng = 111320 * Math.cos(latRadians);

  const radiusLat = radiusInMeters / metersPerDegreeLat;
  const radiusLng = radiusInMeters / metersPerDegreeLng;
  
  const polygon: [number, number][] = [];
  for (let i = 0; i < numPoints; i++) {
    const angle = (i / numPoints) * 2 * Math.PI;
    polygon.push([
      centerLng + radiusLng * Math.cos(angle),
      centerLat + radiusLat * Math.sin(angle),
    ]);
  }
  
  // Close polygon
    polygon.push(polygon[0]);
    return polygon;
}

/**
 * Generate axis-aligned rectangular polygon (for map rendering bounding box)
 * @param center  Rectangle center [longitude, latitude]
 * @param widthM  Width (meters, east-west direction)
 * @param heightM Height (meters, north-south direction)
 * @returns Closed rectangle coordinate array (5 vertices, same start/end)
 */
export function generateRectPolygon(
  center: [number, number],
  widthM: number,
  heightM: number
): [number, number][] {
  const [dLng, dLat] = metersToLatLngDelta(center[1], widthM / 2, heightM / 2);
  const [lng, lat] = center;
  const polygon: [number, number][] = [
    [lng - dLng, lat - dLat],
    [lng + dLng, lat - dLat],
    [lng + dLng, lat + dLat],
    [lng - dLng, lat + dLat],
    [lng - dLng, lat - dLat], // Close
  ];
  return polygon;
}
