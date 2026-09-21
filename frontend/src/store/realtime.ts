import { defineStore } from 'pinia'
import { ref } from 'vue'
import { dataCenterApi, type StockRealtimeItem } from '@/api/dataCenter'

export const useRealtimeStore = defineStore('realtime', () => {
  // 股票列表
  const stocks = ref<StockRealtimeItem[]>([])
  const total = ref(0)
  const loading = ref(false)

  // 查询参数
  const tradeDate = ref<string | undefined>(undefined)
  const search = ref<string>('')
  const sortBy = ref<string>('pct_chg')
  const order = ref<string>('desc')
  const limit = ref(100)
  const offset = ref(0)

  // 排序选项
  const sortOptions = [
    { value: 'pct_chg', label: '涨幅%' },
    { value: 'turnover_rate', label: '换手%' },
    { value: 'volume_ratio', label: '量比' },
    { value: 'amplitude', label: '振幅%' },
    { value: 'amount', label: '成交额' },
    { value: 'volume', label: '成交量' },
    { value: 'total_market_cap', label: '总市值' },
    { value: 'float_market_cap', label: '流通市值' },
    { value: 'close', label: '现价' },
    { value: 'change', label: '涨跌' },
    { value: 'stock_code', label: '代码' },
    { value: 'stock_name', label: '名称' },
  ]

  // 获取股票列表
  async function fetchStocks() {
    loading.value = true
    try {
      const response = await dataCenterApi.getRealtimeList({
        trade_date: tradeDate.value,
        search: search.value || undefined,
        sort_by: sortBy.value,
        order: order.value,
        limit: limit.value,
        offset: offset.value,
      })
      stocks.value = response.items
      total.value = response.total
      return response
    } finally {
      loading.value = false
    }
  }

  // 设置交易日期
  function setTradeDate(date: string | undefined) {
    tradeDate.value = date
    offset.value = 0
  }

  // 设置搜索关键词
  function setSearch(keyword: string) {
    search.value = keyword
    offset.value = 0
  }

  // 设置排序
  function setSort(field: string) {
    if (sortBy.value === field) {
      order.value = order.value === 'desc' ? 'asc' : 'desc'
    } else {
      sortBy.value = field
      order.value = 'desc'
    }
    offset.value = 0
  }

  // 设置分页
  function setPage(page: number) {
    offset.value = (page - 1) * limit.value
  }

  // 格式化市值
  function formatMarketCap(value: number): string {
    if (value >= 100000000000) {
      return (value / 100000000000).toFixed(2) + '万亿'
    } else if (value >= 100000000) {
      return (value / 100000000).toFixed(2) + '亿'
    } else if (value >= 10000) {
      return (value / 10000).toFixed(2) + '万'
    }
    return value.toFixed(2)
  }

  return {
    // 状态
    stocks,
    total,
    loading,
    tradeDate,
    search,
    sortBy,
    order,
    limit,
    offset,
    sortOptions,

    // 方法
    fetchStocks,
    setTradeDate,
    setSearch,
    setSort,
    setPage,
    formatMarketCap,
  }
})
