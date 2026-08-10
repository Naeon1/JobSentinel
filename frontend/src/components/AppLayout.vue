<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Odometer,
  OfficeBuilding,
  Document,
  Timer,
  Setting,
  Fold,
  Expand,
  Refresh,
  DataLine,
  Message,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const isCollapse = ref(false)

// 导航菜单项
const menuItems = [
  { path: '/dashboard', title: '仪表盘', icon: Odometer },
  { path: '/companies', title: '公司管理', icon: OfficeBuilding },
  { path: '/positions', title: '职位配置', icon: Document },
  { path: '/jobs', title: '招聘信息', icon: Timer },
  { path: '/tasks', title: '任务历史', icon: DataLine },
  { path: '/executions', title: '执行过程', icon: Odometer },
  { path: '/email-logs', title: '邮件通知', icon: Message },
  { path: '/settings', title: '系统设置', icon: Setting },
]

// 当前激活的菜单
const activeMenu = computed(() => route.path)

// 导航分组（变体2：结构分解轴）
const navGroups = [
  { label: '监测', items: [menuItems[0], menuItems[3]] },
  { label: '配置', items: [menuItems[1], menuItems[2]] },
  { label: '运行', items: [menuItems[4], menuItems[5], menuItems[6]] },
  { label: '系统', items: [menuItems[7]] },
]

// 页面标题
const pageTitle = computed(() => (route.meta.title as string) || '仪表盘')

// 切换侧边栏
const toggleSidebar = () => {
  isCollapse.value = !isCollapse.value
}

// 跳转页面
const navigateTo = (path: string) => {
  router.push(path)
}
</script>

<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: isCollapse }">
      <!-- Logo -->
      <div class="sidebar-logo" @click="navigateTo('/dashboard')">
        <div class="logo-icon">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect width="28" height="28" rx="8" fill="url(#logo-gradient)"/>
            <path d="M8 10h12M8 14h8M8 18h10" stroke="white" stroke-width="2" stroke-linecap="round"/>
            <circle cx="21" cy="18" r="3" fill="#60a5fa"/>
            <defs>
              <linearGradient id="logo-gradient" x1="0" y1="0" x2="28" y2="28">
                <stop stop-color="#3b82f6"/>
                <stop offset="1" stop-color="#1d4ed8"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <transition name="fade">
          <span v-if="!isCollapse" class="logo-text">JobSentinel</span>
        </transition>
      </div>

      <!-- 导航菜单 -->
      <nav class="sidebar-nav">
        <template v-for="(group, gi) in navGroups" :key="group.label">
          <div v-if="!isCollapse" class="nav-group">
            <div class="group-label">{{ group.label }}</div>
          </div>
          <div v-else-if="gi > 0" style="height: 8px"></div>
          <div
            v-for="item in group.items"
            :key="item.path"
            class="nav-item"
            :class="{ active: activeMenu === item.path }"
            @click="navigateTo(item.path)"
          >
            <el-icon class="nav-icon">
              <component :is="item.icon" />
            </el-icon>
            <transition name="fade">
              <span v-if="!isCollapse" class="nav-text">{{ item.title }}</span>
            </transition>
            <div v-if="activeMenu === item.path" class="active-indicator"></div>
          </div>
        </template>
      </nav>

      <!-- 侧栏底部 -->
      <div class="sidebar-footer">
        <div class="collapse-btn" @click="toggleSidebar">
          <el-icon :size="18">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <transition name="fade">
            <span v-if="!isCollapse" class="collapse-text">收起</span>
          </transition>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <div class="main-wrapper">
      <!-- 顶栏 -->
      <header class="topbar">
        <div class="topbar-left">
          <h1 class="page-title">{{ pageTitle }}</h1>
        </div>
        <div class="topbar-right">
          <button class="icon-btn" @click="$router.go(0)" title="刷新数据">
            <el-icon :size="18"><Refresh /></el-icon>
          </button>
        </div>
      </header>

      <!-- 页面内容 -->
      <main class="main-content">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
/* ── 布局 ── */
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background-color: var(--js-page-bg);
}

/* ── 侧边栏 ── */
.sidebar {
  width: 240px;
  min-width: 240px;
  height: 100vh;
  background: var(--js-sidebar-bg);
  display: flex;
  flex-direction: column;
  transition: width var(--js-transition-slow), min-width var(--js-transition-slow);
  position: relative;
  z-index: 100;
}

.sidebar.collapsed {
  width: 72px;
  min-width: 72px;
}

/* Logo */
.sidebar-logo {
  height: 64px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 20px;
  cursor: pointer;
  border-bottom: 1px solid var(--js-sidebar-border);
  flex-shrink: 0;
}

.logo-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
  white-space: nowrap;
  letter-spacing: -0.02em;
}

/* 导航 */
.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--js-radius-md);
  cursor: pointer;
  color: var(--js-sidebar-text);
  transition: all var(--js-transition);
  position: relative;
  white-space: nowrap;
}

.nav-item:hover {
  background: var(--js-sidebar-hover);
  color: var(--js-sidebar-text-active);
}

.nav-item.active {
  background: var(--js-sidebar-active);
  color: var(--js-sidebar-text-active);
}

.nav-icon {
  font-size: 18px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-text {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}

/* 激活指示器 */
.active-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: var(--js-primary);
  border-radius: 0 3px 3px 0;
  box-shadow: 0 0 8px var(--js-primary);
}

/* 分组化导航（结构分解轴变体，已接受） */
.sidebar-nav {
  padding: 8px 10px;
  gap: 2px;
}
.nav-group {
  margin-top: 12px;
}
.nav-group:first-child {
  margin-top: 4px;
}
.group-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.55);
  padding: 0 12px 6px 12px;
  white-space: nowrap;
}
.nav-item {
  gap: 11px;
  padding: 8px 12px;
  border-radius: var(--js-radius-sm);
  font-weight: 500;
}
.nav-icon {
  font-size: 16px;
}
.nav-text {
  font-size: 13px;
  font-weight: 500;
}

/* 底部收起按钮 */
.sidebar-footer {
  padding: 12px 8px;
  border-top: 1px solid var(--js-sidebar-border);
  flex-shrink: 0;
}

.collapse-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--js-radius-md);
  cursor: pointer;
  color: var(--js-sidebar-text);
  transition: all var(--js-transition);
}

.collapse-btn:hover {
  background: var(--js-sidebar-hover);
  color: var(--js-sidebar-text-active);
}

.collapse-text {
  font-size: 13px;
  white-space: nowrap;
}

/* ── 主内容区 ── */
.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

/* 顶栏 */
.topbar {
  height: 64px;
  min-height: 64px;
  background: var(--js-header-bg);
  border-bottom: 1px solid var(--js-header-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--js-header-text);
  letter-spacing: -0.01em;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--js-radius-sm);
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--js-text-secondary);
  transition: all var(--js-transition);
}

.icon-btn:hover {
  background: var(--js-page-bg);
  color: var(--js-text-primary);
}

/* 内容区 */
.main-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  overflow-x: hidden;
}

/* ── 过渡动画 ── */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
