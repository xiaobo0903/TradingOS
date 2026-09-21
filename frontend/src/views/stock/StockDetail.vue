<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStockStore } from '@/store/stock'
import { stockApi, type DailyData, type Indicator } from '@/api/stock'
import { indicatorApi } from '@/api/indicator'
import * as echarts from 'echarts'

const route = useRoute()
const router = useRouter()
const stockStore = useStockStore()

const activePeriod = ref('daily')
const klineChartRef = ref<HTMLElement | null>(null)
const volumeChartRef = ref<HTMLElement | null>(null)
const indicatorChartRef = ref<HTMLElement | null>(null)

let klineChart: echarts.ECharts | null = null
let volumeChart: echarts.ECharts | null = null
let indicatorChart: echarts.ECharts | null = null

const periods = [
  { label: '1分', value: '1' },
  { label: '5分', value: '5' },
  { label: '15分', value: '15' },
  { label: '30分', value: '30' },
  { label: '60分', value: '60' },
  { label: '日', value: 'daily' },
  { label: '周', value: 'weekly' },
  { label: '月', value: 'monthly' },
]

const code = computed(() => route.params.code as string)

onMounted(async () => {
  await loadData()
  initCharts()
})

watch(code, async () => {
  await loadData()
  updateCharts()
})

watch(activePeriod, async () => {
  if (activePeriod.value === 'daily') {
    await stockStore.fetchDaily(code.value)
  } else {
    await stockStore.fetchMinute(code.value, activePeriod.value)
  }
  updateCharts()
})

async function loadData() {
  await Promise.all([
    stockStore.fetchStock(code.value),
    stockStore.fetchDaily(code.value),
    stockStore.fetchIndicators(code.value),
  ])
}

function initCharts() {
  if (klineChartRef.value) {
    klineChart = echarts.init(klineChartRef.value)
  }
  if (volumeChartRef.value) {
    volumeChart = echarts.init(volumeChartRef.value)
  }
  if (indicatorChartRef.value) {
    indicatorChart = echarts.init(indicatorChartRef.value)
  }
  updateCharts()
}

function updateCharts() {
  if (!klineChart || !stockStore.dailyData.length) return

  const data = stockStore.dailyData

  // K线数据
  const klineData = data.map(d => [d.open, d.close, d.low, d.high])
  const dates = data.map(d => d.trade_date)

  // 成交量数据
  const volumeData = data.map(d => ({
    value: d.volume,
    itemStyle: {
      color: d.change_pct >= 0 ? '#f56c6c' : '#67c23a'
    }
  }))

  // K线图
  klineChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    grid: [{ left: '10%', right: '8%', top: '10%', bottom: '30%' }],
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: true
    },
    yAxis: {
      type: 'value',
      scale: true
    },
    series: [{
      type: 'candlestick',
      data: klineData,
      itemStyle: {
        color: '#f56c6c',
        color0: '#67c23a',
        borderColor: '#f56c6c',
        borderColor0: '#67c23a'
      }
    }]
  })

  // 成交量图
  if (volumeChart) {
    volumeChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: [{ left: '10%', right: '8%', top: '10%', bottom: '0%' }],
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value' },
      series: [{ type: 'bar', data: volumeData }]
    })
  }
}

function formatNumber(num: number | undefined, decimals: number = 2): string {
  if (num === undefined || num === null) return '--'
  return num.toFixed(decimals)
}

function getChangeClass(pct: number | undefined): string {
  if (pct === undefined || pct === null) return ''
  return pct > 0 ? 'price-up' : pct < 0 ? 'price-down' : ''
}

function goBack() {
  router.back()
}
</script>

