// Script for testing environment variables
// Run this code in browser console to check environment variables

console.log('=== Environment Variables Check ===');
console.log('VITE_MAPBOX_ACCESS_TOKEN:', import.meta.env.VITE_MAPBOX_ACCESS_TOKEN);
console.log('Token exists:', !!import.meta.env.VITE_MAPBOX_ACCESS_TOKEN);
console.log('Token value (first 20 chars):', import.meta.env.VITE_MAPBOX_ACCESS_TOKEN ? import.meta.env.VITE_MAPBOX_ACCESS_TOKEN.substring(0, 20) : 'Not set');
console.log('Token contains default value:', import.meta.env.VITE_MAPBOX_ACCESS_TOKEN?.includes('your_token_here') || import.meta.env.VITE_MAPBOX_ACCESS_TOKEN === 'pk.your_mapbox_token_here');
console.log('All environment variables:', import.meta.env);












