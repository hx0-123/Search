<template>
  <el-container class="app-layout">
    <!-- Side navigation -->
    <el-aside class="app-aside" :width="isCollapsed ? '64px' : '260px'">
      <!-- Logo -->
      <div class="aside-header">
        <template v-if="!isCollapsed">
          <span class="logo-text">SKTAQ</span>
          <span class="logo-badge">v2.0</span>
        </template>
        <el-icon class="logo-icon" v-else><DataAnalysis /></el-icon>
      </div>

      <!-- Role-grouped menu -->
      <el-menu
        :default-active="activeMenu"
        class="aside-menu"
        :collapse="isCollapsed"
        :collapse-transition="false"
        @select="handleMenuSelect"
      >
        <!-- DATA OWNER -->
        <div v-if="!isCollapsed" class="menu-group-title">DATA OWNER · Data Provider</div>
        <el-menu-item index="config">
          <el-icon><Setting /></el-icon>
          <template #title>System Config</template>
        </el-menu-item>
        <el-menu-item index="data-manage">
          <el-icon><Files /></el-icon>
          <template #title>Data Management</template>
        </el-menu-item>

        <!-- MOBILE USER -->
        <div v-if="!isCollapsed" class="menu-group-title menu-group-title--user">MOBILE USER · Query Terminal</div>
        <div v-else class="menu-divider" />
        <el-menu-item index="demo">
          <el-icon><MapLocation /></el-icon>
          <template #title>Query Map</template>
        </el-menu-item>
        <el-menu-item index="query-history">
          <el-icon><List /></el-icon>
          <template #title>Query History</template>
        </el-menu-item>

        <!-- SYSTEM ADMIN -->
        <div v-if="!isCollapsed" class="menu-group-title menu-group-title--admin">SYSTEM ADMIN · System Monitor</div>
        <div v-else class="menu-divider" />
        <el-menu-item index="dashboard">
          <el-icon><Monitor /></el-icon>
          <template #title>Node Monitor</template>
        </el-menu-item>
        <el-menu-item index="analysis">
          <el-icon><PieChart /></el-icon>
          <template #title>Results Analysis</template>
        </el-menu-item>
      </el-menu>

      <!-- Bottom actions -->
      <div class="aside-footer">
        <el-tooltip content="Back to Portal" placement="right" :disabled="!isCollapsed">
          <el-button
            class="portal-btn"
            :class="{ 'portal-btn--collapsed': isCollapsed }"
            @click="goHome"
            text
          >
            <el-icon><House /></el-icon>
            <span v-if="!isCollapsed" class="portal-btn-text">Back to Portal</span>
          </el-button>
        </el-tooltip>
        <el-button
          :icon="isCollapsed ? Expand : Fold"
          circle
          text
          @click="isCollapsed = !isCollapsed"
          class="collapse-btn"
        />
      </div>
    </el-aside>

    <!-- Main container -->
    <el-container class="main-container">
      <!-- Header status bar -->
      <el-header class="app-header">
        <div class="header-left">
          <!-- Breadcrumb -->
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item>SKTAQ</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentRole">
              <span class="bc-role" :class="roleClass">{{ currentRoleLabel }}</span>
            </el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentTitle">{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <div class="status-item">
            <span class="status-dot status-dot--ok" />
            <span class="status-label">Network Secure</span>
          </div>
          <div class="status-item">
            <el-icon style="color:#818cf8;font-size:14px"><Key /></el-icon>
            <span class="status-label">Key Loaded</span>
          </div>
          <div class="header-sys-id">SYS · SKTAQ-PROD</div>
        </div>
      </el-header>

      <!-- Main content -->
      <el-main class="app-main">
        <div v-if="navigating" class="nav-loading">
          <div class="nav-loading-bar"></div>
        </div>
        <router-view v-slot="{ Component }">
          <transition name="fade">
            <component :is="Component" :key="$route.path" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  MapLocation,
  Monitor,
  PieChart,
  Setting,
  DataAnalysis,
  Expand,
  Fold,
  Key,
  House,
  Files,
  List,
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const isCollapsed = ref(false)
const navigating = ref(false)

const activeMenu = computed(() => route.name as string || 'demo')
const currentTitle = computed(() => route.meta.title as string || '')
const currentRole = computed(() => route.meta.role as string || '')
const currentRoleLabel = computed(() => route.meta.roleLabel as string || '')

const roleClass = computed(() => {
  const r = currentRole.value
  if (r === 'DATA OWNER') return 'bc-role--owner'
  if (r === 'MOBILE USER') return 'bc-role--user'
  if (r === 'SYSTEM ADMIN') return 'bc-role--admin'
  return ''
})

async function handleMenuSelect(index: string) {
  if (route.name === index) return
  navigating.value = true
  // Yield to main thread to render loading mask before route change
  await new Promise(resolve => setTimeout(resolve, 0))
  try {
    await router.push({ name: index })
  } finally {
    // Wait for next frame to hide, ensure new component starts rendering
    requestAnimationFrame(() => {
      requestAnimationFrame(() => { navigating.value = false })
    })
  }
}

function goHome() {
  router.push({ name: 'home' })
}
</script>

<style scoped>
.app-layout {
  width: 100%;
  height: 100vh;
  display: flex;
  background: #0d1117;
}

