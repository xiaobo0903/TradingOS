<template>
  <aside class="sidebar">
    <el-menu
      :default-active="activeMenu"
      class="sidebar-menu"
      background-color="transparent"
      text-color="#8892A6"
      active-text-color="#FFFFFF"
      :router="true"
    >
      <el-menu-item index="/dashboard">
        <el-icon><HomeFilled /></el-icon>
        <span>首页 Dashboard</span>
      </el-menu-item>

      <el-sub-menu index="market">
        <template #title>
          <el-icon><TrendCharts /></el-icon>
          <span>市场 Market</span>
        </template>
        <el-menu-item index="/market">大盘行情</el-menu-item>
        <el-menu-item index="/hot">热门板块</el-menu-item>
      </el-sub-menu>

      <el-menu-item index="/watchlist">
        <el-icon><Star /></el-icon>
        <span>自选 WatchList</span>
      </el-menu-item>

      <el-menu-item index="/stock">
        <el-icon><DataLine /></el-icon>
        <span>个股分析</span>
      </el-menu-item>

      <el-menu-item index="/indicator">
        <el-icon><DataAnalysis /></el-icon>
        <span>技术指标</span>
      </el-menu-item>

      <el-menu-item index="/capital">
        <el-icon><Money /></el-icon>
        <span>资金分析</span>
      </el-menu-item>

      <el-menu-item index="/ai">
        <el-icon><ChatDotRound /></el-icon>
        <span>AI分析</span>
      </el-menu-item>

      <el-menu-item index="/datacenter">
        <el-icon><Box /></el-icon>
        <span>数据中心</span>
      </el-menu-item>

      <el-menu-item index="/knowledge">
        <el-icon><Reading /></el-icon>
        <span>知识库</span>
      </el-menu-item>

      <el-divider />

      <el-menu-item index="/settings">
        <el-icon><Setting /></el-icon>
        <span>系统设置</span>
      </el-menu-item>
    </el-menu>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  HomeFilled,
  TrendCharts,
  Star,
  DataLine,
  DataAnalysis,
  Money,
  ChatDotRound,
  Box,
  Reading,
  Setting
} from '@element-plus/icons-vue'

const route = useRoute()

const activeMenu = computed(() => route.path)
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  height: 100%;
  background-color: var(--bg-card);
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-menu {
  border-right: none;
  padding: 8px 0;
}

.sidebar-menu .el-menu-item,
.sidebar-menu .el-sub-menu__title {
  height: 44px;
  line-height: 44px;
  margin: 2px 8px;
  border-radius: var(--radius-md);
}

.sidebar-menu .el-menu-item:hover,
.sidebar-menu .el-sub-menu__title:hover {
  background-color: var(--bg-card-hover);
}

.sidebar-menu .el-menu-item.is-active {
  background-color: rgba(26, 115, 232, 0.15);
}

.sidebar-menu .el-divider {
  margin: 12px 16px;
  border-color: rgba(255, 255, 255, 0.05);
}

:deep(.el-sub-menu .el-menu-item) {
  height: 40px;
  line-height: 40px;
  padding-left: 52px !important;
}
</style>
