<template>
  <div class="ai-box">
    <div class="ai-header">
      <div class="ai-title">
        <span class="ai-icon">🤖</span>
        <span class="ai-label">AI智能分析</span>
      </div>
      <div class="ai-trend" :class="analysis?.trend === '上涨趋势' ? 'up' : analysis?.trend === '下跌趋势' ? 'down' : 'neutral'">
        {{ analysis?.trend || '暂无数据' }}
      </div>
    </div>

    <div class="ai-body">
      <div class="ai-main">
        <div class="confidence-row">
          <span class="conf-label">可信度</span>
          <div class="confidence-bar">
            <div class="confidence-fill" :style="{ width: `${analysis?.confidence || 0}%` }"></div>
          </div>
          <span class="conf-value">{{ analysis?.confidence || 0 }}%</span>
        </div>
      </div>

      <div class="ai-signals" v-if="analysis?.signals?.length">
        <div class="signals-label">分析依据</div>
        <div class="signals-list">
          <div v-for="(signal, index) in analysis.signals" :key="index" class="signal-item">
            <span class="signal-check">✓</span>
            <span class="signal-text">{{ signal }}</span>
          </div>
        </div>
      </div>

      <div class="ai-risks" v-if="analysis?.risks?.length">
        <div class="risks-label">风险提示</div>
        <div class="risks-list">
          <div v-for="(risk, index) in analysis.risks" :key="index" class="risk-item">
            <span class="risk-icon">⚠</span>
            <span class="risk-text">{{ risk }}</span>
          </div>
        </div>
      </div>

      <div class="ai-suggestion" v-if="analysis?.suggestion">
        <div class="suggestion-label">操作建议</div>
        <div class="suggestion-text">{{ analysis.suggestion }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface AIAnalysis {
  trend: string
  confidence: number
  signals: string[]
  risks: string[]
  suggestion: string
}

defineProps<{
  analysis?: AIAnalysis | null
}>()
</script>

<style scoped>
.ai-box {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
  border-left: 3px solid var(--color-ai);
}

.ai-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.ai-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-icon {
  font-size: 20px;
}

.ai-label {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-ai);
}

.ai-trend {
  padding: 4px 12px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
}

.ai-trend.up {
  background: rgba(245, 34, 45, 0.15);
  color: var(--color-up);
}

.ai-trend.down {
  background: rgba(82, 196, 26, 0.15);
  color: var(--color-down);
}

.ai-trend.neutral {
  background: rgba(136, 146, 166, 0.15);
  color: var(--text-secondary);
}

.ai-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.confidence-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.conf-label {
  font-size: 13px;
  color: var(--text-secondary);
  min-width: 50px;
}

.confidence-bar {
  flex: 1;
  height: 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-ai), #9B59B6);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.conf-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ai);
  min-width: 45px;
  text-align: right;
}

.signals-label,
.risks-label,
.suggestion-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.signals-list,
.risks-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.signal-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.signal-check {
  color: var(--color-down);
  font-weight: 700;
}

.signal-text {
  color: var(--text-primary);
}

.risk-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.risk-icon {
  color: var(--color-warning);
}

.risk-text {
  color: var(--text-primary);
}

.suggestion-text {
  font-size: 14px;
  color: var(--text-primary);
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}
</style>