/* ── Sidebar ── */
.app-aside {
  background: #1e222d;
  border-right: 1px solid #1e293b;
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease;
  overflow: hidden;
  flex-shrink: 0;
}

.aside-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-bottom: 1px solid #1e293b;
  padding: 0 16px;
  flex-shrink: 0;
}
.logo-text {
  font-size: 18px;
  font-weight: 800;
  color: #38bdf8;
  letter-spacing: 3px;
  font-family: 'JetBrains Mono', monospace;
}
.logo-badge {
  font-size: 10px;
  color: #475569;
  background: #131720;
  border: 1px solid #1e293b;
  border-radius: 3px;
  padding: 1px 5px;
  font-family: monospace;
}
.logo-icon {
  font-size: 24px;
  color: #38bdf8;
}

/* Menu */
.aside-menu {
  flex: 1;
  background: #1e222d;
  border: none;
  padding: 8px 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.menu-group-title {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1.5px;
  color: #2563eb;
  padding: 14px 20px 5px;
  text-transform: uppercase;
  white-space: nowrap;
  overflow: hidden;
}
.menu-group-title--user  { color: #0891b2; }
.menu-group-title--admin { color: #7c3aed; }

.menu-divider {
  height: 1px;
  background: #1e293b;
  margin: 8px 12px;
}

:deep(.aside-menu .el-menu-item) {
  background: transparent;
  color: #94a3b8;
  font-size: 15px;
  height: 48px;
  line-height: 48px;
  margin: 2px 8px;
  border-radius: 6px;
  transition: all 0.2s ease;
  padding-left: 20px !important;
}
:deep(.aside-menu .el-menu-item:hover) {
  background: rgba(56, 189, 248, 0.08);
  color: #e2e8f0;
}
:deep(.aside-menu .el-menu-item.is-active) {
  background: rgba(56, 189, 248, 0.12);
  color: #38bdf8;
  border-left: 2px solid #38bdf8;
}
:deep(.aside-menu .el-menu-item .el-icon) {
  font-size: 16px;
  margin-right: 10px;
  flex-shrink: 0;
}
:deep(.aside-menu.el-menu--collapse .el-menu-item) {
  padding-left: 0 !important;
  justify-content: center;
}
:deep(.aside-menu.el-menu--collapse .el-menu-item .el-icon) {
  margin-right: 0;
}

/* Footer */
.aside-footer {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid #1e293b;
  padding: 0 10px;
  flex-shrink: 0;
  gap: 4px;
}
.portal-btn {
  color: #64748b;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  justify-content: flex-start;
  padding: 0 8px;
  border-radius: 6px;
  transition: all 0.2s;
}
.portal-btn:hover {
  color: #38bdf8;
  background: rgba(56,189,248,0.08);
}
.portal-btn--collapsed {
  justify-content: center;
  flex: none;
  width: 36px;
  padding: 0;
}
.portal-btn-text { font-size: 13px; white-space: nowrap; }
.collapse-btn {
  color: #475569;
  flex-shrink: 0;
}
.collapse-btn:hover { color: #38bdf8; }

/* ── Main Container ── */
.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

/* ── Header ── */
.app-header {
  height: 52px;
  background: #131720;
  border-bottom: 1px solid #1e293b;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}

.breadcrumb {
  font-size: 13px;
}
:deep(.breadcrumb .el-breadcrumb__inner) {
  color: #475569;
  font-size: 13px;
}
:deep(.breadcrumb .el-breadcrumb__item:last-child .el-breadcrumb__inner) {
  color: #94a3b8;
  font-weight: 500;
}
:deep(.breadcrumb .el-breadcrumb__separator) {
  color: #1e293b;
}
.bc-role {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
  padding: 2px 7px;
  border-radius: 3px;
  text-transform: uppercase;
}
.bc-role--owner { background: rgba(37,99,235,0.15); color: #60a5fa; }
.bc-role--user  { background: rgba(8,145,178,0.15); color: #22d3ee; }
.bc-role--admin { background: rgba(124,58,237,0.15); color: #a78bfa; }

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}
.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.status-dot--ok {
  background: #34d399;
  box-shadow: 0 0 6px #34d399;
  animation: blink 2.5s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.35} }
.status-label {
  font-size: 12px;
  color: #475569;
  white-space: nowrap;
}
.header-sys-id {
  font-size: 11px;
  color: #1e3a5f;
  font-family: monospace;
  letter-spacing: 1px;
  border: 1px solid #1e293b;
  padding: 2px 8px;
  border-radius: 3px;
}

/* ── Main Content Area ── */
.app-main {
  flex: 1;
  overflow: auto;
  padding: 0;
  background: #0d1117;
  position: relative;
}

/* ── Navigation Loading Mask ── */
.nav-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 999;
  height: 3px;
  overflow: hidden;
  pointer-events: none;
}
.nav-loading-bar {
  height: 100%;
  background: linear-gradient(90deg, #38bdf8, #818cf8, #34d399);
  animation: nav-progress 0.8s ease-in-out infinite;
  transform-origin: left;
}
@keyframes nav-progress {
  0%   { transform: scaleX(0); opacity: 1; }
  60%  { transform: scaleX(0.8); opacity: 1; }
  100% { transform: scaleX(1); opacity: 0; }
}

/* ── Transition Animation ── */
.fade-enter-active {
  transition: opacity 0.15s ease;
}
.fade-leave-active {
  transition: opacity 0.08s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
