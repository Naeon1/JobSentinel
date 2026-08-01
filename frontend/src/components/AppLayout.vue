<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Odometer,
  OfficeBuilding,
  Position,
  Document,
  Timer,
  Setting,
  Fold,
  Expand,
  Refresh,
  DataLine,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const isCollapse = ref(false)

// 导航菜单项
const menuItems = [
  { path: '/dashboard', title: '仪表盘', icon: Odometer },
  { path: '/companies', title: '公司管理', icon: OfficeBuilding },
  { path: '/positions', title: '职位配置', icon: Position },
  { path: '/jobs', title: '招聘信息', icon: Document },
  { path: '/tasks', title: '任务历史', icon: Timer },
  { path: '/executions', title: '执行过程', icon: DataLine },
  { path: '/settings', title: '系统设置', icon: Setting },
]

// 当前激活的菜单
const activeMenu = computed(() => route.path)

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
  <el-container class="app-layout">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="aside">
      <div class="logo" @click="navigateTo('/dashboard')">
        <el-icon :size="24"><Document /></el-icon>
        <span v-show="!isCollapse" class="logo-text">JobSentinel</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        class="side-menu"
        @select="(path: string) => navigateTo(path)"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.path"
          :index="item.path"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <!-- 顶栏 -->
      <el-header class="header">
        <div class="header-left">
          <el-icon
            class="collapse-btn"
            :size="20"
            @click="toggleSidebar"
          >
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <h2 class="page-title">{{ pageTitle }}</h2>
        </div>
        <div class="header-right">
          <el-tooltip content="刷新数据" placement="bottom">
            <el-button :icon="Refresh" circle @click="$router.go(0)" />
          </el-tooltip>
        </div>
      </el-header>

      <!-- 页面内容 -->
      <el-main class="main-content">
        <slot />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.app-layout {
  height: 100vh;
  overflow: hidden;
}

.aside {
  background-color: #304156;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #fff;
  cursor: pointer;
  border-bottom: 1px solid #3d4f65;
}

.logo-text {
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}

.side-menu {
  border-right: none;
  background-color: #304156;
}

.side-menu:not(.el-menu--collapse) {
  width: 220px;
}

:deep(.el-menu-item) {
  color: #bfcbd9;
}

:deep(.el-menu-item:hover),
:deep(.el-menu-item.is-active) {
  background-color: #263445;
  color: #409eff;
}

.main-container {
  background-color: #f0f2f5;
}

.header {
  background-color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  cursor: pointer;
  color: #666;
}

.collapse-btn:hover {
  color: #409eff;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.main-content {
  padding: 20px;
  overflow-y: auto;
  height: calc(100vh - 60px);
}
</style>
