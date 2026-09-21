import { defineStore } from 'pinia'
import { ref } from 'vue'
import { screenerApi, type ScreenerFilter, type StockItem } from '@/api/screener'

// 保存的筛选预设
export interface ScreenerPreset {
  id: string
  name: string
  filter: ScreenerFilter
  createdAt: string
}

const PRESET_KEY = 'tradingos_screener_presets'

export const useScreenerStore = defineStore('screener', () => {
  // 筛选结果
  const stocks = ref<StockItem[]>([])
  const total = ref(0)
  const loading = ref(false)

  // 筛选条件
  const filter = ref<ScreenerFilter>({
    discovery_type: undefined,
    period: 'short',
    min_change_pct: undefined,
    max_change_pct: undefined,
    min_price: undefined,
    max_price: undefined,
    min_volume: undefined,
    max_volume: undefined,
    min_turnover_rate: undefined,
    max_turnover_rate: undefined,
    min_amount: undefined,
    max_amount: undefined,
    min_ma5: undefined,
    max_ma5: undefined,
    min_rsi6: undefined,
    max_rsi6: undefined,
    min_macd: undefined,
    max_macd: undefined,
    market: undefined,
    industry: undefined,
    sort_by: 'score',
    sort_order: 'desc',
    limit: 50,
    offset: 0,
  })

  // 排序选项
  const sortOptions = [
    { value: 'score', label: '综合评分' },
    { value: 'change_pct', label: '涨跌幅' },
    { value: 'volume', label: '成交量' },
    { value: 'turnover_rate', label: '换手率' },
    { value: 'price', label: '价格' },
  ]

  // 周期选项
  const periodOptions = [
    { value: 'short', label: '短线' },
    { value: 'medium', label: '中线' },
    { value: 'long', label: '长线' },
  ]

  // 市场选项
  const marketOptions = [
    { value: 'SH', label: '上海' },
    { value: 'SZ', label: '深圳' },
  ]

  // 保存的预设
  const presets = ref<ScreenerPreset[]>([])
  const currentPresetId = ref<string | null>(null)

  // 行业列表
  const industries = ref<string[]>([])

  // 初始化
  async function init() {
    await Promise.all([
      fetchIndustries(),
      loadPresets(),
    ])
  }

  // 获取行业列表
  async function fetchIndustries() {
    try {
      industries.value = await screenerApi.getIndustries()
    } catch (e) {
      console.error('获取行业列表失败:', e)
    }
  }

  // 查询股票
  async function queryStocks() {
    loading.value = true
    try {
      const response = await screenerApi.queryStocks(filter.value)
      stocks.value = response.items
      total.value = response.total
      return response
    } finally {
      loading.value = false
    }
  }

  // 重置筛选条件
  function resetFilter() {
    filter.value = {
      discovery_type: undefined,
      period: 'short',
      min_change_pct: undefined,
      max_change_pct: undefined,
      min_price: undefined,
      max_price: undefined,
      min_volume: undefined,
      max_volume: undefined,
      min_turnover_rate: undefined,
      max_turnover_rate: undefined,
      min_amount: undefined,
      max_amount: undefined,
      min_ma5: undefined,
      max_ma5: undefined,
      min_rsi6: undefined,
      max_rsi6: undefined,
      min_macd: undefined,
      max_macd: undefined,
      market: undefined,
      industry: undefined,
      sort_by: 'score',
      sort_order: 'desc',
      limit: 50,
      offset: 0,
    }
    currentPresetId.value = null
  }

  // 保存当前预设
  function savePreset(name: string) {
    const preset: ScreenerPreset = {
      id: Date.now().toString(),
      name,
      filter: { ...filter.value },
      createdAt: new Date().toISOString(),
    }
    presets.value.push(preset)
    currentPresetId.value = preset.id
    persistPresets()
  }

  // 加载预设
  function loadPreset(presetId: string) {
    const preset = presets.value.find(p => p.id === presetId)
    if (preset) {
      filter.value = { ...preset.filter }
      currentPresetId.value = presetId
    }
  }

  // 删除预设
  function deletePreset(presetId: string) {
    const index = presets.value.findIndex(p => p.id === presetId)
    if (index !== -1) {
      presets.value.splice(index, 1)
      if (currentPresetId.value === presetId) {
        currentPresetId.value = null
      }
      persistPresets()
    }
  }

  // 持久化预设到 localStorage
  function persistPresets() {
    localStorage.setItem(PRESET_KEY, JSON.stringify(presets.value))
  }

  // 从 localStorage 加载预设
  function loadPresets() {
    const saved = localStorage.getItem(PRESET_KEY)
    if (saved) {
      try {
        presets.value = JSON.parse(saved)
      } catch (e) {
        console.error('加载预设失败:', e)
      }
    }
  }

  // 更新筛选条件单个字段
  function updateFilter(key: keyof ScreenerFilter, value: any) {
    (filter.value as any)[key] = value
  }

  return {
    // 状态
    stocks,
    total,
    loading,
    filter,
    sortOptions,
    periodOptions,
    marketOptions,
    presets,
    currentPresetId,
    industries,

    // 方法
    init,
    fetchIndustries,
    queryStocks,
    resetFilter,
    savePreset,
    loadPreset,
    deletePreset,
    updateFilter,
  }
})