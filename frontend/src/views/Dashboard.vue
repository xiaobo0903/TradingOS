<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMarketStore } from '@/store/market'
import { marketApi } from '@/api/market'

const router = useRouter()
const marketStore = useMarketStore()

const marketOverview = ref<any>(null)
const loading = ref(false)

const quickActions = [
  { path: '/screener', title: '股票发现', desc: '发现强势股、异动股', icon: '🔍' },
  { path: '/watchlist', title: '我的关注', desc: '管理自选股票', icon: '⭐' },
  { path: '/market', title: '市场行情', desc: '查看全市场行情', icon: '📊' },
  { path: '/data-center', title: '数据中心', desc: '数据采集与管理', icon: '💾' },
  { path: '/ai-analysis', title: 'AI分析', desc: '智能股票分析', icon: '🤖' },
]

onMounted(async () => {
  loading.value = true
  try {
    await Promise.all([
      marketStore.fetchIndices(),
      marketStore.fetchHotSectors(),
      fetchMarketOverview(),
    ])
  } finally {
    loading.value = false
  }
})

async function fetchMarketOverview() {
  try {
    marketOverview.value = await marketApi.getOverview()
  } catch (e) {
    console.error('获取市场概览失败:', e)
  }
}

function formatNumber(num: number | undefined, decimals: number = 2): string {
  if (num === undefined || num === null) return '--'
  return num.toFixed(decimals)
}

function formatAmount(num: number | undefined): string {
  if (num === undefined || num === null) return '--'
  if (num >= 100000000) {
    return (num / 100000000).toFixed(2) + '亿'
  } else if (num >= 10000) {
    return (num / 10000).toFixed(2) + '万'
  }
  return num.toFixed(2)
}

function getChangeClass(pct: number | undefined): string {
  if (pct === undefined || pct === null) return ''
  if (pct > 0) return 'price-up'
  if (pct < 0) return 'price-down'
  return ''
}

function goToStock(code: string) {
  router.push(`/stock/${code}`)
}
</script>

<template>
  <div class="dashboard">
    <el-row :gutter="20" class="mb-4">
      <el-col :span="24">
        <h1 class="page-title">市场概览</h1>
      </el-col>
    </el-row>

    <!-- 主要指数 -->
    <el-row :gutter="20" class="mb-4">
      <el-col :span="24">
        <div class="section-header">
          <span class="section-title">主要指数</span>
          <span class="data-source" v-if="marketStore.indices[0]?.source">
            数据来源: {{ marketStore.indices[0].source }}
          </span>
        </div>
      </el-col>
      <el-col
        v-for="index in marketStore.indices"
        :key="index.code"
        :xs="12"
        :sm="8"
        :md="6"
        :lg="4"
      >
        <el-card class="index-card" shadow="hover">
          <div class="index-name">{{ index.name }}</div>
          <div class="index-price" :class="getChangeClass(index.change_pct)">
            {{ formatNumber(index.current_price) }}
          </div>
          <div class="index-change" :class="getChangeClass(index.change_pct)">
            {{ index.change_pct > 0 ? '+' : '' }}{{ formatNumber(index.change_pct) }}%
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 市场统计和热门板块 -->
    <el-row :gutter="20">
      <!-- 市场统计 -->
      <el-col :span="12">
        <el-card class="stats-card">
          <template #header>
            <span>市场统计</span>
          </template>
          <el-row :gutter="10" v-if="marketOverview?.statistics">
            <el-col :span="12">
              <div class="stat-item">
                <span class="stat-label">上涨</span>
                <span class="stat-value price-up">{{ marketOverview.statistics.rising }}</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="stat-item">
                <span class="stat-label">下跌</span>
                <span class="stat-value price-down">{{ marketOverview.statistics.falling }}</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="stat-item">
                <span class="stat-label">涨停</span>
                <span class="stat-value limit-up">{{ marketOverview.statistics.limit_up }}</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="stat-item">
                <span class="stat-label">跌停</span>
                <span class="stat-value limit-down">{{ marketOverview.statistics.limit_down }}</span>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>

      <!-- 热门板块 -->
      <el-col :span="12">
        <el-card class="sector-card">
          <template #header>
            <div class="card-header">
              <span>热门板块</span>
              <span class="data-source" v-if="marketStore.hotSectorsSource">
                {{ marketStore.hotSectorsSource }}
              </span>
            </div>
          </template>
          <div class="sector-list">
            <div
              v-for="sector in marketStore.hotSectors.slice(0, 6)"
              :key="sector.板块名称 || sector.name"
              class="sector-item"
            >
              <span class="sector-name">{{ sector.板块名称 || sector.name }}</span>
              <span
                class="sector-change"
                :class="getChangeClass(sector.涨跌幅)"
              >
                {{ formatNumber(sector.涨跌幅 || sector.change_pct) }}%
              </span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 功能入口 -->
    <el-row :gutter="20" class="mt-4">
      <el-col :span="24">
        <h2 class="section-title">快速入口</h2>
      </el-col>
      <el-col :xs="12" :sm="8" :md="6" :lg="4" v-for="item in quickActions" :key="item.path">
        <el-card class="action-card" shadow="hover" @click="router.push(item.path)">
          <div class="action-icon">{{ item.icon }}</div>
          <div class="action-title">{{ item.title }}</div>
          <div class="action-desc">{{ item.desc }}</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.dashboard {
  padding: 0;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 20px;
}

.mb-4 {
  margin-bottom: 20px;
}

.mt-4 {
  margin-top: 20px;
}

.section-title {
  font-size: 18px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 15px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.data-source {
  font-size: 12px;
  color: #909399;
  background-color: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
}

.index-card {
  margin-bottom: 15px;
  text-align: center;
}

.index-name {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.index-price {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 4px;
}

.index-change {
  font-size: 14px;
}

.price-up {
  color: #f56c6c;
}

.price-down {
  color: #67c23a;
}

.limit-up {
  color: #f56c6c;
}

.limit-down {
  color: #67c23a;
}

.stats-card,
.sector-card {
  height: 100%;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.stat-label {
  color: #909399;
}

.stat-value {
  font-weight: 600;
  font-size: 18px;
}

.sector-list {
  display: flex;
  flex-direction: column;
}

.sector-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.sector-name {
  color: #303133;
}

.sector-change {
  font-weight: 500;
}

.action-card {
  cursor: pointer;
  text-align: center;
  margin-bottom: 15px;
  transition: all 0.3s;
}

.action-card:hover {
  transform: translateY(-5px);
}

.action-icon {
  font-size: 32px;
  margin-bottom: 10px;
}

.action-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 5px;
}

.action-desc {
  font-size: 12px;
  color: #909399;
}
</style>
