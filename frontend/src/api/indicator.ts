import api from './index'

export interface IndicatorAnalysis {
  stock_code: string
  current_price: number
  analysis: {
    macd: any
    rsi: any
    boll: any
    kdj: any
    ma: {
      signals: string[]
      latest: Record<string, number>
    }
    ma_arrangement?: string
  }
}

export const indicatorApi = {
  // 计算指标
  calculate(stockCode: string, indicators?: string[]) {
    return api.post('/indicators/calculate', {
      stock_code: stockCode,
      indicators,
    })
  },

  // 综合技术分析
  analyze(code: string, currentPrice?: number) {
    return api.get<IndicatorAnalysis>(`/indicators/analyze/${code}`, {
      params: { current_price: currentPrice },
    })
  },
}
