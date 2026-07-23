import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface IndexData {
  code: string
  name: string
  price: number
  change: number
  changePercent: number
  volume: number
  amount: number
}

export interface StockHot {
  code: string
  name: string
  change: number
  turnover: number
  volumeRatio: number
  aiScore: number
}

export interface MarketCapital {
  mainInflow: number
  northMoney: number
  industryMoney: number
}

export const useMarketStore = defineStore('market', () => {
  const indices = ref<IndexData[]>([
    { code: '000001', name: '上证指数', price: 2965.23, change: 45.32, changePercent: 1.55, volume: 325600000, amount: 398000000000 },
    { code: '399001', name: '深证成指', price: 10748.56, change: 156.78, changePercent: 1.48, volume: 456700000, amount: 512000000000 },
    { code: '399006', name: '创业板', price: 2234.12, change: 35.67, changePercent: 1.62, volume: 189500000, amount: 267000000000 },
    { code: '000688', name: '科创50', price: 756.89, change: 12.34, changePercent: 1.66, volume: 98700000, amount: 123000000000 }
  ])

  const upCount = ref(2856)
  const downCount = ref(1892)
  const limitUpCount = ref(85)
  const limitDownCount = ref(12)

  const hotStocks = ref<StockHot[]>([
    { code: '600519', name: '贵州茅台', change: 2.35, turnover: 3.5, volumeRatio: 1.8, aiScore: 88 },
    { code: '000858', name: '五粮液', change: 3.21, turnover: 4.2, volumeRatio: 2.1, aiScore: 85 },
    { code: '002594', name: '比亚迪', change: 4.56, turnover: 5.8, volumeRatio: 2.5, aiScore: 90 },
    { code: '600036', name: '招商银行', change: 1.89, turnover: 2.1, volumeRatio: 1.3, aiScore: 78 },
    { code: '601318', name: '中国平安', change: 2.12, turnover: 2.8, volumeRatio: 1.6, aiScore: 82 },
    { code: '000001', name: '平安银行', change: 1.45, turnover: 1.9, volumeRatio: 1.2, aiScore: 75 },
    { code: '600900', name: '长江电力', change: 0.89, turnover: 1.2, volumeRatio: 0.9, aiScore: 72 },
    { code: '300750', name: '宁德时代', change: 3.78, turnover: 4.5, volumeRatio: 2.2, aiScore: 87 },
    { code: '601012', name: '隆基绿能', change: 2.34, turnover: 3.2, volumeRatio: 1.7, aiScore: 80 },
    { code: '002415', name: '海康威视', change: 1.98, turnover: 2.6, volumeRatio: 1.4, aiScore: 76 }
  ])

  const capital = ref<MarketCapital>({
    mainInflow: 125000000000,
    northMoney: 28500000000,
    industryMoney: 45600000000
  })

  const aiAnalysis = ref({
    trend: '上涨趋势',
    score: 78,
    risk: '中等',
    sentiment: '资金活跃'
  })

  return {
    indices,
    upCount,
    downCount,
    limitUpCount,
    limitDownCount,
    hotStocks,
    capital,
    aiAnalysis
  }
})
