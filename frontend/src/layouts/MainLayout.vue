<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const isCollapse = ref(false)

const menuItems = [
  { path: '/', title: '股票明细', icon: 'List' },
]

function handleMenuSelect(path: string) {
  router.push(path)
}
</script>

<template>
  <el-container class="main-layout">
    <el-aside :width="isCollapse ? '64px' : '200px'">
      <div class="logo">
        <span v-if="!isCollapse">TradingOS</span>
        <span v-else>TS</span>
      </div>
      <el-menu
        :default-active="route.path"
        :collapse="isCollapse"
        @select="handleMenuSelect"
        class="sidebar-menu"
      >
        <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-button text @click="isCollapse = !isCollapse">
            <span v-if="isCollapse">展开</span>
            <span v-else>收起</span>
          </el-button>
        </div>
        <div class="header-right">
          <span class="app-title">A 股智能分析系统</span>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.main-layout {
  height: 100vh;
}

.el-aside {
  background-color: #304157;
  transition: width 0.3s;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  background-color: #263445;
}

.sidebar-menu {
  border-right: none;
  background-color: transparent;
}

.sidebar-menu :deep(.el-menu-item) {
  color: #bfcbd9;
}

.sidebar-menu :deep(.el-menu-item:hover),
.sidebar-menu :deep(.el-menu-item.is-active) {
  background-color: #263445;
  color: #409eff;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
}

.app-title {
  font-size: 16px;
  color: #303133;
  font-weight: 500;
}

.main-content {
  background-color: #f5f7fa;
  padding: 20px;
}
</style>
