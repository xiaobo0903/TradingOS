<template>
  <footer class="status-bar">
    <div class="status-left">
      <span class="status-item">
        <span class="dot online"></span>
        数据连接正常
      </span>
      <span class="status-item">
        <el-icon><Clock /></el-icon>
        {{ currentTime }}
      </span>
    </div>

    <div class="status-center">
      <span class="status-item">数据延迟: 3秒</span>
      <span class="status-item">今日采集: 526万条</span>
    </div>

    <div class="status-right">
      <span class="status-item">TradingOS v1.0</span>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Clock } from '@element-plus/icons-vue'

const currentTime = ref('')
let timer: number | null = null

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(() => {
  updateTime()
  timer = window.setInterval(updateTime, 1000)
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<style scoped>
.status-bar {
  height: var(--statusbar-height);
  background-color: var(--bg-card);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  font-size: 12px;
  color: var(--text-secondary);
}

.status-left,
.status-center,
.status-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--text-secondary);
}

.dot.online {
  background-color: var(--color-down);
}

.dot.offline {
  background-color: var(--color-up);
}
</style>
