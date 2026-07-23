<template>
  <div class="capital-page">
    <div class="page-header">
      <h1 class="page-title">资金分析</h1>
      <div class="time-selector">
        <el-radio-group v-model="timeRange" size="small">
          <el-radio-button label="today">今日</el-radio-button>
          <el-radio-button label="week">本周</el-radio-button>
          <el-radio-button label="month">本月</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- Capital Summary Cards -->
    <div class="capital-summary">
      <div class="summary-card main">
        <div class="card-icon">💰</div>
        <div class="card-info">
          <div class="card-label">主力净流入</div>
          <div class="card-value" :class="totalMainFlow >= 0 ? 'up' : 'down'">
            {{ totalMainFlow >= 0 ? '+' : '' }}{{ formatAmount(totalMainFlow) }}
          </div>
        </div>
      </div>

      <div class="summary-card">
        <div class="card-icon">🌊</div>
        <div class="card-info">
          <div class="card-label">北向资金</div>
          <div class="card-value up">{{ formatAmount(northMoney) }}</div>
        </div>
      </div>

      <div class="summary-card">
        <div class="card-icon">🏭</div>
        <div class="card-info">
          <div class="card-label">超大单</div>
          <div class="card-value" :class="superLargeNet >= 0 ? 'up' : 'down'">
            {{ superLargeNet >= 0 ? '+' : '' }}{{ formatAmount(superLargeNet) }}
          </div>
        </div>
      </div>

      <div class="summary-card">
        <div class="card-icon">📊</div>
        <div class="card-info">
          <div class="card-label">大单</div>
          <div class="card-value" :class="largeNet >= 0 ? 'up' : 'down'">
            {{ largeNet >= 0 ? '+' : '' }}{{ formatAmount(largeNet) }}
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="capital-content">
      <!-- Left: Flow Details -->
      <div class="flow-section">
        <div class="section-title">资金流向构成</div>
        <div class="flow-chart">
          <div class="flow-bars">
            <div class="flow-bar-item">
              <div class="bar-header">
                <span class="bar-name">超大单</span>
                <span class="bar-value up">{{ formatAmount(superLargeNet) }}</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill inflow" :style="{ width: `${inflowPercent(superLargeNet)}%` }"></div>
                <div class="bar-fill outflow" :style="{ width: `${outflowPercent(superLargeNet)}%` }"></div>
              </div>
            </div>

            <div class="flow-bar-item">
              <div class="bar-header">
                <span class="bar-name">大单</span>
                <span class="bar-value up">{{ formatAmount(largeNet) }}</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill inflow" :style="{ width: `${inflowPercent(largeNet)}%` }"></div>
                <div class="bar-fill outflow" :style="{ width: `${outflowPercent(largeNet)}%` }"></div>
              </div>
            </div>

            <div class="flow-bar-item">
              <div class="bar-header">
                <span class="bar-name">中单</span>
                <span class="bar-value down">{{ formatAmount(mediumNet) }}</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill inflow" :style="{ width: `${inflowPercent(mediumNet)}%` }"></div>
                <div class="bar-fill outflow" :style="{ width: `${outflowPercent(mediumNet)}%` }"></div>
              </div>
            </div>

            <div class="flow-bar-item">
              <div class="bar-header">
                <span class="bar-name">散户</span>
                <span class="bar-value down">{{ formatAmount(smallNet) }}</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill inflow" :style="{ width: `${inflowPercent(smallNet)}%` }"></div>
                <div class="bar-fill outflow" :style="{ width: `${outflowPercent(smallNet)}%` }"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="flow-legend">
          <div class="legend-item">
            <span class="legend-dot inflow"></span>
            <span class="legend-text">流入</span>
          </div>
          <div class="legend-item">
            <span class="legend-dot outflow"></span>
            <span class="legend-text">流出</span>
          </div>
        </div>
      </div>

      <!-- Right: AI Analysis -->
      <div class="analysis-section">
        <div class="section-title">AI主力行为分析</div>
        <AIBox :analysis="mainForceAnalysis" />

        <div class="behavior-list">
          <div class="behavior-item">
            <div class="behavior-header">
              <span class="behavior-icon">📈</span>
              <span class="behavior-name">吸筹阶段</span>
            </div>
            <div class="behavior-desc">
              检测到低位放量特征，主力资金持续流入，换手率温和放大。
            </div>
            <div class="behavior-prob">
              <span class="prob-label">概率</span>
              <el-progress :percentage="72" :stroke-width="8" :show-text="false" color="#722ED1" />
              <span class="prob-value">72%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Dragon Tiger List -->
    <div class="dragon-section">
      <div class="section-title">龙虎榜</div>
      <el-table :data="dragonList" stripe style="width: 100%">
        <el-table-column prop="date" label="日期" width="100" />
        <el-table-column prop="stockName" label="股票" width="120">
          <template #default="{ row }">
            <div>
              <div class="stock-name">{{ row.stockName }}</div>
              <div class="stock-code">{{ row.stockCode }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="上榜原因" />
        <el-table-column prop="buyAmount" label="买入金额" width="120">
          <template #default="{ row }">
            <span class="text-up">{{ formatAmount(row.buyAmount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="sellAmount" label="卖出金额" width="120">
          <template #default="{ row }">
            <span class="text-down">{{ formatAmount(row.sellAmount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="netAmount" label="净买入" width="120">
          <template #default="{ row }">
            <span :class="row.netAmount >= 0 ? 'text-up' : 'text-down'">
              {{ row.netAmount >= 0 ? '+' : '' }}{{ formatAmount(row.netAmount) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import AIBox from '@/components/Common/AIBox.vue'

const timeRange = ref('today')

const totalMainFlow = ref(1250000000)
const northMoney = ref(285000000)
const superLargeNet = ref(850000000)
const largeNet = ref(520000000)
const mediumNet = ref(-380000000)
const smallNet = ref(-620000000)

const mainForceAnalysis = computed(() => ({
  trend: '吸筹阶段',
  confidence: 72,
  signals: ['低位放量', '换手率提升', '价格稳定'],
  risks: ['需关注后续量能是否持续'],
  suggestion: '保持观察，等待确认信号'
}))

const dragonList = ref([
  { date: '07-22', stockName: '贵州茅台', stockCode: '600519', reason: '连续3日涨幅偏离值达20%', buyAmount: 5800000000, sellAmount: 4200000000, netAmount: 1600000000 },
  { date: '07-22', stockName: '比亚迪', stockCode: '002594', reason: '日涨幅偏离值达7%', buyAmount: 3200000000, sellAmount: 2800000000, netAmount: 400000000 },
  { date: '07-21', stockName: '宁德时代', stockCode: '300750', reason: '融资融券信息', buyAmount: 4500000000, sellAmount: 5100000000, netAmount: -600000000 },
  { date: '07-21', stockName: '招商银行', stockCode: '600036', reason: '沪股通买入卖出', buyAmount: 2100000000, sellAmount: 1800000000, netAmount: 300000000 }
])

const formatAmount = (amount: number): string => {
  const absAmount = Math.abs(amount)
  if (absAmount >= 100000000) {
    return (amount < 0 ? '-' : '') + (absAmount / 100000000).toFixed(2) + '亿'
  } else if (absAmount >= 10000) {
    return (amount < 0 ? '-' : '') + (absAmount / 10000).toFixed(2) + '万'
  }
  return amount.toFixed(2)
}

const inflowPercent = (net: number): number => {
  const total = Math.abs(net) + Math.abs(net) * 0.5
  return Math.min((Math.abs(net) / total) * 100, 100)
}

const outflowPercent = (net: number): number => {
  return net >= 0 ? 0 : Math.min((Math.abs(net) / (Math.abs(net) + Math.abs(net) * 0.5)) * 100, 100)
}
</script>

<style scoped>
.capital-page {
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

.capital-summary {
  display: grid;
  grid-template-columns: 2fr repeat(3, 1fr);
  gap: 12px;
}

.summary-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.summary-card.main {
  background: linear-gradient(135deg, var(--bg-card), rgba(114, 46, 209, 0.2));
}

.card-icon {
  font-size: 28px;
}

.card-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.card-value {
  font-size: 20px;
  font-weight: 700;
}

.card-value.up { color: var(--color-up); }
.card-value.down { color: var(--color-down); }

.capital-content {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 16px;
}

.flow-section,
.analysis-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
}

.flow-bars {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.flow-bar-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bar-name {
  font-size: 13px;
  font-weight: 500;
}

.bar-value {
  font-size: 14px;
  font-weight: 600;
}

.bar-value.up { color: var(--color-up); }
.bar-value.down { color: var(--color-down); }

.bar-track {
  height: 12px;
  background: var(--bg-secondary);
  border-radius: 6px;
  display: flex;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.bar-fill.inflow { background: var(--color-up); }
.bar-fill.outflow { background: var(--color-down); }

.flow-legend {
  display: flex;
  gap: 24px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.legend-dot.inflow { background: var(--color-up); }
.legend-dot.outflow { background: var(--color-down); }

.legend-text {
  font-size: 12px;
  color: var(--text-secondary);
}

.behavior-list {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.behavior-item {
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.behavior-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.behavior-icon {
  font-size: 16px;
}

.behavior-name {
  font-weight: 600;
}

.behavior-desc {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.behavior-prob {
  display: flex;
  align-items: center;
  gap: 8px;
}

.prob-label {
  font-size: 11px;
  color: var(--text-secondary);
}

.prob-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-ai);
}

.dragon-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
}

.dragon-section :deep(.el-table) {
  background-color: transparent;
}

.dragon-section :deep(.el-table th.el-table__cell) {
  background-color: transparent;
  color: var(--text-secondary);
  font-weight: 500;
}

.stock-name {
  font-weight: 600;
}

.stock-code {
  font-size: 11px;
  color: var(--text-secondary);
}
</style>
