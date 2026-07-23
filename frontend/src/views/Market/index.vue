<template>
  <div class="market-page">
    <!-- Index Cards -->
    <div class="index-cards">
      <div
        v-for="index in marketStore.indices"
        :key="index.code"
        class="index-card"
        :class="{ selected: selectedIndex === index.code }"
        @click="selectIndex(index.code)"
      >
        <div class="index-name">{{ index.name }}</div>
        <div class="index-price">{{ index.price.toFixed(2) }}</div>
        <div class="index-change" :class="index.change >= 0 ? 'up' : 'down'">
          {{ index.change >= 0 ? '+' : '' }}{{ index.changePercent.toFixed(2) }}%
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="market-content">
      <!-- Left: Chart -->
      <div class="chart-area">
        <div class="chart-header">
          <div class="chart-title">{{ selectedIndexName }}</div>
          <div class="period-selector">
            <el-radio-group v-model="period" size="small">
              <el-radio-button label="daily">日K</el-radio-button>
              <el-radio-button label="weekly">周K</el-radio-button>
              <el-radio-button label="monthly">月K</el-radio-button>
            </el-radio-group>
          </div>
        </div>
        <div class="chart-container">
          <KLineChart :kline-data="klineData" />
        </div>
      </div>

      <!-- Right: AI Analysis -->
      <div class="analysis-panel">
        <div class="panel-section">
          <div class="section-title">AI实时分析</div>
          <AIBox :analysis="marketAIAnalysis" />
        </div>

        <div class="panel-section">
          <div class="section-title">热点板块</div>
          <div class="hot-sectors">
            <div v-for="sector in hotSectors" :key="sector.name" class="sector-item">
              <span class="sector-name">{{ sector.name }}</span>
              <span class="sector-change" :class="sector.change >= 0 ? 'up' : 'down'">
                {{ sector.change >= 0 ? '+' : '' }}{{ sector.change.toFixed(2) }}%
              </span>
              <div class="sector-stocks">
                <el-tag v-for="stock in sector.topStocks" :key="stock" size="small">
                  {{ stock }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMarketStore } from '@/stores/market'
import KLineChart from '@/components/Charts/KLineChart.vue'
import AIBox from '@/components/Common/AIBox.vue'

const marketStore = useMarketStore()

const period = ref('daily')
const selectedIndex = ref('000001')

const selectedIndexName = computed(() => {
  const index = marketStore.indices.find(i => i.code === selectedIndex.value)
  return index?.name || '上证指数'
})

const hotSectors = ref([
  { name: '人工智能', change: 6.2, topStocks: ['寒武纪', '海康威视', '科大讯飞'] },
  { name: '新能源汽车', change: 4.5, topStocks: ['比亚迪', '宁德时代'] },
  { name: '半导体', change: 3.8, topStocks: ['中芯国际', '韦尔股份'] },
  { name: '白酒', change: 2.1, topStocks: ['贵州茅台', '五粮液'] },
  { name: '银行', change: 1.5, topStocks: ['招商银行', '宁波银行'] }
])

const marketAIAnalysis = computed(() => ({
  trend: '震荡偏强',
  confidence: 72,
  signals: ['成交量放大', '北向资金流入', '板块轮动'],
  risks: ['外围市场波动', '获利回吐压力'],
  suggestion: '控制仓位，关注主线板块'
}))

// Mock K线 data
const generateKlineData = () => {
  const data = []
  const basePrice = 2965
  const today = new Date()

  for (let i = 60; i >= 0; i--) {
    const date = new Date(today)
    date.setDate(date.getDate() - i)
    const open = basePrice + (Math.random() - 0.5) * 50
    const close = open + (Math.random() - 0.5) * 30
    const high = Math.max(open, close) + Math.random() * 20
    const low = Math.min(open, close) - Math.random() * 20

    data.push({
      date: `${date.getMonth() + 1}/${date.getDate()}`,
      open: parseFloat(open.toFixed(2)),
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      close: parseFloat(close.toFixed(2)),
      volume: Math.floor(Math.random() * 100000000) + 50000000,
      ma5: parseFloat((close * (1 + (Math.random() - 0.5) * 0.02)).toFixed(2)),
      ma10: parseFloat((close * (1 + (Math.random() - 0.5) * 0.03)).toFixed(2)),
      ma20: parseFloat((close * (1 + (Math.random() - 0.5) * 0.04)).toFixed(2))
    })
  }

  return data
}

const klineData = ref(generateKlineData())

const selectIndex = (code: string) => {
  selectedIndex.value = code
}
</script>

<style scoped>
.market-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}

.index-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.index-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
  cursor: pointer;
  transition: var(--transition-fast);
  border: 1px solid transparent;
}

.index-card:hover {
  background: var(--bg-card-hover);
}

.index-card.selected {
  border-color: var(--color-info);
  background: rgba(26, 115, 232, 0.1);
}

.index-name {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.index-price {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 4px;
}

.index-change {
  font-size: 14px;
  font-weight: 600;
}

.index-change.up { color: var(--color-up); }
.index-change.down { color: var(--color-down); }

.market-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 16px;
  min-height: 0;
}

.chart-area {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.chart-title {
  font-size: 18px;
  font-weight: 600;
}

.chart-container {
  flex: 1;
  min-height: 400px;
}

.analysis-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.hot-sectors {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sector-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sector-name {
  font-size: 13px;
  font-weight: 600;
}

.sector-change {
  font-size: 12px;
  font-weight: 600;
}

.sector-change.up { color: var(--color-up); }
.sector-change.down { color: var(--color-down); }

.sector-stocks {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.sector-stocks .el-tag {
  background: var(--bg-secondary);
  border: none;
  color: var(--text-secondary);
}
</style>
