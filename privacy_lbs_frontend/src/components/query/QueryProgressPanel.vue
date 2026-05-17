<template>
  <transition name="panel-slide">
    <div v-if="visible" class="qpp-wrapper">
      <!-- Title row -->
      <div class="qpp-header">
        <span class="qpp-title">
          <el-icon class="spin" v-if="isRunning"><Loading /></el-icon>
          <el-icon v-else-if="isDone" style="color:#67c23a"><CircleCheck /></el-icon>
          Query Progress
        </span>
        <span class="qpp-elapsed">{{ formatMs(queryStore.totalElapsedMs) }}</span>
        <el-button size="small" text @click="handlePause" :disabled="!isRunning">
          <el-icon><VideoPause /></el-icon> Pause Query
        </el-button>
      </div>
      <!-- 4 Stages -->
      <div class="qpp-stages">
        <div
          v-for="item in stageItems"
          :key="item.key"
          class="stage-row"
          :class="{ active: queryStore.activeStage === item.key, done: item.done, waiting: item.waiting }"
        >
          <div class="stage-icon">
            <el-icon v-if="item.done" style="color:#67c23a"><CircleCheck /></el-icon>
            <el-icon v-else-if="queryStore.activeStage === item.key" class="spin"><Loading /></el-icon>
            <el-icon v-else style="color:#c0c4cc"><CircleClose /></el-icon>
          </div>
          <div class="stage-body">
            <div class="stage-top">
              <span class="stage-label">{{ item.label }}</span>
              <span class="stage-meta">{{ item.meta }}</span>
            </div>
            <el-progress
              :percentage="item.progress"
              :stroke-width="6"
              :status="item.done ? 'success' : undefined"
              :color="item.color"
              :show-text="false"
              style="margin-top:6px"
            />
            <p class="stage-desc">{{ item.desc }}</p>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Loading, CircleCheck, CircleClose, VideoPause } from '@element-plus/icons-vue';
import { useQueryStore } from '@/stores/query.store';
import { QueryStatus } from '@/types';
import { eventBus } from '@/utils/event-bus';

const queryStore = useQueryStore();

const visible = computed(() =>
  // Only show when main query (non-continuous update) is running, avoid continuous re-rendering during continuous updates
  queryStore.queryStatus !== QueryStatus.IDLE &&
  queryStore.activeStage !== null
);
const isRunning = computed(() => queryStore.isQuerying);
const isDone = computed(() => queryStore.queryStatus === QueryStatus.SUCCESS);

function formatMs(ms: number): string {
  if (ms < 1000) return ms + ' ms';
  return (ms / 1000).toFixed(1) + ' s';
}

const stageItems = computed(() => {
  const { stage, activeStage } = queryStore;
  const isActive = (k: string) => activeStage === k;
  const isDoneStage = (k: string, p: number) => p === 100 && activeStage !== k;
  const isWaiting = (k: string, p: number) => p === 0 && !isActive(k);

  const pruneRate = stage.pruning.candidates[0] > 0
    ? Math.round((1 - stage.pruning.candidates[1] / stage.pruning.candidates[0]) * 100)
    : 0;

  return [
    {
      key: 'encrypting',
      label: 'Stage 1：Location and keyword encryption',
      progress: stage.encrypting.progress,
      color: '#409eff',
      meta: stage.encrypting.timeMs > 0 ? formatMs(stage.encrypting.timeMs) : '',
      desc: isActive('encrypting') ? 'Encrypting…' : stage.encrypting.progress === 100 ? 'Encryption completed' : 'Waiting for encryption',
      done: isDoneStage('encrypting', stage.encrypting.progress),
      waiting: isWaiting('encrypting', stage.encrypting.progress),
    },
    {
      key: 'pruning',
      label: 'Stage 2：Cloud space pruning',  
      progress: stage.pruning.progress,
      color: '#e6a23c',
      meta: stage.pruning.candidates[1] > 0
        ? `${stage.pruning.candidates[0].toLocaleString()} → ${stage.pruning.candidates[1].toLocaleString()}`
        : '',
      desc: isActive('pruning') ? `Cloud filtering (pruning rate: ${pruneRate}%)` : stage.pruning.progress === 100 ? `Pruning completed, rate ${pruneRate}%` : 'Waiting for pruning',
      done: isDoneStage('pruning', stage.pruning.progress),
      waiting: isWaiting('pruning', stage.pruning.progress),
    },
    {
      key: 'scoring',
      label: 'Stage 3：Fog node scoring calculation',
      progress: stage.scoring.progress,
      color: '#909399',
      meta: stage.scoring.totalNodes > 0
        ? `${stage.scoring.completedNodes}/${stage.scoring.totalNodes} nodes completed`
        : '',
      desc: isActive('scoring') ? 'Scoring…' : stage.scoring.progress === 100 ? 'Scoring completed' : 'Waiting for scoring',
      done: isDoneStage('scoring', stage.scoring.progress),
      waiting: isWaiting('scoring', stage.scoring.progress),
    },
    {
      key: 'aggregation',
      label: 'Stage 4：Result aggregation and sorting', 
      progress: stage.aggregation.progress,
      color: '#67c23a',
      meta: stage.aggregation.finalCount > 0
        ? `Top-${stage.aggregation.finalCount}`
        : '',
      desc: isActive('aggregation') ? 'Sorting and preparing for display…' : stage.aggregation.progress === 100 ? 'Sorting completed, ready for display' : 'Waiting for aggregation',
      done: isDoneStage('aggregation', stage.aggregation.progress),
      waiting: isWaiting('aggregation', stage.aggregation.progress),
    },
  ];
});

function handlePause() {
  eventBus.emit('query:pause');
}
</script>

<style scoped>
.qpp-wrapper {
  background: #fff;
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 14px 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  flex-shrink: 0;
}
.qpp-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.qpp-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
}
.qpp-elapsed {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-variant-numeric: tabular-nums;
  min-width: 48px;
  text-align: right;
}
.qpp-stages { display: flex; flex-direction: column; gap: 10px; }
.stage-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 8px 10px;
  border-radius: 6px;
  transition: background 0.25s, opacity 0.25s;
  opacity: 0.5;
}
.stage-row.active {
  background: var(--el-color-primary-light-9);
  opacity: 1;
}
.stage-row.done { opacity: 1; }
.stage-icon { padding-top: 2px; flex-shrink: 0; font-size: 16px; }
.stage-body { flex: 1; min-width: 0; }
.stage-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
.stage-label { font-size: 13px; font-weight: 500; color: var(--el-text-color-primary); }
.stage-meta { font-size: 11px; color: var(--el-text-color-secondary); font-variant-numeric: tabular-nums; }
.stage-desc { font-size: 11px; color: var(--el-text-color-placeholder); margin: 4px 0 0; }
@keyframes spin { to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; display: inline-flex; }
.panel-slide-enter-active, .panel-slide-leave-active { transition: all 0.3s ease; }
.panel-slide-enter-from, .panel-slide-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
