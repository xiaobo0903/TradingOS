<template>
  <div class="ai-page">
    <div class="page-header">
      <h1 class="page-title">AI智能中心</h1>
    </div>

    <div class="ai-content">
      <!-- AI Model Status -->
      <div class="model-status-section">
        <div class="section-title">AI模型状态</div>
        <div class="model-cards">
          <div class="model-card">
            <div class="model-icon">🤖</div>
            <div class="model-info">
              <div class="model-name">Qwen3-14B</div>
              <div class="model-status running">
                <span class="status-dot"></span>
                运行中
              </div>
            </div>
            <div class="model-metrics">
              <div class="metric">
                <span class="metric-label">GPU</span>
                <el-progress :percentage="68" :stroke-width="4" :show-text="false" />
                <span class="metric-value">68%</span>
              </div>
              <div class="metric">
                <span class="metric-label">内存</span>
                <el-progress :percentage="45" :stroke-width="4" :show-text="false" />
                <span class="metric-value">45%</span>
              </div>
            </div>
          </div>

          <div class="model-card">
            <div class="model-icon">📊</div>
            <div class="model-info">
              <div class="model-name">指标分析引擎</div>
              <div class="model-status running">
                <span class="status-dot"></span>
                运行中
              </div>
            </div>
            <div class="model-metrics">
              <div class="metric">
                <span class="metric-label">请求</span>
                <span class="metric-value">1.2k/h</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- AI Tasks -->
      <div class="tasks-section">
        <div class="section-title">AI分析任务</div>
        <div class="task-grid">
          <div class="ai-task-card" @click="runMarketAnalysis">
            <div class="task-icon">📈</div>
            <div class="task-info">
              <div class="task-name">今日市场分析</div>
              <div class="task-desc">AI综合分析大盘走势</div>
            </div>
            <div class="task-action">
              <el-button type="primary" size="small">执行</el-button>
            </div>
          </div>

          <div class="ai-task-card" @click="runStockScreening">
            <div class="task-icon">🔍</div>
            <div class="task-info">
              <div class="task-name">股票筛选</div>
              <div class="task-desc">根据AI模型筛选强势股</div>
            </div>
            <div class="task-action">
              <el-button type="primary" size="small">执行</el-button>
            </div>
          </div>

          <div class="ai-task-card" @click="runRiskScan">
            <div class="task-icon">⚠️</div>
            <div class="task-info">
              <div class="task-name">风险扫描</div>
              <div class="task-desc">扫描持仓股票风险</div>
            </div>
            <div class="task-action">
              <el-button type="primary" size="small">执行</el-button>
            </div>
          </div>

          <div class="ai-task-card" @click="runDailyReview">
            <div class="task-icon">📋</div>
            <div class="task-info">
              <div class="task-name">每日复盘</div>
              <div class="task-desc">生成每日市场复盘报告</div>
            </div>
            <div class="task-action">
              <el-button type="primary" size="small">执行</el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- AI Reports -->
      <div class="reports-section">
        <div class="section-header">
          <span class="section-title">AI报告</span>
          <el-button text @click="loadMoreReports">
            查看更多
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>

        <div class="report-list">
          <div v-for="report in aiReports" :key="report.id" class="report-card">
            <div class="report-header">
              <span class="report-type" :class="report.type">{{ report.typeText }}</span>
              <span class="report-time">{{ report.time }}</span>
            </div>
            <div class="report-title">{{ report.title }}</div>
            <div class="report-summary">{{ report.summary }}</div>
            <div class="report-actions">
              <el-button type="primary" text size="small">查看详情</el-button>
              <el-button text size="small">分享</el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- AI Chat -->
      <div class="chat-section">
        <div class="section-title">AI问答</div>
        <div class="chat-container">
          <div class="chat-messages" ref="chatMessagesRef">
            <div v-for="(msg, index) in chatMessages" :key="index" class="chat-message" :class="msg.role">
              <div class="message-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
              <div class="message-content">
                <div class="message-text">{{ msg.content }}</div>
                <div class="message-time">{{ msg.time }}</div>
              </div>
            </div>
          </div>
          <div class="chat-input">
            <el-input
              v-model="chatInput"
              placeholder="输入股票相关问题..."
              type="textarea"
              :rows="2"
              @keyup.enter="sendMessage"
            />
            <el-button type="primary" @click="sendMessage">发送</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ArrowRight } from '@element-plus/icons-vue'

