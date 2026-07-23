<template>
  <header class="header">
    <div class="header-left">
      <div class="logo">
        <span class="logo-icon">📊</span>
        <span class="logo-text">TradingOS</span>
      </div>
    </div>

    <div class="header-center">
      <div class="market-status">
        <span class="status-label">市场状态</span>
        <span class="status-value" :class="marketOpen ? 'open' : 'closed'">
          {{ marketOpen ? '交易中' : '已休市' }}
        </span>
      </div>
      <div class="ai-status">
        <span class="status-label">AI状态</span>
        <span class="status-value ai">
          <el-icon><Monitor /></el-icon>
          运行正常
        </span>
      </div>
    </div>

    <div class="header-right">
      <el-dropdown trigger="click">
        <div class="user-info">
          <el-icon><User /></el-icon>
          <span>交易者</span>
          <el-icon><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item>个人设置</el-dropdown-item>
            <el-dropdown-item>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { User, ArrowDown, Monitor } from '@element-plus/icons-vue'

const marketOpen = ref(true)
let timer: number | null = null

const checkMarketStatus = () => {
  const now = new Date()
  const hours = now.getHours()
  const minutes = now.getMinutes()
  const day = now.getDay()

  // 周末休市
  if (day === 0 || day === 6) {
    marketOpen.value = false
    return
  }

  // A股交易时间: 9:30-11:30, 13:00-15:00
  const totalMinutes = hours * 60 + minutes
  marketOpen.value = (totalMinutes >= 570 && totalMinutes <= 690) || (totalMinutes >= 780 && totalMinutes <= 900)
}

onMounted(() => {
  checkMarketStatus()
  timer = window.setInterval(checkMarketStatus, 60000)
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<style scoped>
.header {
  height: var(--header-height);
  background-color: var(--bg-card);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-center {
  display: flex;
  align-items: center;
  gap: 24px;
}

.market-status,
.ai-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-label {
  color: var(--text-secondary);
  font-size: 12px;
}

.status-value {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
}

.status-value.open {
  background-color: rgba(82, 196, 26, 0.15);
  color: var(--color-down);
}

.status-value.closed {
  background-color: rgba(136, 146, 166, 0.15);
  color: var(--text-secondary);
}

.status-value.ai {
  background-color: rgba(114, 46, 209, 0.15);
  color: var(--color-ai);
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition-fast);
}

.user-info:hover {
  background-color: var(--bg-card-hover);
}
</style>
