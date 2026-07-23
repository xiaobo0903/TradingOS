<template>
  <div class="indicator-page">
    <div class="page-header">
      <h1 class="page-title">技术指标分析</h1>
      <div class="stock-selector">
        <el-autocomplete
          v-model="stockQuery"
          :fetch-suggestions="searchStock"
          placeholder="选择股票..."
          :trigger-on-focus="false"
          clearable
          @select="handleSelect"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
          <template #default="{ item }">
            <span>{{ item.value }} ({{ item.code }})</span>
          </template>
        </el-autocomplete>
      </div>
    </div>

    <div class="indicator-content">
      <!-- Indicator Tabs -->
      <div class="indicator-list">
        <div
          v-for="ind in indicators"
          :key="ind.key"
          class="indicator-card"
          :class="{ active: activeIndicator === ind.key }"
          @click="activeIndicator = ind.key"
        >
          <div class="ind-icon">{{ ind.icon }}</div>
          <div class="ind-info">
            <div class="ind-name">{{ ind.name }}</div>
            <div class="ind-desc">{{ ind.desc }}</div>
          </div>
        </div>
      </div>

      <!-- Indicator Detail -->
      <div class="indicator-detail">
        <div class="detail-header">
          <h2>{{ currentIndicator?.name }}</h2>
          <div class="current-value" v-if="indicatorValues">
            <span class="value-label">{{ currentIndicator?.name }}:</span>
            <span class="value-num">{{ getCurrentValue() }}</span>
          </div>
        </div>

        <div class="detail-content">
          <!-- Chart -->
          <div class="detail-chart">
            <div ref="chartRef" style="width: 100%; height: 300px;"></div>
          </div>

          <!-- Explanation -->
          <div class="detail-explanation">
            <div class="exp-section">
              <div class="exp-title">指标说明</div>
              <p class="exp-text">{{ currentIndicator?.explanation }}</p>
            </div>

            <div class="exp-section" v-if="indicatorValues">
              <div class="exp-title">当前状态</div>
              <div class="status-tags">
                <el-tag v-if="isOverbought" type="danger">超买</el-tag>
                <el-tag v-if="isOversold" type="success">超卖</el-tag>
                <el-tag v-if="isGoldenCross" type="warning">金叉</el-tag>
                <el-tag v-if="isDeadCross" type="warning">死叉</el-tag>
              </div>
            </div>

            <div class="exp-section">
              <div class="exp-title">AI解读</div>
              <div class="ai-interpretation">
                <p>{{ aiInterpretation }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { Search } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const stockQuery = ref('')
const activeIndicator = ref('macd')
const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const indicators = [
  { key: 'macd', name: 'MACD', icon: '📊', desc: '指数平滑异同移动平均线', explanation: 'MACD通过计算短期EMA与长期EMA的差值，判断股价趋势的动量变化。金叉通常被视为买入信号，死叉被视为卖出信号。' },
  { key: 'rsi', name: 'RSI', icon: '📈', desc: '相对强弱指数', explanation: 'RSI衡量股价变动的速度和幅度，取值范围0-100。RSI超过70通常表示超买，低于30表示超卖。' },
  { key: 'boll', name: 'BOLL', icon: '🔴', desc: '布林带', explanation: '布林带由中轨（MA20）和上下轨（中轨±2标准差）组成。价格突破上轨可能表示强势，跌破下轨可能表示弱势。' },
  { key: 'kdj', name: 'KDJ', icon: '🎯', desc: '随机指标', explanation: 'KDJ通过比较收盘价与一定周期内的最高最低价关系，判断股价的超买超卖状态。K值上穿D值为金叉，下穿为死叉。' },
  { key: 'ema', name: 'EMA', icon: '📉', desc: '指数移动平均线', explanation: 'EMA给予近期价格更高权重，比MA更能反映最新价格变化。常用于判断趋势方向和支撑压力位。' },
  { key: 'ma', name: 'MA', icon: '〰️', desc: '移动平均线', explanation: 'MA将一定周期内的收盘价相加求平均，连成曲线。用于判断趋势方向，多头排列（短期>长期）为买入信号。' }
]

const indicatorValues = ref({
  macd: { dif: 12.35, dea: 8.67, macd: 7.36 },
  rsi: { rsi6: 68.5, rsi12: 65.3, rsi24: 62.8 },
  boll: { upper: 1685.25, mid: 1650.0, lower: 1614.75 },
  kdj: { k: 72.5, d: 68.3, j: 81.2 },
 ema: { ema5: 1652.35, ema10: 1648.72, ema20: 1645.18 },
  ma: { ma5: 1652.35, ma10: 1648.72, ma20: 1645.18, ma60: 1638.45 }
})

const currentIndicator = computed(() => indicators.find(i => i.key === activeIndicator.value))

const isOverbought = computed(() => {
  if (activeIndicator.value === 'rsi') return indicatorValues.value.rsi.rsi6 > 70
  if (activeIndicator.value === 'kdj') return indicatorValues.value.kdj.k > 80
  return false
})

const isOversold = computed(() => {
  if (activeIndicator.value === 'rsi') return indicatorValues.value.rsi.rsi6 < 30
  if (activeIndicator.value === 'kdj') return indicatorValues.value.kdj.k < 20
  return false
})

const isGoldenCross = computed(() => {
  if (activeIndicator.value === 'macd') return indicatorValues.value.macd.dif > indicatorValues.value.macd.dea
  if (activeIndicator.value === 'kdj') return indicatorValues.value.kdj.k > indicatorValues.value.kdj.d
  return false
})

const isDeadCross = computed(() => {
  if (activeIndicator.value === 'macd') return indicatorValues.value.macd.dif < indicatorValues.value.macd.dea
  if (activeIndicator.value === 'kdj') return indicatorValues.value.kdj.k < indicatorValues.value.kdj.d
  return false
})

const aiInterpretation = computed(() => {
  const interpretations: Record<string, string> = {
    macd: 'MACD指标显示DIF上穿DEA形成金叉，位于零轴上方，表明多头力量较强。但MACD柱有所收缩，需关注成交量配合情况。',
    rsi: 'RSI指标处于强势区域但接近超买边界，建议谨慎追高。短期可能面临调整压力，等待回调后再关注。',
    boll: '股价突破布林带上轨，强势特征明显。但乖离率较大，注意回调风险。',
    kdj: 'KDJ指标金叉向上，J值较高显示短期强势。需关注高位钝化后的反转风险。',
    ema: 'EMA均线多头排列，短期趋势向上。价格回踩均线时可考虑关注。',
    ma: '均线系统呈多头排列，趋势向好。可依托均线作为止损参考。'
  }
  return interpretations[activeIndicator.value] || '暂无数据'
})

const getCurrentValue = () => {
  const values = indicatorValues.value[activeIndicator.value as keyof typeof indicatorValues.value]
  if (!values) return ''
  return Object.values(values).map(v => v.toFixed(2)).join(' / ')
}

const searchStock = (query: string, cb: (results: Array<{ value: string; code: string }>) => void) => {
  const mockStocks = [
    { value: '贵州茅台', code: '600519' },
    { value: '五粮液', code: '000858' },
    { value: '比亚迪', code: '002594' },
    { value: '招商银行', code: '600036' },
    { value: '中国平安', code: '601318' }
  ]
  cb(mockStocks.filter(s => s.value.includes(query) || s.code.includes(query)))
}

const handleSelect = (item: { value: string; code: string }) => {
  console.log('Selected:', item)
}

const initChart = () => {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

const updateChart = () => {
  if (!chartInstance) return

  let option: echarts.EChartsOption

  if (activeIndicator.value === 'macd') {
    option = {
      tooltip: { trigger: 'axis' },
      legend: { data: ['DIF', 'DEA', 'MACD'], bottom: 0, textStyle: { color: '#8892A6' } },
      grid: { left: 50, right: 20, top: 20, bottom: 60 },
      xAxis: { type: 'category', data: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'], axisLine: { lineStyle: { color: '#2A3A55' } }, axisLabel: { color: '#8892A6' } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: '#1A2540' } }, axisLine: { lineStyle: { color: '#2A3A55' } }, axisLabel: { color: '#8892A6' } },
      series: [
        { name: 'DIF', type: 'line', data: [10.2, 11.5, 12.8, 11.2, 13.5, 14.2, 13.8, 12.5, 11.8, 12.35], smooth: true, lineStyle: { color: '#722ED1', width: 2 } },
        { name: 'DEA', type: 'line', data: [8.5, 9.2, 9.8, 9.5, 10.2, 10.5, 10.2, 9.8, 9.2, 8.67], smooth: true, lineStyle: { color: '#FAAD14', width: 2 } },
        { name: 'MACD', type: 'bar', data: [1.7, 2.3, 3.0, 1.7, 3.3, 3.7, 3.6, 2.7, 2.6, 3.68], itemStyle: { color: (params: any) => params.value >= 0 ? '#F5222D' : '#52C41A' } }
      ]
    }
  } else if (activeIndicator.value === 'rsi') {
    option = {
      tooltip: { trigger: 'axis' },
      legend: { data: ['RSI6', 'RSI12', 'RSI24'], bottom: 0, textStyle: { color: '#8892A6' } },
      grid: { left: 50, right: 20, top: 20, bottom: 60 },
      xAxis: { type: 'category', data: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'], axisLine: { lineStyle: { color: '#2A3A55' } }, axisLabel: { color: '#8892A6' } },
      yAxis: { type: 'value', min: 0, max: 100, splitLine: { lineStyle: { color: '#1A2540' } }, axisLine: { lineStyle: { color: '#2A3A55' } }, axisLabel: { color: '#8892A6' } },
      series: [
        { name: 'RSI6', type: 'line', data: [65, 68, 70, 72, 69, 71, 73, 70, 68, 68.5], smooth: true, lineStyle: { width: 2 } },
        { name: 'RSI12', type: 'line', data: [62, 65, 67, 68, 66, 68, 69, 67, 65, 65.3], smooth: true, lineStyle: { width: 2 } },
        { name: 'RSI24', type: 'line', data: [60, 62, 64, 65, 64, 65, 66, 64, 63, 62.8], smooth: true, lineStyle: { width: 2 } }
      ]
    }
  } else {
    option = {
      tooltip: { trigger: 'axis' },
      legend: { data: ['MA5', 'MA10', 'MA20'], bottom: 0, textStyle: { color: '#8892A6' } },
      grid: { left: 50, right: 20, top: 20, bottom: 60 },
      xAxis: { type: 'category', data: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'], axisLine: { lineStyle: { color: '#2A3A55' } }, axisLabel: { color: '#8892A6' } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: '#1A2540' } }, axisLine: { lineStyle: { color: '#2A3A55' } }, axisLabel: { color: '#8892A6' } },
      series: [
        { name: 'MA5', type: 'line', data: [1640, 1645, 1650, 1648, 1652, 1655, 1658, 1660, 1655, 1652.35], smooth: true, lineStyle: { color: '#722ED1', width: 2 } },
        { name: 'MA10', type: 'line', data: [1635, 1640, 1642, 1645, 1648, 1650, 1652, 1654, 1652, 1648.72], smooth: true, lineStyle: { color: '#FAAD14', width: 2 } },
        { name: 'MA20', type: 'line', data: [1630, 1635, 1638, 1640, 1642, 1645, 1647, 1648, 1646, 1645.18], smooth: true, lineStyle: { color: '#1a73e8', width: 2 } }
      ]
    }
  }

  chartInstance.setOption(option)
}

watch(activeIndicator, () => {
  nextTick(() => {
    updateChart()
  })
})

onMounted(() => {
  nextTick(() => {
    initChart()
  })
})
</script>

<style scoped>
.indicator-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
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

.stock-selector {
  width: 200px;
}

.indicator-content {
  flex: 1;
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
  min-height: 0;
}

.indicator-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.indicator-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition-fast);
  border: 1px solid transparent;
}

.indicator-card:hover {
  background: var(--bg-card-hover);
}

.indicator-card.active {
  border-color: var(--color-info);
  background: rgba(26, 115, 232, 0.1);
}

.ind-icon {
  font-size: 24px;
}

.ind-name {
  font-weight: 600;
  font-size: 14px;
}

.ind-desc {
  font-size: 11px;
  color: var(--text-secondary);
}

.indicator-detail {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.detail-header h2 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.current-value {
  display: flex;
  align-items: center;
  gap: 8px;
}

.value-label {
  color: var(--text-secondary);
  font-size: 13px;
}

.value-num {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-info);
}

.detail-content {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 20px;
}

.detail-chart {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 12px;
}

.detail-explanation {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.exp-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.exp-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.exp-text {
  font-size: 13px;
  line-height: 1.6;
  margin: 0;
}

.status-tags {
  display: flex;
  gap: 8px;
}

.ai-interpretation {
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border-left: 3px solid var(--color-ai);
}

.ai-interpretation p {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
}
</style>
