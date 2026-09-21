import { defineStore } from 'pinia'
import { ref } from 'vue'
import { discoveryApi, type DiscoveryItem } from '@/api/discovery'

export const useDiscoveryStore = defineStore('discovery', () => {
  const discoveries = ref<DiscoveryItem[]>([])
  const loading = ref(false)
  const running = ref(false)
  const lastRunTime = ref<string>('')

  async function runDiscovery(params?: {
    period?: string
    limit?: number
    min_score?: number
  }) {
    running.value = true
    try {
      const response = await discoveryApi.run({
        period: params?.period || 'short',
        limit: params?.limit || 50,
        min_score: params?.min_score || 60,
        save: true,
      })
      lastRunTime.value = new Date().toLocaleTimeString()
      return response
    } finally {
      running.value = false
    }
  }

  async function fetchDiscoveries(params?: {
    limit?: number
    offset?: number
  }) {
    loading.value = true
    try {
      const response = await discoveryApi.getList({
        limit: params?.limit || 50,
        offset: params?.offset || 0,
      })
      discoveries.value = response.items
      return response
    } finally {
      loading.value = false
    }
  }

  async function fetchHotDiscoveries(limit: number = 10) {
    try {
      const response = await discoveryApi.getHot(limit)
      return response.items
    } catch (e) {
      console.error('获取热门发现失败:', e)
      return []
    }
  }

  return {
    discoveries,
    loading,
    running,
    lastRunTime,
    runDiscovery,
    fetchDiscoveries,
    fetchHotDiscoveries,
  }
})