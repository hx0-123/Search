// 测试环境变量的脚本
// 在浏览器控制台运行此代码来检查环境变量

console.log('=== 环境变量检查 ===');
console.log('VITE_MAPBOX_ACCESS_TOKEN:', import.meta.env.VITE_MAPBOX_ACCESS_TOKEN);
console.log('Token存在:', !!import.meta.env.VITE_MAPBOX_ACCESS_TOKEN);
console.log('Token值（前20字符）:', import.meta.env.VITE_MAPBOX_ACCESS_TOKEN ? import.meta.env.VITE_MAPBOX_ACCESS_TOKEN.substring(0, 20) : '未设置');
console.log('Token是否包含默认值:', import.meta.env.VITE_MAPBOX_ACCESS_TOKEN?.includes('your_token_here') || import.meta.env.VITE_MAPBOX_ACCESS_TOKEN === 'pk.your_mapbox_token_here');
console.log('所有环境变量:', import.meta.env);










