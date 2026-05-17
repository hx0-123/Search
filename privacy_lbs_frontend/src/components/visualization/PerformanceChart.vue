<template>
  <div class="perf-chart" ref="chartEl"></div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, shallowRef } from 'vue';
import * as echarts from 'echarts';

type ChartType = 'histogram' | 'line' | 'pie';

const props = defineProps<{
  type: ChartType;
  data: any;
  title?: string;
  height?: string;
}>();

const chartEl = ref<HTMLDivElement | null>(null);
const chart = shallowRef<echarts.ECharts | null>(null);

function buildOption(type: ChartType, data: any): echarts.EChartsOption {
  const baseText = { color: '#606266', fontSize: 13 };

  if (type === 'histogram') {
    // Latency distribution histogram
    const values: number[] = data.values ?? [];
    const bins: number[] = data.bins ?? [];
    const avg: number = data.avg ?? 0;
    const p95: number = data.p95 ?? 0;
    return {
      title: { text: props.title ?? 'Query Latency Distribution', textStyle: baseText },
      tooltip: { trigger: 'axis', formatter: (p: any) => `${p[0].name} ms<br/>Count: ${p[0].value}` },
      grid: { left: 48, right: 24, top: 48, bottom: 36 },
      xAxis: { type: 'category', data: bins.map(b => b + ''), name: 'Latency (ms)', nameLocation: 'end' },
      yAxis: { type: 'value', name: 'Count' },
      series: [
        {
          type: 'bar',
          data: values,
          itemStyle: { color: '#409eff' },
          barMaxWidth: 32,
        },
      ],
      markLine: {
        silent: true,
        data: [
          { xAxis: avg, label: { formatter: `Avg ${avg}ms`, color: '#e6a23c' }, lineStyle: { color: '#e6a23c', type: 'dashed' } },
          { xAxis: p95, label: { formatter: `P95 ${p95}ms`, color: '#f56c6c' }, lineStyle: { color: '#f56c6c', type: 'dashed' } },
        ],
      } as any,
    };
  }

  if (type === 'line') {
    // Safe Zone hit rate trend line chart
    const times: string[] = data.times ?? [];
    const rates: number[] = data.rates ?? [];
    return {
      title: { text: props.title ?? 'Safe Zone Hit Rate Trend', textStyle: baseText },
      tooltip: { trigger: 'axis', formatter: (p: any) => `${p[0].name}<br/>Hit Rate: ${p[0].value}%` },
      grid: { left: 52, right: 24, top: 48, bottom: 36 },
      xAxis: { type: 'category', data: times, axisLabel: { rotate: 30, fontSize: 11 } },
      yAxis: { type: 'value', name: 'Hit Rate %', min: 0, max: 100 },
      series: [
        {
          type: 'line',
          data: rates,
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          itemStyle: { color: '#67c23a' },
          areaStyle: { color: 'rgba(103,194,58,0.12)' },
          lineStyle: { width: 2 },
        },
      ],
    };
  }

  if (type === 'pie') {
    // Encryption cost breakdown pie chart
    const items: { name: string; value: number }[] = data.items ?? [];
    return {
      title: { text: props.title ?? 'Encryption Cost Breakdown', textStyle: baseText, left: 'center' },
      tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
      legend: { orient: 'vertical', left: 10, top: 'middle', textStyle: { fontSize: 12 } },
      series: [
        {
          type: 'pie',
          radius: ['38%', '62%'],
          center: ['60%', '50%'],
          data: items,
          label: { formatter: '{b}\n{d}%', fontSize: 12 },
          itemStyle: {
            borderRadius: 4,
            borderColor: '#fff',
            borderWidth: 2,
          },
        },
      ],
      color: ['#f56c6c', '#409eff', '#67c23a', '#e6a23c'],
    };
  }

  return {};
}

function initChart() {
  if (!chartEl.value) return;
  chart.value = echarts.init(chartEl.value, undefined, { renderer: 'svg' });
  chart.value.setOption(buildOption(props.type, props.data));
}

function resizeChart() {
  chart.value?.resize();
}

watch(
  () => [props.type, props.data],
  () => {
    if (chart.value) {
      chart.value.setOption(buildOption(props.type, props.data), true);
    }
  },
  { deep: true }
);

const ro = new ResizeObserver(resizeChart);

onMounted(() => {
  initChart();
  if (chartEl.value) ro.observe(chartEl.value);
});

onUnmounted(() => {
  ro.disconnect();
  chart.value?.dispose();
});
</script>

<style scoped>
.perf-chart {
  width: 100%;
  height: v-bind('props.height ?? "280px"');
}
</style>






