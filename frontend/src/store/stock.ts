import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { stockApi, type Stock, type StockDetail, type DailyData, type Indicator } from '@/api/stock'

export const useStockStore = defineStore('stock', () => {
  const currentStock = ref<StockDetail | null>(null)
  const dailyData = ref<DailyData[]>([])
  const minuteData = ref<any[]>([])
  const indicators = ref<Indicator | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const latestPrice = computed(() => dailyData.value[dailyData.value.length - 1])

  async function fetchStock(code: string) {
    loading.value = true
    error.value = null
    try {
      currentStock.value = await stockApi.getStock(code)
    } catch (e) {
      error.value = '获取股票详情失败'
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  async function fetchDaily(code: string, startDate?: string, endDate?: string) {
    try {
      dailyData.value = await stockApi.getDaily(code, { start_date: startDate, end_date: endDate })
    } catch (e) {
      console.error('获取日线数据失败:', e)
    }
  }

  async function fetchMinute(code: string, period: string = '1') {
    try {
      minuteData.value = await stockApi.getMinute(code, { period, limit: 100 })
    } catch (e) {
      console.error('获取分钟数据失败:', e)
    }
  }

  async function fetchIndicators(code: string, tradeDate?: string) {
    try {
      indicators.value = await stockApi.getIndicators(code, { trade_date: tradeDate })
    } catch (e) {
      console.error('获取指标失败:', e)
    }
  }

  return {
    currentStock,
    dailyData,
    minuteData,
    indicators,
    loading,
    error,
    latestPrice,
    fetchStock,
    fetchDaily,
    fetchMinute,
    fetchIndicators,
  }
})
