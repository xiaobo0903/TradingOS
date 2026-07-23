<template>
  <div class="datacenter-page">
    <div class="page-header">
      <h1 class="page-title">数据中心</h1>
      <div class="header-actions">
        <el-button @click="refreshAll">
          <el-icon><Refresh /></el-icon>
          刷新全部
        </el-button>
      </div>
    </div>

    <!-- Data Status Overview -->
    <div class="status-overview">
      <div class="status-card">
        <div class="status-icon green">✓</div>
        <div class="status-info">
          <div class="status-label">行情数据</div>
          <div class="status-value green">正常</div>
        </div>
      </div>
      <div class="status-card">
        <div class="status-icon yellow">!</div>
        <div class="status-info">
          <div class="status-label">资金数据</div>
          <div class="status-value yellow">延迟</div>
        </div>
      </div>
      <div class="status-card">
        <div class="status-icon green">✓</div>
        <div class="status-info">
          <div class="status-label">新闻数据</div>
          <div class="status-value green">正常</div>
        </div>
      </div>
      <div class="status-card">
        <div class="status-icon green">✓</div>
        <div class="status-info">
          <div class="status-label">AI服务</div>
          <div class="status-value green">运行中</div>
        </div>
      </div>
    </div>

    <!-- Data Tasks -->
    <div class="tasks-section">
      <div class="section-header">
        <span class="section-title">数据任务</span>
        <el-radio-group v-model="taskFilter" size="small">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="normal">正常</el-radio-button>
          <el-radio-button label="abnormal">异常</el-radio-button>
        </el-radio-group>
      </div>

      <div class="task-list">
        <div v-for="task in filteredTasks" :key="task.id" class="task-card" :class="task.status">
          <div class="task-info">
            <div class="task-name">{{ task.name }}</div>
            <div class="task-meta">
              <span class="task-status" :class="task.status">{{ task.statusText }}</span>
              <span class="task-time">最后更新: {{ task.lastUpdate }}</span>
            </div>
          </div>
          <div class="task-stats">
            <div class="stat-item">
              <span class="stat-label">完整率</span>
              <span class="stat-value">{{ task.completeness }}%</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">延迟</span>
              <span class="stat-value">{{ task.delay }}秒</span>
            </div>
          </div>
          <div class="task-actions">
            <el-button size="small" @click="retryTask(task)">重试</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- Data Anomalies -->
    <div class="anomaly-section">
      <div class="section-header">
        <span class="section-title">异常数据</span>
      </div>

      <el-table :data="anomalies" stripe style="width: 100%">
        <el-table-column prop="stockCode" label="股票代码" width="100" />
        <el-table-column prop="stockName" label="股票名称" width="120" />
        <el-table-column prop="dataType" label="数据类型" width="100" />
        <el-table-column prop="errorTime" label="异常时间" width="160" />
        <el-table-column prop="errorType" label="错误类型" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '已修复' ? 'success' : 'warning'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button v-if="row.status !== '已修复'" type="primary" text size="small" @click="fixAnomaly(row)">
              重新获取
            </el-button>
            <el-button v-if="row.status !== '已修复'" type="warning" text size="small" @click="manualFix(row)">
              人工修正
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Data Collection Stats -->
    <div class="collection-stats">
      <div class="section-header">
        <span class="section-title">采集统计</span>
      </div>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">📊</div>
          <div class="stat-content">
            <div class="stat-value">5,260,000</div>
            <div class="stat-label">今日采集条数</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">⏱️</div>
          <div class="stat-content">
            <div class="stat-value">3秒</div>
            <div class="stat-label">平均延迟</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">✓</div>
          <div class="stat-content">
            <div class="stat-value">99.8%</div>
            <div class="stat-label">完整率</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">⚠</div>
          <div class="stat-content">
            <div class="stat-value">3</div>
            <div class="stat-label">异常数量</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Refresh } from '@element-plus/icons-vue'

const taskFilter = ref('all')

const tasks = ref([
  { id: 1, name: '实时行情采集', status: 'normal', statusText: '正常', lastUpdate: '10:30:05', completeness: 99.8, delay: 3 },
  { id: 2, name: '分钟K线生成', status: 'normal', statusText: '正常', lastUpdate: '10:30:00', completeness: 100, delay: 2 },
  { id: 3, name: '资金流计算', status: 'abnormal', statusText: '延迟', lastUpdate: '10:28:30', completeness: 95.2, delay: 120 },
  { id: 4, name: '技术指标计算', status: 'normal', statusText: '正常', lastUpdate: '10:29:00', completeness: 99.9, delay: 5 },
  { id: 5, name: '龙虎榜数据', status: 'normal', statusText: '正常', lastUpdate: '昨日 16:00', completeness: 100, delay: 0 },
  { id: 6, name: '新闻数据采集', status: 'normal', statusText: '正常', lastUpdate: '10:29:45', completeness: 98.5, delay: 8 }
])

const anomalies = ref([
  { stockCode: '600519', stockName: '贵州茅台', dataType: '成交量', errorTime: '10:31', errorType: '数据缺失', status: '待处理' },
  { stockCode: '000001', stockName: '平安银行', dataType: '资金流向', errorTime: '10:25', errorType: '数值异常', status: '已修复' },
  { stockCode: '002594', stockName: '比亚迪', dataType: '分钟K', errorTime: '10:20', errorType: '格式错误', status: '待处理' }
])

const filteredTasks = computed(() => {
  if (taskFilter.value === 'all') return tasks.value
  if (taskFilter.value === 'normal') return tasks.value.filter(t => t.status === 'normal')
  return tasks.value.filter(t => t.status === 'abnormal')
})

const refreshAll = () => {
  tasks.value.forEach(task => {
    task.lastUpdate = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  })
}

const retryTask = (task: any) => {
  task.status = 'normal'
  task.statusText = '正常'
  task.lastUpdate = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const fixAnomaly = (row: any) => {
  row.status = '已修复'
}

const manualFix = (row: any) => {
  console.log('Manual fix for:', row)
}
</script>

<style scoped>
.datacenter-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.status-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.status-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
}

.status-icon.green {
  background: rgba(82, 196, 26, 0.15);
  color: var(--color-down);
}

.status-icon.yellow {
  background: rgba(250, 173, 20, 0.15);
  color: var(--color-warning);
}

.status-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.status-value {
  font-size: 16px;
  font-weight: 600;
}

.status-value.green { color: var(--color-down); }
.status-value.yellow { color: var(--color-warning); }

.tasks-section,
.anomaly-section,
.collection-stats {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border-left: 3px solid transparent;
}

.task-card.normal {
  border-left-color: var(--color-down);
}

.task-card.abnormal {
  border-left-color: var(--color-warning);
}

.task-info {
  flex: 1;
}

.task-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.task-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
}

.task-status {
  padding: 2px 6px;
  border-radius: var(--radius-sm);
}

.task-status.normal {
  background: rgba(82, 196, 26, 0.15);
  color: var(--color-down);
}

.task-status.abnormal {
  background: rgba(250, 173, 20, 0.15);
  color: var(--color-warning);
}

.task-time {
  color: var(--text-secondary);
}

.task-stats {
  display: flex;
  gap: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: 11px;
  color: var(--text-secondary);
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-icon {
  font-size: 24px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.anomaly-section :deep(.el-table) {
  background-color: transparent;
}

.anomaly-section :deep(.el-table th.el-table__cell) {
  background-color: transparent;
  color: var(--text-secondary);
}
</style>
