import api from './index'

export interface IndexSpot {
  code: string
  name: string
  current_price: number
  change_pct: number
  volume: number
  amount: number
  source?: string
}

export interface MarketStatistics {
  rising: number
  falling: number
  limit_up: number
  limit_down: number
  total_amount: number
  source?: string
}

export interface HotSectorResponse {
  source: string
  data: any[]
}

export const marketApi = {
  // 获取主要指数
  getIndices(): Promise<IndexSpot[]> {
    return api.get('/market/indices')
  },

  // 获取市场概览
  getOverview(): Promise<any> {
    return api.get('/market/overview')
  },

  // 获取热门板块
  getHotSectors(limit?: number): Promise<HotSectorResponse> {
    return api.get('/market/hot-sectors', { params: { limit } })
  },
}
