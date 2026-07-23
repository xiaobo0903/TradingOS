<template>
  <div class="stock-detail">
    <!-- Search Header -->
    <div class="search-header">
      <el-autocomplete
        v-model="searchQuery"
        :fetch-suggestions="searchStock"
        placeholder="搜索股票代码或名称..."
        :trigger-on-focus="false"
        clearable
        class="stock-search"
        @select="handleSelectStock"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
        <template #default="{ item }">
          <div class="search-item">
            <span class="stock-name">{{ item.value }}</span>
            <span class="stock-code">{{ item.code }}</span>
          </div>
        </template>
      </el-autocomplete>
    </div>

    <div v-if="stockStore.currentStock" class="stock-content">
      <!-- Stock Info -->
      <div class="stock-info-card">
        <div class="stock-header">
          <div class="stock-title">
            <h2>{{ stockStore.currentStock.name }}</h2>
            <span class="stock-code">{{ stockStore.currentStock.code }}</span>
          </div>
          <el-button
            :type="isWatched ? 'warning' : 'default'"
            text
            @click="toggleWatch"
          >
            {{ isWatched ? '⭐ 已自选' : '☆ 加自选' }}
          </el-button>
        </div>

        <div class="stock-price">
          <span class="price">{{ stockStore.currentStock.price.toFixed(2) }}</span>
          <span class="change" :class="stockStore.currentStock.change >= 0 ? 'up' : 'down'">
            {{ stockStore.currentStock.change >= 0 ? '+' : '' }}{{ stockStore.currentStock.change.toFixed(2) }}
            ({{ stockStore.currentStock.changePercent >= 0 ? '+' : '' }}{{ stockStore.currentStock.changePercent.toFixed(2) }}%)
          </span>
        </div>

        <div class="stock-indicators">
          <div class="indicator-item">
            <span class="label">成交额</span>
            <span class="value">{{ formatAmount(stockStore.currentStock.amount) }}</span>
          </div>
          <div class="indicator-item">
            <span class="label">换手率</span>
            <span class="value">{{ stockStore.currentStock.turnover.toFixed(2) }}%</span>
          </div>
          <div class="indicator-item">
            <span class="label">量比</span>
            <span class="value">{{ stockStore.currentStock.volumeRatio.toFixed(2) }}</span>
          </div>
          <div class="indicator-item">
            <span class="label">市盈率PE</span>
            <span class="value">{{ stockStore.currentStock.pe.toFixed(2) }}</span>
          </div>
          <div class="indicator-item">
            <span class="label">市净率PB</span>
            <span class="value">{{ stockStore.currentStock.pb.toFixed(2) }}</span>
          </div>
          <div class="indicator-item">
            <span class="label">52周高</span>
            <span class="value">{{ stockStore.currentStock.high52w.toFixed(2) }}</span>
          </div>
          <div class="indicator-item">
            <span class="label">52周低</span>
            <span class="value">{{ stockStore.currentStock.low52w.toFixed(2) }}</span>
          </div>
        </div>
      </div>

      <!-- K线图 -->
      <div class="chart-section">
        <KLineChart
          :kline-data="klineData"
          :indicator-data="stockStore.indicatorData"
        />
      </div>

      <!-- 技术指标面板 -->
      <div class="indicator-section">
        <div class="section-title">技术指标</div>
        <div class="indicator-tabs">
          <el-tabs v-model="activeIndicator" class="indicator-tabs-content">
            <el-tab-pane label="MACD" name="macd">
              <div class="indicator-content" v-if="stockStore.indicatorData">
                <div class="indicator-row">
                  <span class="ind-label">DIF</span>
                  <span class="ind-value">{{ stockStore.indicatorData.dif.toFixed(3) }}</span>
                </div>
                <div class="indicator-row">
                  <span class="ind-label">DEA</span>
                  <span class="ind-value">{{ stockStore.indicatorData.dea.toFixed(3) }}</span>
                </div>
                <div class="indicator-row">
                  <span class="ind-label">MACD柱</span>
                  <span class="ind-value" :class="stockStore.indicatorData.macd >= 0 ? 'up' : 'down'">
                    {{ stockStore.indicatorData.macd.toFixed(3) }}
                  </span>
                </div>
                <div class="indicator-signal">
                  <el-tag :type="stockStore.indicatorData.dif > stockStore.indicatorData.dea ? 'success' : 'danger'">
                    {{ stockStore.indicatorData.dif > stockStore.indicatorData.dea ? '金叉' : '死叉' }}
                  </el-tag>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="RSI" name="rsi">
              <div class="indicator-content" v-if="stockStore.indicatorData">
                <div class="indicator-row">
                  <span class="ind-label">RSI6</span>
                  <span class="ind-value">{{ stockStore.indicatorData.rsi6.toFixed(2) }}</span>
                </div>
                <div class="indicator-row">
                  <span class="ind-label">RSI12</span>
                  <span class="ind-value">{{ stockStore.indicatorData.rsi12.toFixed(2) }}</span>
                </div>
                <div class="indicator-row">
                  <span class="ind-label">RSI24</span>
                  <span class="ind-value">{{ stockStore.indicatorData.rsi24.toFixed(2) }}</span>
                </div>
                <div class="indicator-signal">
                  <el-tag v-if="stockStore.indicatorData.rsi6 > 80" type="danger">超买</el-tag>
                  <el-tag v-else-if="stockStore.indicatorData.rsi6 < 20" type="success">超卖</el-tag>
                  <el-tag v-else type="info">正常</el-tag>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="BOLL" name="boll">
              <div class="indicator-content" v-if="stockStore.indicatorData">
                <div class="indicator-row">
                  <span class="ind-label">上轨</span>
                  <span class="ind-value up">{{ stockStore.indicatorData.bollUpper?.toFixed(2) }}</span>
                </div>
                <div class="indicator-row">
                  <span class="ind-label">中轨</span>
                  <span class="ind-value">{{ stockStore.indicatorData.bollMid?.toFixed(2) }}</span>
                </div>
                <div class="indicator-row">
                  <span class="ind-label">下轨</span>
                  <span class="ind-value down">{{ stockStore.indicatorData.bollLower?.toFixed(2) }}</span>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="KDJ" name="kdj">
              <div class="indicator-content" v-if="stockStore.indicatorData">
                <div class="indicator-row">
                  <span class="ind-label">K</span>
                  <span class="ind-value">{{ stockStore.indicatorData.kdjK.toFixed(2) }}</span>
                </div>
                <div class="indicator-row">
                  <span class="ind-label">D</span>
                  <span class="ind-value">{{ stockStore.indicatorData.kdjD.toFixed(2) }}</span>
                </div>
                <div class="indicator-row">
                  <span class="ind-label">J</span>
                  <span class="ind-value" :class="stockStore.indicatorData.kdjJ > 80 ? 'up' : stockStore.indicatorData.kdjJ < 20 ? 'down' : ''">
                    {{ stockStore.indicatorData.kdjJ.toFixed(2) }}
                  </span>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>

      <!-- AI分析 -->
      <div class="ai-section">
        <AIBox :analysis="stockStore.aiAnalysis" />
      </div>

      <!-- 资金分析 -->
      <div class="capital-section">
        <div class="section-title">资金分析</div>
        <div class="capital-detail" v-if="stockStore.capitalData">
          <div class="capital-row">
            <span class="cap-label">主力净流入</span>
            <span class="cap-value" :class="stockStore.capitalData.mainInflow >= 0 ? 'up' : 'down'">
              {{ stockStore.capitalData.mainInflow >= 0 ? '+' : '' }}{{ formatAmount(stockStore.capitalData.mainInflow) }}
            </span>
          </div>
          <div class="capital-bars">
            <div class="capital-bar">
              <span class="bar-label">超大单</span>
              <div class="bar-container">
                <div
                  class="bar-fill up"
                  :style="{ width: `${Math.min(Math.abs(stockStore.capitalData.superLargeIn) / 100000000, 100)}%` }"
                ></div>
              </div>
              <span class="bar-value">{{ formatAmount(stockStore.capitalData.superLargeIn) }}</span>
            </div>
            <div class="capital-bar">
              <span class="bar-label">大单</span>
              <div class="bar-container">
                <div
                  class="bar-fill up"
                  :style="{ width: `${Math.min(Math.abs(stockStore.capitalData.largeIn) / 100000000, 100)}%` }"
                ></div>
              </div>
              <span class="bar-value">{{ formatAmount(stockStore.capitalData.largeIn) }}</span>
            </div>
            <div class="capital-bar">
              <span class="bar-label">中单</span>
              <div class="bar-container">
                <div
                  class="bar-fill down"
                  :style="{ width: `${Math.min(Math.abs(stockStore.capitalData.mediumOut) / 100000000, 100)}%` }"
                ></div>
              </div>
              <span class="bar-value">{{ formatAmount(stockStore.capitalData.mediumOut) }}</span>
            </div>
            <div class="capital-bar">
              <span class="bar-label">散户</span>
              <div class="bar-container">
                <div
                  class="bar-fill down"
                  :style="{ width: `${Math.min(Math.abs(stockStore.capitalData.smallOut) / 100000000, 100)}%` }"
                ></div>
              </div>
              <span class="bar-value">{{ formatAmount(stockStore.capitalData.smallOut) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <div class="empty-icon">📊</div>
      <div class="empty-text">搜索股票开始分析</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { useStockStore } from '@/stores/stock'
import KLineChart from '@/components/Charts/KLineChart.vue'
import AIBox from '@/components/Common/AIBox.vue'

const route = useRoute()
const router = useRouter()
const stockStore = useStockStore()

const searchQuery = ref('')
const activeIndicator = ref('macd')

// Mock data for demo
const mockKlineData = () => {
  const data = []
  const basePrice = 1650
  const today = new Date()

  for (let i = 60; i >= 0; i--) {
    const date = new Date(today)
    date.setDate(date.getDate() - i)
    const open = basePrice + (Math.random() - 0.5) * 50
    const close = open + (Math.random() - 0.5) * 30
    const high = Math.max(open, close) + Math.random() * 20
    const low = Math.min(open, close) - Math.random() * 20
    const volume = Math.floor(Math.random() * 10000000) + 5000000

    data.push({
      date: `${date.getMonth() + 1}/${date.getDate()}`,
      open: parseFloat(open.toFixed(2)),
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      close: parseFloat(close.toFixed(2)),
      volume,
      ma5: parseFloat((close * (1 + (Math.random() - 0.5) * 0.02)).toFixed(2)),
      ma10: parseFloat((close * (1 + (Math.random() - 0.5) * 0.03)).toFixed(2)),
      ma20: parseFloat((close * (1 + (Math.random() - 0.5) * 0.04)).toFixed(2))
    })

    basePrice + (close - basePrice) * 0.1
  }

  return data
}

const mockIndicatorData = () => ({
  ma5: 1652.35,
  ma10: 1648.72,
  ma20: 1645.18,
  ma60: 1638.45,
  dif: 12.35,
  dea: 8.67,
  macd: 7.36,
  rsi6: 68.5,
  rsi12: 65.3,
  rsi24: 62.8,
  bollUpper: 1685.25,
  bollMid: 1650.0,
  bollLower: 1614.75,
  kdjK: 72.5,
  kdjD: 68.3,
  kdjJ: 81.2
})

const mockCapitalData = () => ({
  mainInflow: 125000000,
  mainOutflow: 98000000,
  superLargeIn: 85000000,
  superLargeOut: 62000000,
  largeIn: 68000000,
  largeOut: 55000000,
  mediumIn: 32000000,
  mediumOut: 45000000,
  smallIn: 18000000,
  smallOut: 35000000
})

const mockAIAnalysis = () => ({
  trend: '上涨趋势',
  confidence: 78,
  signals: ['MACD金叉', 'BOLL突破上轨', '放量上涨', '主力资金流入'],
  risks: ['RSI接近超买区域', '短线涨幅较大'],
  suggestion: '等待回踩20日均线后关注'
})

const klineData = ref(mockKlineData())

const isWatched = computed(() => {
  if (!stockStore.currentStock) return false
  return stockStore.watchList.includes(stockStore.currentStock.code)
})

const searchStock = (query: string, cb: (results: Array<{ value: string; code: string }>) => void) => {
  const mockStocks = [
    { value: '贵州茅台', code: '600519' },
    { value: '五粮液', code: '000858' },
    { value: '比亚迪', code: '002594' },
    { value: '招商银行', code: '600036' },
    { value: '中国平安', code: '601318' },
    { value: '宁德时代', code: '300750' },
    { value: '隆基绿能', code: '601012' },
    { value: '海康威视', code: '002415' }
  ]

  const results = mockStocks.filter(s =>
    s.value.includes(query) || s.code.includes(query)
  )
  cb(results)
}

const handleSelectStock = (item: { value: string; code: string }) => {
  loadStockData(item.code)
  router.push(`/stock/${item.code}`)
}

const loadStockData = (code: string) => {
  stockStore.setCurrentStock({
    code,
    name: code === '600519' ? '贵州茅台' : '五粮液',
    price: 1650.25,
    change: 38.52,
    changePercent: 2.39,
    volume: 3562000,
    amount: 5870000000,
    turnover: 3.52,
    volumeRatio: 1.85,
    pe: 28.5,
    pb: 4.2,
    high52w: 1850.0,
    low52w: 1450.0
  })

  stockStore.setKlineData(klineData.value)
  stockStore.setIndicatorData(mockIndicatorData())
  stockStore.setCapitalData(mockCapitalData())
  stockStore.setAIAnalysis(mockAIAnalysis())
}

const toggleWatch = () => {
  if (!stockStore.currentStock) return

  if (isWatched.value) {
    stockStore.removeFromWatchList(stockStore.currentStock.code)
  } else {
    stockStore.addToWatchList(stockStore.currentStock.code)
  }
}

const formatAmount = (amount: number): string => {
  const absAmount = Math.abs(amount)
  if (absAmount >= 100000000) {
    return (amount >= 0 ? '+' : '-') + (absAmount / 100000000).toFixed(2) + '亿'
  } else if (absAmount >= 10000) {
    return (amount >= 0 ? '+' : '-') + (absAmount / 10000).toFixed(2) + '万'
  }
  return amount.toFixed(2)
}

onMounted(() => {
  const code = route.params.code as string
  if (code) {
    loadStockData(code)
  }
})

watch(() => route.params.code, (newCode) => {
  if (newCode) {
    loadStockData(newCode as string)
  }
})
</script>

<style scoped>
.stock-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}

.search-header {
  display: flex;
  gap: 16px;
}

.stock-search {
  width: 320px;
}

:deep(.stock-search .el-input__wrapper) {
  background-color: var(--bg-card);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.search-item {
  display: flex;
  flex-direction: column;
}

.stock-name {
  font-weight: 600;
}

.stock-code {
  font-size: 11px;
  color: var(--text-secondary);
}

.stock-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.stock-info-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
}

.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.stock-title h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.stock-code {
  font-size: 12px;
  color: var(--text-secondary);
  margin-left: 8px;
}

.stock-price {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 16px;
}

.stock-price .price {
  font-size: 32px;
  font-weight: 700;
}

.stock-price .change {
  font-size: 16px;
  font-weight: 600;
}

.stock-price .change.up { color: var(--color-up); }
.stock-price .change.down { color: var(--color-down); }

.stock-indicators {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 12px;
}

.indicator-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.indicator-item .label {
  font-size: 11px;
  color: var(--text-secondary);
}

.indicator-item .value {
  font-size: 14px;
  font-weight: 600;
}

.chart-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
  height: 450px;
}

.indicator-section,
.capital-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
}

.indicator-tabs-content :deep(.el-tabs__header) {
  margin-bottom: 12px;
}

.indicator-tabs-content :deep(.el-tabs__nav-wrap::after) {
  background-color: rgba(255, 255, 255, 0.05);
}

.indicator-content {
  display: flex;
  gap: 24px;
}

.indicator-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ind-label {
  font-size: 11px;
  color: var(--text-secondary);
}

.ind-value {
  font-size: 16px;
  font-weight: 600;
}

.ind-value.up { color: var(--color-up); }
.ind-value.down { color: var(--color-down); }

.indicator-signal {
  margin-top: auto;
}

.capital-detail {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.capital-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cap-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.cap-value {
  font-size: 18px;
  font-weight: 700;
}

.cap-value.up { color: var(--color-up); }
.cap-value.down { color: var(--color-down); }

.capital-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.capital-bar {
  display: grid;
  grid-template-columns: 60px 1fr 80px;
  align-items: center;
  gap: 12px;
}

.bar-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.bar-container {
  height: 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.bar-fill.up { background: var(--color-up); }
.bar-fill.down { background: var(--color-down); }

.bar-value {
  font-size: 12px;
  text-align: right;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}
</style>
