<template>
  <div class="dashboard">
    <!-- Market Overview -->
    <div class="market-overview">
      <div
        v-for="index in marketStore.indices"
        :key="index.code"
        class="mkt-card"
      >
        <div class="label">{{ index.name }}</div>
        <div class="value">{{ index.price.toFixed(2) }}</div>
        <div class="chg" :class="index.change >= 0 ? 'up' : 'down'">
          {{ index.change >= 0 ? '+' : '' }}{{ index.change.toFixed(2) }}
          ({{ index.changePercent >= 0 ? '+' : '' }}{{ index.changePercent.toFixed(2) }}%)
        </div>
        <div class="sub">
          <div>
            <span class="label">成交额</span>
            <span class="val">{{ formatAmount(index.amount) }}</span>
          </div>
        </div>
      </div>

      <!-- Market Stats -->
      <div class="mkt-stats">
        <div class="stats-row">
          <div class="stat-item">
            <span class="stat-label">上涨</span>
            <span class="stat-value up">{{ marketStore.upCount }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">下跌</span>
            <span class="stat-value down">{{ marketStore.downCount }}</span>
          </div>
        </div>
        <div class="stats-row">
          <div class="stat-item">
            <span class="stat-label">涨停</span>
            <span class="stat-value limit-up">{{ marketStore.limitUpCount }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">跌停</span>
            <span class="stat-value limit-down">{{ marketStore.limitDownCount }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- AI Market Analysis -->
    <div class="section ai-section">
      <div class="section-header">
        <span class="section-title">AI市场解读</span>
      </div>
      <div class="ai-content">
        <div class="ai-info">
          <div class="ai-market">
            <div class="ai-label">今日市场</div>
            <div class="ai-main">{{ marketStore.aiAnalysis.trend }}</div>
          </div>
          <div class="ai-detail">
            <div class="ai-row">
              <span class="ai-row-label">AI评分</span>
              <el-rate v-model="aiScore" disabled text-color="#722ED1" />
            </div>
            <div class="ai-row">
              <span class="ai-row-label">趋势</span>
              <span class="ai-trend">
                <span v-for="i in 4" :key="i" class="star">★</span>
                <span v-for="i in 1" :key="'empty'+i" class="star empty">☆</span>
              </span>
            </div>
            <div class="ai-row">
              <span class="ai-row-label">风险</span>
              <span class="ai-risk">
                <span v-for="i in 3" :key="i" class="star">★</span>
                <span v-for="i in 2" :key="'empty'+i" class="star empty">☆</span>
              </span>
            </div>
          </div>
        </div>
        <div class="ai-reason">
          <div class="reason-item">
            <span class="reason-label">上涨原因</span>
            <span class="reason-text">资金持续流入，成交量放大</span>
          </div>
          <div class="reason-item">
            <span class="reason-label">风险因素</span>
            <span class="reason-text">外部市场波动影响</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Hot Stocks -->
    <div class="section hot-section">
      <div class="section-header">
        <span class="section-title">热点股票 TOP10</span>
      </div>
      <div class="hot-table">
        <el-table :data="marketStore.hotStocks" stripe style="width: 100%">
          <el-table-column prop="name" label="股票" width="120">
            <template #default="{ row }">
              <div class="stock-name">
                <span class="name">{{ row.name }}</span>
                <span class="code">{{ row.code }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="change" label="涨幅" width="100">
            <template #default="{ row }">
              <span :class="row.change >= 0 ? 'text-up' : 'text-down'">
                {{ row.change >= 0 ? '+' : '' }}{{ row.change.toFixed(2) }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="turnover" label="换手率" width="100">
            <template #default="{ row }">
              {{ row.turnover.toFixed(1) }}%
            </template>
          </el-table-column>
          <el-table-column prop="volumeRatio" label="量比" width="80">
            <template #default="{ row }">
              {{ row.volumeRatio.toFixed(1) }}
            </template>
          </el-table-column>
          <el-table-column prop="aiScore" label="AI评分" width="120">
            <template #default="{ row }">
              <div class="ai-score">
                <el-progress
                  :percentage="row.aiScore"
                  :color="getScoreColor(row.aiScore)"
                  :show-text="false"
                  :stroke-width="6"
                />
                <span class="score-text">{{ row.aiScore }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作">
            <template #default="{ row }">
              <el-button type="primary" text @click="goToStock(row.code)">分析</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- Capital Flow -->
    <div class="section capital-section">
      <div class="section-header">
        <span class="section-title">资金流向</span>
      </div>
      <div class="capital-cards">
        <div class="capital-card">
          <div class="capital-icon">💰</div>
          <div class="capital-info">
            <div class="capital-label">主力流入</div>
            <div class="capital-value up">{{ formatAmount(marketStore.capital.mainInflow) }}</div>
          </div>
        </div>
        <div class="capital-card">
          <div class="capital-icon">🌊</div>
          <div class="capital-info">
            <div class="capital-label">北向资金</div>
            <div class="capital-value up">{{ formatAmount(marketStore.capital.northMoney) }}</div>
          </div>
        </div>
        <div class="capital-card">
          <div class="capital-icon">🏭</div>
          <div class="capital-info">
            <div class="capital-label">行业资金</div>
            <div class="capital-value up">{{ formatAmount(marketStore.capital.industryMoney) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMarketStore } from '@/stores/market'

const router = useRouter()
const marketStore = useMarketStore()

const aiScore = computed(() => marketStore.aiAnalysis.score / 20)

const formatAmount = (amount: number): string => {
  if (amount >= 100000000) {
    return (amount / 100000000).toFixed(2) + '亿'
  } else if (amount >= 10000) {
    return (amount / 10000).toFixed(2) + '万'
  }
  return amount.toFixed(2)
}

const getScoreColor = (score: number): string => {
  if (score >= 80) return '#52C41A'
  if (score >= 60) return '#FAAD14'
  return '#F5222D'
}

const goToStock = (code: string) => {
  router.push(`/stock/${code}`)
}
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Market Overview */
.market-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr) 240px;
  gap: 12px;
}

.mkt-card {
  background: var(--bg-card);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-lg);
  padding: 16px;
}

.mkt-card .label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.mkt-card .value {
  font-size: 22px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.mkt-card .chg {
  font-size: 14px;
  font-weight: 600;
  margin-top: 6px;
}

.mkt-card .chg.up { color: var(--color-up); }
.mkt-card .chg.down { color: var(--color-down); }

.mkt-card .sub {
  display: flex;
  gap: 12px;
  margin-top: 8px;
  font-size: 12px;
}

.mkt-card .sub .label { color: var(--text-secondary); margin: 0; font-size: 11px; }
.mkt-card .sub .val { color: var(--text-primary); font-weight: 500; }

.mkt-stats {
  background: var(--bg-card);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stats-row {
  display: flex;
  gap: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
}

.stat-value.up { color: var(--color-up); }
.stat-value.down { color: var(--color-down); }
.stat-value.limit-up { color: #F5222D; }
.stat-value.limit-down { color: #52C41A; }

/* Section */
.section {
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

/* AI Section */
.ai-section .ai-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.ai-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ai-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.ai-main {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-ai);
}

.ai-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-row-label {
  font-size: 12px;
  color: var(--text-secondary);
  width: 48px;
}

.ai-trend, .ai-risk {
  display: flex;
  gap: 2px;
}

.star {
  color: #FAAD14;
  font-size: 14px;
}

.star.empty {
  color: var(--text-muted);
}

.ai-reason {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.reason-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.reason-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.reason-text {
  font-size: 14px;
  color: var(--text-primary);
}

/* Hot Table */
.hot-table :deep(.el-table) {
  background-color: transparent;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: var(--bg-card);
}

.hot-table :deep(.el-table th.el-table__cell) {
  background-color: transparent;
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 12px;
}

.hot-table :deep(.el-table td.el-table__cell) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.stock-name {
  display: flex;
  flex-direction: column;
}

.stock-name .name {
  font-weight: 600;
}

.stock-name .code {
  font-size: 11px;
  color: var(--text-secondary);
}

.ai-score {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-score .el-progress {
  flex: 1;
}

.score-text {
  font-size: 12px;
  font-weight: 600;
  min-width: 24px;
}

/* Capital Cards */
.capital-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.capital-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
}

.capital-icon {
  font-size: 28px;
}

.capital-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.capital-value {
  font-size: 18px;
  font-weight: 700;
}

.capital-value.up { color: var(--color-up); }
.capital-value.down { color: var(--color-down); }
</style>
