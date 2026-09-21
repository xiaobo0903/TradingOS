import api from './index'

export interface ScreenerFilter {
  // 发现类型
  discovery_type?: string
  period?: string

  // 行情条件
  min_change_pct?: number
  max_change_pct?: number
  min_price?: number
  max_price?: number
  min_volume?: number
  max_volume?: number
  min_turnover_rate?: number
  max_turnover_rate?: number
  min_amount?: number
  max_amount?: number

  // 技术指标条件
  min_ma5?: number
  max_ma5?: number
  min_rsi6?: number
  max_rsi6?: number
  min_macd?: number
  max_macd?: number

  // 市场条件
  market?: string
  industry?: string

  // 排序
  sort_by?: string
  sort_order?: string

  // 分页
  limit?: number
  offset?: number
}

export interface StockItem {
  id: number
  stock_id: number
  code: string
  name: string
  industry?: string
  market?: string

  // 行情数据
  current_price: number
  change_pct: number
  volume: number
  amount: number
  turnover_rate: number
  open: number
  high: number
  low: number

  // 发现相关
  discovery_type?: string
  score?: number
  reason?: string
  behaviors?: Record<string, boolean>
  trend?: Record<string, any>
}

export interface ScreenerResponse {
  total: number
  items: StockItem[]
}

export interface FilterOption {
  value: string
  label: string
  desc?: string
}

export interface FilterOptions {
  discovery_types: FilterOption[]
  periods: FilterOption[]
  sort_options: FilterOption[]
}

export const screenerApi = {
  // 获取筛选选项
  getFilterOptions(): Promise<FilterOptions> {
    return api.get('/screener/filters/options')
  },

  // 查询股票
  queryStocks(filter: ScreenerFilter): Promise<ScreenerResponse> {
    return api.post('/screener/query', filter)
  },

  // 获取行业列表
  getIndustries(): Promise<string[]> {
    return api.get('/screener/industries')
  },
}