import api from './index'

export interface LogEntry {
  timestamp: string
  level: string
  logger: string
  message: string
  category: string
  exception?: string
}

export interface LogQueryResponse {
  total: number
  logs: LogEntry[]
}

export const logsApi = {
  query(params: {
    keyword?: string
    level?: string
    category?: string
    start_time?: string
    end_time?: string
    limit?: number
    offset?: number
  }): Promise<LogQueryResponse> {
    return api.get('/logs/query', { params })
  },

  getLevels(): Promise<string[]> {
    return api.get('/logs/levels')
  },

  getCategories(): Promise<string[]> {
    return api.get('/logs/categories')
  },
}