<template>
  <div class="stock-detail">
    <!-- 股票头部信息 -->
    <el-card class="stock-header" v-if="stockStore.currentStock">
      <div class="header-content">
        <div class="stock-info">
          <h1 class="stock-name">{{ stockStore.currentStock.name }}</h1>
          <span class="stock-code">{{ stockStore.currentStock.code }}</span>
        </div>
        <div class="stock-price">
          <span class="current-price" :class="getChangeClass(stockStore.currentStock.change_pct)">
            {{ formatNumber(stockStore.currentStock.current_price) }}
          </span>
          <span class="change-pct" :class="getChangeClass(stockStore.currentStock.change_pct)">
            {{ stockStore.currentStock.change_pct > 0 ? '+' : '' }}{{ formatNumber(stockStore.currentStock.change_pct) }}%
          </span>
        </div>
        <div class="stock-meta">
          <span>成交量: {{ stockStore.currentStock.volume }}</span>
          <span>成交额: {{ stockStore.currentStock.amount }}</span>
          <span>换手率: {{ formatNumber(stockStore.currentStock.turnover_rate) }}%</span>
        </div>
      </div>
      <el-button @click="goBack">返回</el-button>
    </el-card>

    <!-- 时间周期选择 -->
    <el-card class="period-selector">
      <el-radio-group v-model="activePeriod" size="default">
        <el-radio-button v-for="p in periods" :key="p.value" :value="p.value">
          {{ p.label }}
        </el-radio-button>
      </el-radio-group>
    </el-card>

    <!-- K线图 -->
    <el-card class="chart-card">
      <div ref="klineChartRef" class="kline-chart"></div>
      <div ref="volumeChartRef" class="volume-chart"></div>
    </el-card>

    <!-- 技术指标 -->
    <el-card class="indicator-card" v-if="stockStore.indicators">
      <template #header>
        <span>技术指标</span>
      </template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="MA5">{{ formatNumber(stockStore.indicators.ma?.ma5) }}</el-descriptions-item>
        <el-descriptions-item label="MA10">{{ formatNumber(stockStore.indicators.ma?.ma10) }}</el-descriptions-item>
        <el-descriptions-item label="MA20">{{ formatNumber(stockStore.indicators.ma?.ma20) }}</el-descriptions-item>
        <el-descriptions-item label="MA30">{{ formatNumber(stockStore.indicators.ma?.ma30) }}</el-descriptions-item>
        <el-descriptions-item label="MA60">{{ formatNumber(stockStore.indicators.ma?.ma60) }}</el-descriptions-item>
        <el-descriptions-item label="EMA12">{{ formatNumber(stockStore.indicators.ema?.ema12) }}</el-descriptions-item>
        <el-descriptions-item label="DIF">{{ formatNumber(stockStore.indicators.macd?.dif) }}</el-descriptions-item>
        <el-descriptions-item label="DEA">{{ formatNumber(stockStore.indicators.macd?.dea) }}</el-descriptions-item>
        <el-descriptions-item label="MACD">{{ formatNumber(stockStore.indicators.macd?.macd) }}</el-descriptions-item>
        <el-descriptions-item label="RSI6">{{ formatNumber(stockStore.indicators.rsi?.rsi6) }}</el-descriptions-item>
        <el-descriptions-item label="RSI12">{{ formatNumber(stockStore.indicators.rsi?.rsi12) }}</el-descriptions-item>
        <el-descriptions-item label="RSI24">{{ formatNumber(stockStore.indicators.rsi?.rsi24) }}</el-descriptions-item>
        <el-descriptions-item label="BOLL上轨">{{ formatNumber(stockStore.indicators.boll?.ub) }}</el-descriptions-item>
        <el-descriptions-item label="BOLL中轨">{{ formatNumber(stockStore.indicators.boll?.mb) }}</el-descriptions-item>
        <el-descriptions-item label="BOLL下轨">{{ formatNumber(stockStore.indicators.boll?.lb) }}</el-descriptions-item>
        <el-descriptions-item label="KDJ_K">{{ formatNumber(stockStore.indicators.kdj?.k) }}</el-descriptions-item>
        <el-descriptions-item label="KDJ_D">{{ formatNumber(stockStore.indicators.kdj?.d) }}</el-descriptions-item>
        <el-descriptions-item label="KDJ_J">{{ formatNumber(stockStore.indicators.kdj?.j) }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<style scoped>
.stock-detail {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 30px;
}

.stock-info {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.stock-name {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.stock-code {
  color: #909399;
  font-size: 14px;
}

.stock-price {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.current-price {
  font-size: 28px;
  font-weight: 600;
}

.change-pct {
  font-size: 18px;
}

.stock-meta {
  display: flex;
  gap: 20px;
  color: #606266;
  font-size: 14px;
}

.price-up {
  color: #f56c6c;
}

.price-down {
  color: #67c23a;
}

.period-selector {
  padding: 10px;
}

.chart-card {
  padding: 10px;
}

.kline-chart {
  height: 400px;
}

.volume-chart {
  height: 150px;
}

.indicator-card {
  margin-top: 0;
}
</style>
