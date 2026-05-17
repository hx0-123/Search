/**
 * Coordinate conversion utility functions
 * Provides conversion functions between various coordinate systems
 */

/**
 * Calculate distance between two points (Haversine formula)
 * @param point1 First point [longitude, latitude]
 * @param point2 Second point [longitude, latitude]
 * @returns Distance (meters)
 */
export function calculateDistance(
  point1: [number, number],
  point2: [number, number]
): number {
  const R = 6371000; // Earth radius (meters)
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
 * Convert degrees to radians
 */
function toRadians(degrees: number): number {
  return degrees * (Math.PI / 180);
}

/**
 * Convert radians to degrees
 */
function toDegrees(radians: number): number {
  return radians * (180 / Math.PI);
}

/**
 * Calculate bearing between two points (from point1 to point2)
 * @param point1 Start point [longitude, latitude]
 * @param point2 End point [longitude, latitude]
 * @returns Bearing (degrees, 0-360)
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
 * Calculate destination point from start, distance and bearing
 * @param start Start point [longitude, latitude]
 * @param distance Distance (meters)
 * @param bearing Bearing (degrees)
 * @returns Destination [longitude, latitude]
 */
export function calculateDestination(
  start: [number, number],
  distance: number,
  bearing: number
): [number, number] {
  const R = 6371000; // Earth radius (meters)
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
 * Check if coordinate is within valid range
 * @param longitude Longitude
 * @param latitude Latitude
 * @returns Whether valid
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
 * Format distance for display
 * @param distance Distance (meters)
 * @returns Formatted string
 */
export function formatDistance(distance: number): string {
  if (distance < 1000) {
    return `${Math.round(distance)}m`;
  } else if (distance < 10000) {
    return `${(distance / 1000).toFixed(1)}km`;
  } else {
    return `${Math.round(distance / 1000)}km`;
  }
}

/**
 * Convert coordinate array to GeoJSON format
 * @param coordinates Coordinate array [[lng, lat], ...]
 * @returns GeoJSON formatted coordinates
 */
export function toGeoJSONCoordinates(
  coordinates: [number, number][]
): [number, number][] {
  return coordinates.map(([lng, lat]) => [lng, lat]);
}

/**
 * Calculate polygon center point
 * @param polygon Polygon coordinate array
 * @returns Center point [longitude, latitude]
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

