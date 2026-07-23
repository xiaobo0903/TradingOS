<template>
  <div class="kline-chart">
    <div class="chart-header">
      <div class="period-selector">
        <el-radio-group v-model="currentPeriod" size="small">
          <el-radio-button label="1m">分时</el-radio-button>
          <el-radio-button label="5m">5分钟</el-radio-button>
          <el-radio-button label="15m">15分钟</el-radio-button>
          <el-radio-button label="30m">30分钟</el-radio-button>
          <el-radio-button label="1d">日K</el-radio-button>
          <el-radio-button label="1w">周K</el-radio-button>
          <el-radio-button label="1M">月K</el-radio-button>
        </el-radio-group>
      </div>
    </div>
    <div class="chart-container" ref="chartRef"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

interface KLineData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  ma5?: number
  ma10?: number
  ma20?: number
}

interface IndicatorData {
  dif: number
  dea: number
  macd: number
  rsi6: number
  rsi12: number
  rsi24: number
  bollUpper?: number
  bollMid?: number
  bollLower?: number
}

const props = defineProps<{
  klineData: KLineData[]
  indicatorData?: IndicatorData | null
  symbol?: string
}>()

const chartRef = ref<HTMLElement>()
const currentPeriod = ref('1d')
let chartInstance: echarts.ECharts | null = null
let resizeObserver: ResizeObserver | null = null

const initChart = () => {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)

  updateChart()
}

const updateChart = () => {
  if (!chartInstance || !props.klineData.length) return

  const klineData = props.klineData

  // K线数据
  const klineSeries = klineData.map(item => [item.open, item.close, item.low, item.high])

  // 成交数据
  const volumeData = klineData.map(item => ({
    value: item.volume,
    itemStyle: {
      color: item.close >= item.open ? '#F5222D' : '#52C41A'
    }
  }))

  // MA均线数据
  const ma5Data = klineData.map(item => item.ma5 ?? null)
  const ma10Data = klineData.map(item => item.ma10 ?? null)
  const ma20Data = klineData.map(item => item.ma20 ?? null)

  // 日期标签
  const dateLabels = klineData.map(item => item.date)

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: '#151F32',
      borderColor: '#2A3A55',
      textStyle: { color: '#FFFFFF' }
    },
    legend: {
      show: true,
      bottom: 60,
      textStyle: { color: '#8892A6', fontSize: 11 },
      data: ['MA5', 'MA10', 'MA20']
    },
    grid: [
      { left: '60px', right: '20px', top: '20px', height: '55%' },
      { left: '60px', right: '20px', top: '75%', height: '10%' },
      { left: '60px', right: '20px', top: '87%', height: '10%' }
    ],
    xAxis: [
      {
        type: 'category',
        data: dateLabels,
        gridIndex: 0,
        axisLine: { lineStyle: { color: '#2A3A55' } },
        axisLabel: { color: '#8892A6', fontSize: 10 },
        axisTick: { show: false }
      },
      {
        type: 'category',
        data: dateLabels,
        gridIndex: 1,
        axisLine: { lineStyle: { color: '#2A3A55' } },
        axisLabel: { show: false },
        axisTick: { show: false }
      },
      {
        type: 'category',
        data: dateLabels,
        gridIndex: 2,
        axisLine: { lineStyle: { color: '#2A3A55' } },
        axisLabel: { show: false },
        axisTick: { show: false }
      }
    ],
    yAxis: [
      {
        scale: true,
        gridIndex: 0,
        splitLine: { lineStyle: { color: '#1A2540' } },
        axisLine: { lineStyle: { color: '#2A3A55' } },
        axisLabel: { color: '#8892A6', fontSize: 10 }
      },
      {
        scale: true,
        gridIndex: 1,
        splitLine: { show: false },
        axisLine: { lineStyle: { color: '#2A3A55' } },
        axisLabel: { color: '#8892A6', fontSize: 10 }
      },
      {
        scale: true,
        gridIndex: 2,
        splitLine: { show: false },
        axisLine: { lineStyle: { color: '#2A3A55' } },
        axisLabel: { color: '#8892A6', fontSize: 10 }
      }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1, 2], start: 70, end: 100 }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: klineSeries,
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
          color: '#F5222D',
          color0: '#52C41A',
          borderColor: '#F5222D',
          borderColor0: '#52C41A'
        }
      },
      {
        name: 'MA5',
        type: 'line',
        data: ma5Data,
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: true,
        showSymbol: false,
        lineStyle: { color: '#722ED1', width: 1 }
      },
      {
        name: 'MA10',
        type: 'line',
        data: ma10Data,
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: true,
        showSymbol: false,
        lineStyle: { color: '#FAAD14', width: 1 }
      },
      {
        name: 'MA20',
        type: 'line',
        data: ma20Data,
        xAxisIndex: 0,
        yAxisIndex: 0,
        smooth: true,
        showSymbol: false,
        lineStyle: { color: '#1a73e8', width: 1 }
      },
      {
        name: '成交量',
        type: 'bar',
        data: volumeData,
        xAxisIndex: 1,
        yAxisIndex: 1
      },
      {
        name: 'MACD',
        type: 'bar',
        data: props.indicatorData?.macd
          ? klineData.map(() => {
              const macdValue = props.indicatorData!.macd
              return {
                value: macdValue,
                itemStyle: {
                  color: macdValue >= 0 ? '#F5222D' : '#52C41A'
                }
              }
            })
          : [],
        xAxisIndex: 2,
        yAxisIndex: 2
      }
    ]
  }

  chartInstance.setOption(option)
}

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

onMounted(() => {
  nextTick(() => {
    initChart()

    if (chartRef.value) {
      resizeObserver = new ResizeObserver(handleResize)
      resizeObserver.observe(chartRef.value)
    }
  })
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  if (chartInstance) {
    chartInstance.dispose()
  }
})

watch(
  () => [props.klineData, props.indicatorData],
  () => {
    updateChart()
  },
  { deep: true }
)
</script>

<style scoped>
.kline-chart {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.period-selector :deep(.el-radio-button__inner) {
  background-color: var(--bg-card);
  border-color: var(--bg-card);
  color: var(--text-secondary);
}

.period-selector :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background-color: var(--color-info);
  border-color: var(--color-info);
  color: white;
}

.chart-container {
  flex: 1;
  min-height: 400px;
}
</style>
