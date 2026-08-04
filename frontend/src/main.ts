/**
 * JobSentinel - 前端入口
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'

// 全局 CSS 变量（必须在导入 Element Plus CSS 之后覆盖）
const style = document.createElement('style')
style.textContent = `
:root {
  /* ── 品牌色 ── */
  --js-primary: #3b82f6;
  --js-primary-light: #60a5fa;
  --js-primary-dark: #2563eb;
  --js-primary-alpha: rgba(59, 130, 246, 0.12);

  /* ── 侧栏 ── */
  --js-sidebar-bg: #0f172a;
  --js-sidebar-hover: rgba(255, 255, 255, 0.06);
  --js-sidebar-active: rgba(59, 130, 246, 0.18);
  --js-sidebar-text: #94a3b8;
  --js-sidebar-text-active: #ffffff;
  --js-sidebar-border: rgba(255, 255, 255, 0.06);

  /* ── 顶栏 ── */
  --js-header-bg: #ffffff;
  --js-header-border: #e2e8f0;
  --js-header-text: #1e293b;

  /* ── 内容区 ── */
  --js-page-bg: #f1f5f9;
  --js-card-bg: #ffffff;
  --js-card-border: #e2e8f0;
  --js-card-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --js-card-shadow-hover: 0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);

  /* ── 文字层级 ── */
  --js-text-primary: #1e293b;
  --js-text-secondary: #64748b;
  --js-text-tertiary: #94a3b8;
  --js-text-inverse: #ffffff;

  /* ── 状态色 ── */
  --js-success: #10b981;
  --js-warning: #f59e0b;
  --js-danger: #ef4444;
  --js-info: #6366f1;

  /* ── 统计卡渐变背景 ── */
  --js-gradient-blue: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
  --js-gradient-green: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  --js-gradient-orange: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
  --js-gradient-purple: linear-gradient(135deg, #6366f1 0%, #818cf8 100%);
  --js-gradient-slate: linear-gradient(135deg, #475569 0%, #64748b 100%);

  /* ── 圆角 ── */
  --js-radius-sm: 6px;
  --js-radius-md: 10px;
  --js-radius-lg: 14px;
  --js-radius-xl: 20px;

  /* ── 过渡 ── */
  --js-transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  --js-transition-slow: 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
`
document.head.appendChild(style)

// 创建应用实例
const app = createApp(App)

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 使用插件
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: undefined })

// 挂载应用
app.mount('#app')
