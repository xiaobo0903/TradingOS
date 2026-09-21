import api from './index'

export interface CollectionResponse {
  success: boolean
  message: string
  records_count: number
}

export interface StockRealtimeItem {
  stock_code: string
  stock_name: string
  trade_date: string
  pre_close: number
  open: number
  high: number
  low: number
  close: number
  change: number
  pct_chg: number
  amplitude: number
  volume: number
  amount: number
  turnover_rate: number
  volume_ratio: number
  total_share: number
  float_share: number
  total_market_cap: number
  float_market_cap: number
  pe: number | null
  pb: number | null
  main_inflow: number
  main_volume: number
  weibi: number
  buy_price: number
  sell_price: number
}

export interface RealtimeListResponse {
  trade_date: string
  total: number
  items: StockRealtimeItem[]
}

export const dataCenterApi = {
  // 采集股票列表
  collectStocks(force?: boolean): Promise<CollectionResponse> {
    return api.post('/data-center/collect/stocks', null, {
      params: { force },
    })
  },

  // 采集日线数据
  collectDaily(stockCode?: string, startDate?: string, endDate?: string): Promise<CollectionResponse> {
    return api.post('/data-center/collect/daily', null, {
      params: { stock_code: stockCode, start_date: startDate, end_date: endDate },
    })
  },

  // 采集分钟数据
  collectMinute(stockCode: string, period?: string): Promise<any> {
    return api.post('/data-center/collect/minute', null, {
      params: { stock_code: stockCode, period },
    })
  },

  // 采集资金数据
  collectCapital(stockCode?: string): Promise<CollectionResponse> {
    return api.post('/data-center/collect/capital', null, {
      params: { stock_code: stockCode },
    })
  },

  // 采集板块数据
  collectSectors(): Promise<CollectionResponse> {
    return api.post('/data-center/collect/sectors')
  },

  // 采集资金流数据（腾讯财经）
  collectCapitalFlow(): Promise<CollectionResponse> {
    return api.post('/data-center/collect/capital-flow')
  },

  // 一键采集所有数据
  collectAll(): Promise<CollectionResponse> {
    return api.post('/data-center/collect/all')
  },

  // 同步历史数据
  syncHistory(days?: number): Promise<CollectionResponse> {
    return api.post('/data-center/sync/history', null, {
      params: { days },
    })
  },

  // 获取数据状态
  getStatus(): Promise<any> {
    return api.get('/data-center/status')
  },

  // 获取股票实时行情列表（股票明细）
  getRealtimeList(params: {
    trade_date?: string
    search?: string
    sort_by?: string
    order?: string
    limit?: number
    offset?: number
  }): Promise<RealtimeListResponse> {
    return api.get('/data-center/realtime/list', { params })
  },

  // CSV导入股票数据
  importStockData(tradeDate: string, formData: FormData): Promise<{
    success: boolean
    message: string
    total_rows: number
    success_count: number
    error_count: number
    errors: { row: number; message: string; data: string }[]
  }> {
    return api.post(`/data-center/import/csv?trade_date=${tradeDate}`, formData)
  },
}
