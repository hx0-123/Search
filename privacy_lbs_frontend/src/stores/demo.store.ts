/**
 * Demo Mode Store
 * Controls the 6-step automatic demonstration flow for DemoView
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { eventBus } from '@/utils/event-bus';

export enum DemoStep {
  UPLOAD   = 0,
  CONFIG   = 1,
  QUERY    = 2,
  PROGRESS = 3,
  RESULTS  = 4,
  SUMMARY  = 5,
}

export interface DemoStepMeta {
  step: DemoStep;
  key: string;
  label: string;
  icon: string;
  desc: string;
  durationMs: number; // Duration at 1x speed
}

export const DEMO_STEPS: DemoStepMeta[] = [
  { step: DemoStep.UPLOAD,   key: 'upload',   label: 'Data Upload',   icon: '📁', desc: 'Simulate CSV upload → Preview → Encryption complete', durationMs: 3500 },
  { step: DemoStep.CONFIG,   key: 'config',   label: 'Config Load',   icon: '⚙️', desc: 'Auto-set radius=1000, alpha=0.6',   durationMs: 2500 },
  { step: DemoStep.QUERY,    key: 'query',    label: 'Query',         icon: '🔍', desc: 'Input keyword "restaurant", fixed location',       durationMs: 2000 },
  { step: DemoStep.PROGRESS, key: 'progress', label: 'Visualization', icon: '⚡', desc: 'Play 4-stage query progress animation',            durationMs: 4000 },
  { step: DemoStep.RESULTS,  key: 'results',  label: 'Results',       icon: '📍', desc: 'Map shows POIs + Safe Zone + sorted list',        durationMs: 3500 },
  { step: DemoStep.SUMMARY,  key: 'summary',  label: 'Summary',       icon: '📊', desc: 'Display latency, hit rate and statistics',        durationMs: 3000 },
];

export const useDemoStore = defineStore('demo', () => {
  const currentStep = ref<DemoStep>(DemoStep.UPLOAD);
  const isPlaying   = ref(false);
  const playSpeed   = ref<1 | 2>(1);
  const elapsedMs   = ref(0);     // Current step elapsed time
  const totalMs     = ref(0);     // Total demo elapsed time
  const isFinished  = ref(false);

  let _stepTimer:    ReturnType<typeof setTimeout>   | null = null;
  let _elapsedTimer: ReturnType<typeof setInterval> | null = null;
  let _stepStart = 0;

  const currentMeta = computed(() => DEMO_STEPS[currentStep.value]);
  const progress    = computed(() => {
    const dur = currentMeta.value.durationMs / playSpeed.value;
    return Math.min(100, Math.round((elapsedMs.value / dur) * 100));
  });
  const overallProgress = computed(() =>
    Math.round(((currentStep.value + progress.value / 100) / DEMO_STEPS.length) * 100)
  );

  function _clearTimers() {
    if (_stepTimer)    { clearTimeout(_stepTimer);    _stepTimer    = null; }
    if (_elapsedTimer) { clearInterval(_elapsedTimer); _elapsedTimer = null; }
  }

  function _startStepTimer() {
    _stepStart = Date.now();
    elapsedMs.value = 0;

    _elapsedTimer = setInterval(() => {
      elapsedMs.value = Date.now() - _stepStart;
      totalMs.value  += 100;
    }, 100);

    const dur = DEMO_STEPS[currentStep.value].durationMs / playSpeed.value;
    _stepTimer = setTimeout(() => {
      _advanceStep();
    }, dur);
  }

  function _advanceStep() {
    _clearTimers();
    const next = currentStep.value + 1;
    if (next >= DEMO_STEPS.length) {
      isFinished.value = true;
      isPlaying.value  = false;
      eventBus.emit('demo:step', 'finished');
      return;
    }
    currentStep.value = next as DemoStep;
    elapsedMs.value   = 0;
    eventBus.emit('demo:step', DEMO_STEPS[next].key);
    _startStepTimer();
  }

  function play() {
    if (isFinished.value) replay();
    if (isPlaying.value) return;
    isPlaying.value = true;
    eventBus.emit('demo:step', DEMO_STEPS[currentStep.value].key);
    _startStepTimer();
  }

  function pause() {
    _clearTimers();
    isPlaying.value = false;
  }

  function replay() {
    _clearTimers();
    currentStep.value = DemoStep.UPLOAD;
    elapsedMs.value   = 0;
    totalMs.value     = 0;
    isFinished.value  = false;
    isPlaying.value   = false;
  }

  function jumpTo(step: DemoStep) {
    _clearTimers();
    currentStep.value = step;
    elapsedMs.value   = 0;
    isFinished.value  = false;
    if (isPlaying.value) {
      eventBus.emit('demo:step', DEMO_STEPS[step].key);
      _startStepTimer();
    }
  }

  function setSpeed(s: 1 | 2) {
    playSpeed.value = s;
    if (isPlaying.value) {
      // Recalculate remaining time
      _clearTimers();
      _startStepTimer();
    }
  }

  return {
    currentStep, isPlaying, playSpeed, elapsedMs, totalMs, isFinished,
    currentMeta, progress, overallProgress,
    play, pause, replay, jumpTo, setSpeed,
  };
});






