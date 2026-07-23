import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface StockInfo {
  code: string
  name: string
  price: number
  change: number
  changePercent: number
  volume: number
  amount: number
  turnover: number
  volumeRatio: number
  pe: number
  pb: number
  high52w: number
  low52w: number
}

export interface KLineData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface IndicatorData {
  ma5: number
  ma10: number
  ma20: number
  ma60: number
  dif: number
  dea: number
  macd: number
  rsi6: number
  rsi12: number
  rsi24: number
  bollUpper: number
  bollMid: number
  bollLower: number
  kdjK: number
  kdjD: number
  kdjJ: number
}

export interface CapitalData {
  mainInflow: number
  mainOutflow: number
  superLargeIn: number
  superLargeOut: number
  largeIn: number
  largeOut: number
  mediumIn: number
  mediumOut: number
  smallIn: number
  smallOut: number
}

export interface AIAnalysis {
  trend: string
  confidence: number
  signals: string[]
  risks: string[]
  suggestion: string
}

export const useStockStore = defineStore('stock', () => {
  const currentStock = ref<StockInfo | null>(null)
  const klineData = ref<KLineData[]>([])
  const indicatorData = ref<IndicatorData | null>(null)
  const capitalData = ref<CapitalData | null>(null)
  const aiAnalysis = ref<AIAnalysis | null>(null)
  const watchList = ref<string[]>(['600519', '000858', '002594', '600036', '601318'])

  function setCurrentStock(stock: StockInfo) {
    currentStock.value = stock
  }

  function setKlineData(data: KLineData[]) {
    klineData.value = data
  }

  function setIndicatorData(data: IndicatorData) {
    indicatorData.value = data
  }

  function setCapitalData(data: CapitalData) {
    capitalData.value = data
  }

  function setAIAnalysis(data: AIAnalysis) {
    aiAnalysis.value = data
  }

  function addToWatchList(code: string) {
    if (!watchList.value.includes(code)) {
      watchList.value.push(code)
    }
  }

  function removeFromWatchList(code: string) {
    const index = watchList.value.indexOf(code)
    if (index > -1) {
      watchList.value.splice(index, 1)
    }
  }

  return {
    currentStock,
    klineData,
    indicatorData,
    capitalData,
    aiAnalysis,
    watchList,
    setCurrentStock,
    setKlineData,
    setIndicatorData,
    setCapitalData,
    setAIAnalysis,
    addToWatchList,
    removeFromWatchList
  }
})
