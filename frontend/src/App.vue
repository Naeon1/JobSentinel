<script setup lang="ts">
import { RouterView } from 'vue-router'
import AppLayout from './components/AppLayout.vue'
</script>

<template>
  <AppLayout>
    <RouterView />
  </AppLayout>
</template>

<style>
/* 全局样式重置 */
*,
*::before,
*::after {
  box-sizing: border-box;
}

html {
  font-size: 14px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  scroll-behavior: smooth;
}

body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: var(--js-page-bg);
  color: var(--js-text-primary);
}

#app {
  width: 100%;
  min-height: 100vh;
}

/* ── Element Plus 覆盖 ── */
.el-card {
  border-radius: var(--js-radius-lg) !important;
  border: 1px solid var(--js-card-border) !important;
  box-shadow: var(--js-card-shadow) !important;
  transition: box-shadow var(--js-transition) !important;
}

.el-card:hover {
  box-shadow: var(--js-card-shadow-hover) !important;
}

.el-button {
  border-radius: var(--js-radius-sm) !important;
  font-weight: 500 !important;
  transition: all var(--js-transition) !important;
}

.el-button--primary {
  background-color: var(--js-primary) !important;
  border-color: var(--js-primary) !important;
}

.el-button--primary:hover {
  background-color: var(--js-primary-light) !important;
  border-color: var(--js-primary-light) !important;
}

.el-button--primary:active {
  background-color: var(--js-primary-dark) !important;
  border-color: var(--js-primary-dark) !important;
}

.el-input__wrapper,
.el-textarea__inner,
.el-select__wrapper {
  border-radius: var(--js-radius-sm) !important;
  box-shadow: 0 0 0 1px var(--js-card-border) inset !important;
  transition: all var(--js-transition) !important;
}

.el-input__wrapper:hover,
.el-textarea__inner:hover,
.el-select__wrapper:hover {
  box-shadow: 0 0 0 1px var(--js-primary-light) inset !important;
}

.el-input__wrapper.is-focus,
.el-textarea__inner:focus,
.el-select__wrapper.is-focused {
  box-shadow: 0 0 0 2px var(--js-primary-alpha) inset, 0 0 0 2px var(--js-primary) inset !important;
}

.el-table {
  --el-table-border-color: var(--js-card-border);
  --el-table-header-bg-color: #f8fafc;
  --el-table-row-hover-bg-color: var(--js-primary-alpha);
  border-radius: var(--js-radius-md);
  overflow: hidden;
}

.el-table th.el-table__cell {
  font-weight: 600 !important;
  color: var(--js-text-secondary) !important;
  font-size: 12px !important;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.el-table td.el-table__cell {
  color: var(--js-text-primary);
}

.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell {
  background-color: #fafbfc;
}

.el-dialog {
  border-radius: var(--js-radius-xl) !important;
}

.el-dialog__header {
  padding: 20px 24px 0 !important;
}

.el-dialog__body {
  padding: 20px 24px !important;
}

.el-dialog__footer {
  padding: 0 24px 20px !important;
}

.el-tag {
  border-radius: 20px !important;
  font-weight: 500 !important;
}

.el-pagination {
  --el-pagination-hover-color: var(--js-primary);
}

.el-pagination.is-background .el-pager li:not(.is-disabled).is-active {
  background-color: var(--js-primary) !important;
}

.el-form-item__label {
  font-weight: 500 !important;
  color: var(--js-text-primary) !important;
}

.el-descriptions__label {
  font-weight: 500 !important;
  color: var(--js-text-secondary) !important;
}

.el-menu {
  border-right: none !important;
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.15);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.25);
}

/* 侧栏内滚动条 */
.aside ::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
}

/* ── 工具类 ── */
.text-primary { color: var(--js-text-primary); }
.text-secondary { color: var(--js-text-secondary); }
.text-tertiary { color: var(--js-text-tertiary); }
.text-success { color: var(--js-success); }
.text-warning { color: var(--js-warning); }
.text-danger { color: var(--js-danger); }
.text-info { color: var(--js-info); }

.bg-page { background-color: var(--js-page-bg); }
.bg-card { background-color: var(--js-card-bg); }

.flex { display: flex; }
.flex-col { flex-direction: column; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.gap-2 { gap: 8px; }
.gap-3 { gap: 12px; }
.gap-4 { gap: 16px; }
.gap-5 { gap: 20px; }
</style>
