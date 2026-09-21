import api from './index'
import type { AxiosResponse } from 'axios'

export interface SectorItem {
  code: string
  name: string
  type: string
  change_pct: number
  stock_count: number
  lead_stocks: Array<{
    code: string
    name: string
    change_pct: number
  }>
  heat_score: number
  heat_reason?: string
  reason?: string
  rank?: number
}

export interface SectorListResponse {
  total: number
  items: SectorItem[]
}

export interface HotSectorsResponse {
  total: number
  items: SectorItem[]
}

export interface SectorStock {
  code: string
  name: string
  change_pct: number
  volume: number
  turnover_rate: number
  current_price: number
}

export interface SectorStocksResponse {
  sector_name: string
  total: number
  items: SectorStock[]
}

// CSV导入相关类型
export interface CSVTemplateResponse {
  filename: string
  columns: Array<{
    name: string
    description: string
    required: boolean
  }>
  example: any[]
}

export interface ImportedDataItem {
  id: number
  sector_id: number
  sector_name: string
  stock_code: string
  stock_name: string
  trade_date: string
  close: string
  change_pct: string
  volume: string
  turnover_rate: string
  open: string
  high: string
  low: string
  amount: string
}

export interface ImportedDataResponse {
  total: number
  items: ImportedDataItem[]
}

export interface CSVImportResponse {
  success: boolean
  total_rows: number
  imported: number
  skipped: number
  errors: string[]
  preview: Array<{
    stock_code: string
    stock_name: string
    close: string
    change_pct: string
    matched: boolean
  }>
  unmatched_codes: string[]
}

export const sectorApi = {
  // 获取板块列表
  getList(params: {
    sector_type?: string
    limit?: number
    offset?: number
  }): Promise<SectorListResponse> {
    return api.get('/sector/list', { params })
  },

  // 获取热门板块
  getHot(limit?: number): Promise<HotSectorsResponse> {
    return api.get('/sector/hot', { params: { limit } })
  },

  // 获取板块详情
  getDetail(sectorCode: string): Promise<any> {
    return api.get(`/sector/${sectorCode}`)
  },

  // 获取板块内股票
  getStocks(sectorCode: string, params?: {
    sort_by?: string
    order?: string
    limit?: number
  }): Promise<SectorStocksResponse> {
    return api.get(`/sector/${sectorCode}/stocks`, { params })
  },

  // 获取CSV模板
  getCSVTemplate(): Promise<CSVTemplateResponse> {
    return api.get('/sector/csv-template')
  },

  // 获取已导入的板块数据
  getImportedData(params?: {
    sector_name?: string
    trade_date?: string
    limit?: number
    offset?: number
  }): Promise<ImportedDataResponse> {
    return api.get('/sector/imported-data', { params })
  },

  // 导入CSV数据
  importCSV(sectorName: string, tradeDate: string, file: File): Promise<CSVImportResponse> {
    const formData = new FormData()
    formData.append('sector_name', sectorName)
    formData.append('trade_date', tradeDate)
    formData.append('file', file)
    return api.post('/sector/import-csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
}