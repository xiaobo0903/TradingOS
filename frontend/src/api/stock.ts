import api from './index'

export interface Stock {
  id: number
  code: string
  name: string
  market?: string
  industry?: string
  status: string
}

export interface StockDetail extends Stock {
  current_price: number
  change_pct: number
  volume: number
  amount: number
  turnover_rate: number
}

export interface DailyData {
  trade_date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number
  turnover_rate: number
  change_pct: number
  amplitude: number
}

export interface Indicator {
  trade_date: string
  ma: {
    ma5: number
    ma10: number
    ma20: number
    ma30: number
    ma60: number
    ma120?: number
    ma250?: number
  }
  ema: {
    ema12: number
    ema26: number
  }
  macd: {
    dif: number
    dea: number
    macd: number
  }
  rsi: {
    rsi6: number
    rsi12: number
    rsi24: number
  }
  boll: {
    mb: number
    ub: number
    lb: number
    width?: number
  }
  kdj: {
    k: number
    d: number
    j: number
  }
}

export const stockApi = {
  // 获取股票列表
  list(params: { market?: string; industry?: string; page?: number; page_size?: number }): Promise<Stock[]> {
    return api.get('/stocks/', { params })
  },

  // 获取股票详情
  getStock(code: string): Promise<StockDetail> {
    return api.get(`/stocks/${code}`)
  },

  // 获取日线数据
  getDaily(code: string, params?: { start_date?: string; end_date?: string; adjust?: string }): Promise<DailyData[]> {
    return api.get(`/stocks/${code}/daily`, { params })
  },

  // 获取分钟数据
  getMinute(code: string, params?: { period?: string; limit?: number }): Promise<any[]> {
    return api.get(`/stocks/${code}/minute`, { params })
  },

  // 获取实时行情
  getRealtime(code: string): Promise<any> {
    return api.get(`/stocks/${code}/realtime`)
  },

  // 获取技术指标
  getIndicators(code: string, params?: { trade_date?: string }): Promise<Indicator> {
    return api.get(`/stocks/${code}/indicators`, { params })
  },
}
