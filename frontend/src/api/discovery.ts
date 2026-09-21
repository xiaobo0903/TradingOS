import api from './index'

export interface DiscoveryItem {
  id: number
  stock_id: number
  code: string
  name: string
  industry?: string
  score: number
  reason: string
  trade_date: string
  // 满足的条件列表
  conditions: string[]
  // T-1日行情
  close: number
  change_pct: number
  volume: number
  turnover_rate: number
  high: number
  low: number
  // 技术指标
  indicators: {
    ma5?: number
    ma10?: number
    ma20?: number
    dif?: number
    dea?: number
    macd?: number
    rsi6?: number
    kdj_k?: number
    kdj_d?: number
  }
}

export interface DiscoveryRunResponse {
  success: boolean
  total_scanned: number
  discoveries_found: number
  saved: number
  message: string
}

export interface DiscoveryListResponse {
  total: number
  items: DiscoveryItem[]
}

export interface ThresholdConfig {
  vol_ratio_min: number
  turnover_rate_min: number
  change_pct_min: number
  change_pct_max: number
  rsi_max: number
  rsi_min: number
}

export const discoveryApi = {
  // 运行发现任务
  run(params: {
    period?: string
    limit?: number
    min_score?: number
    save?: boolean
  }): Promise<DiscoveryRunResponse> {
    return api.post('/discovery/run', null, { params })
  },

  // 获取发现列表
  getList(params: {
    limit?: number
    offset?: number
  }): Promise<DiscoveryListResponse> {
    return api.get('/discovery/list', { params })
  },

  // 获取热门发现（用于首页）
  getHot(limit?: number): Promise<DiscoveryListResponse> {
    return api.get('/discovery/hot', { params: { limit } })
  },

  // 获取当前阈值配置
  getThresholds(): Promise<ThresholdConfig> {
    return api.get('/discovery/thresholds')
  },
}