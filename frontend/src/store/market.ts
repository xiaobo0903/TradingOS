import { defineStore } from 'pinia'
import { ref } from 'vue'
import { marketApi, type IndexSpot } from '@/api/market'

export const useMarketStore = defineStore('market', () => {
  const indices = ref<IndexSpot[]>([])
  const hotSectors = ref<any[]>([])
  const hotSectorsSource = ref<string>('')
  const overview = ref<any>(null)
  const loading = ref(false)

  async function fetchIndices() {
    loading.value = true
    try {
      indices.value = await marketApi.getIndices()
    } catch (e) {
      console.error('获取指数失败:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchHotSectors(limit: number = 10) {
    try {
      const response = await marketApi.getHotSectors(limit)
      // 处理响应格式 { source: string, data: any[] }
      if (response && typeof response === 'object' && 'source' in response) {
        hotSectorsSource.value = (response as any).source || ''
        hotSectors.value = (response as any).data || []
      } else {
        // 兼容旧格式（直接返回数组）
        hotSectorsSource.value = ''
        hotSectors.value = response as any[]
      }
    } catch (e) {
      console.error('获取热门板块失败:', e)
    }
  }

  async function fetchOverview() {
    try {
      overview.value = await marketApi.getOverview()
    } catch (e) {
      console.error('获取市场概览失败:', e)
    }
  }

  return {
    indices,
    hotSectors,
    hotSectorsSource,
    overview,
    loading,
    fetchIndices,
    fetchHotSectors,
    fetchOverview,
  }
})