const chatInput = ref('')

const aiReports = ref([
  {
    id: 1,
    type: 'market',
    typeText: '市场分析',
    time: '10:30 今日',
    title: '今日大盘走势分析',
    summary: '上证指数早盘震荡上行，成交量温和放大。AI模型判断当前市场处于上涨趋势，建议关注主线板块。'
  },
  {
    id: 2,
    type: 'stock',
    typeText: '个股分析',
    time: '09:45 今日',
    title: '贵州茅台(600519)技术分析',
    summary: 'MACD形成金叉，位于零轴上方。RSI处于强势区域但未超买。主力资金持续流入，建议关注。'
  },
  {
    id: 3,
    type: 'risk',
    typeText: '风险提示',
    time: '昨日 15:30',
    title: '持仓风险扫描报告',
    summary: '检测到3只持仓股票存在短期风险，建议关注止损位设置。具体分析已生成详细报告。'
  }
])

const chatMessages = ref([
  {
    role: 'assistant',
    content: '您好！我是TradingOS AI助手。我可以帮助您分析股票、解读技术指标、了解市场动态。请问有什么可以帮助您的？',
    time: '10:00'
  }
])

const runMarketAnalysis = () => {
  console.log('Running market analysis...')
}

const runStockScreening = () => {
  console.log('Running stock screening...')
}

const runRiskScan = () => {
  console.log('Running risk scan...')
}

const runDailyReview = () => {
  console.log('Running daily review...')
}

const loadMoreReports = () => {
  console.log('Loading more reports...')
}

const sendMessage = () => {
  if (!chatInput.value.trim()) return

  chatMessages.value.push({
    role: 'user',
    content: chatInput.value,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  })

  // Simulate AI response
  setTimeout(() => {
    chatMessages.value.push({
      role: 'assistant',
      content: '感谢您的问题。根据您询问的内容，我需要更多上下文信息才能给出准确的分析。您可以告诉我具体是哪只股票，或者想要了解哪方面的分析？',
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    })
  }, 1000)

  chatInput.value = ''
}
</script>

<style scoped>
.ai-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.ai-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.model-status-section,
.tasks-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
}

.model-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.model-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.model-icon {
  font-size: 32px;
}

.model-info {
  flex: 1;
}

.model-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.model-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.model-status.running {
  color: var(--color-down);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-down);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.model-metrics {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 120px;
}

.metric {
  display: flex;
  align-items: center;
  gap: 8px;
}

.metric .el-progress {
  flex: 1;
}

.metric-label {
  font-size: 11px;
  color: var(--text-secondary);
  min-width: 30px;
}

.metric-value {
  font-size: 12px;
  font-weight: 600;
  min-width: 35px;
  text-align: right;
}

.task-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.ai-task-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: var(--transition-fast);
}

.ai-task-card:hover {
  background: var(--bg-card-hover);
}

.task-icon {
  font-size: 24px;
}

.task-info {
  flex: 1;
}

.task-name {
  font-weight: 600;
  margin-bottom: 2px;
}

.task-desc {
  font-size: 11px;
  color: var(--text-secondary);
}

.reports-section {
  grid-column: 1 / -1;
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

.report-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.report-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 16px;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.report-type {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 600;
}

.report-type.market {
  background: rgba(26, 115, 232, 0.15);
  color: var(--color-info);
}

.report-type.stock {
  background: rgba(114, 46, 209, 0.15);
  color: var(--color-ai);
}

.report-type.risk {
  background: rgba(245, 34, 45, 0.15);
  color: var(--color-up);
}

.report-time {
  font-size: 11px;
  color: var(--text-secondary);
}

.report-title {
  font-weight: 600;
  margin-bottom: 8px;
}

.report-summary {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin-bottom: 12px;
}

.report-actions {
  display: flex;
  gap: 8px;
}

.chat-section {
  grid-column: 1 / -1;
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 400px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-message {
  display: flex;
  gap: 12px;
}

.message-avatar {
  font-size: 24px;
}

.message-content {
  flex: 1;
}

.message-text {
  padding: 12px;
  border-radius: var(--radius-md);
  line-height: 1.5;
}

.chat-message.user .message-text {
  background: var(--color-info);
  color: white;
}

.chat-message.assistant .message-text {
  background: var(--bg-secondary);
}

.message-time {
  font-size: 10px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.chat-input {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.chat-input .el-input {
  flex: 1;
}
</style>
