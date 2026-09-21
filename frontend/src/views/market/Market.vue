<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { sectorApi, type SectorItem } from '@/api/sector'
import { useRouter } from 'vue-router'

const router = useRouter()

// 热门板块数据
const hotSectors = ref<SectorItem[]>([])
const sectorsTotal = ref(0)
const loading = ref(false)

// 板块类型过滤
const sectorType = ref('')
const sectorTypes = [
  { value: '', label: '全部' },
  { value: 'industry', label: '行业板块' },
  { value: 'concept', label: '概念板块' },
  { value: 'region', label: '地域板块' },
]

// 当前选中板块详情
const selectedSector = ref<SectorItem | null>(null)
const sectorStocks = ref<any[]>([])
const sectorDetailLoading = ref(false)

// 获取热门板块
async function fetchHotSectors() {
  loading.value = true
  try {
    const response = await sectorApi.getHot(30)
    hotSectors.value = response.items || []
    sectorsTotal.value = response.total || 0
  } catch (e) {
    console.error('获取热门板块失败:', e)
  } finally {
    loading.value = false
  }
}

// 获取板块内股票
async function fetchSectorStocks(code: string) {
  sectorDetailLoading.value = true
  try {
    const response = await sectorApi.getStocks(code, { sort_by: 'change_pct', limit: 20 })
    sectorStocks.value = response.items || []
  } catch (e) {
    console.error('获取板块股票失败:', e)
  } finally {
    sectorDetailLoading.value = false
  }
}

// 选择板块查看详情
function selectSector(sector: SectorItem) {
  selectedSector.value = sector
  fetchSectorStocks(sector.code)
}

// 关闭详情
function closeDetail() {
  selectedSector.value = null
  sectorStocks.value = []
}

// 格式化涨跌幅
function formatChange(pct: number | undefined): string {
  if (pct === undefined || pct === null) return '--'
  return pct > 0 ? `+${pct.toFixed(2)}%` : `${pct.toFixed(2)}%`
}

// 获取涨跌幅样式
function getChangeClass(pct: number): string {
  if (pct > 0) return 'price-up'
  if (pct < 0) return 'price-down'
  return ''
}

// 获取排名颜色
function getRankColor(rank: number): string {
  if (rank <= 3) return '#f56c6c'  // 红
  if (rank <= 10) return '#e6a23c' // 橙
  if (rank <= 20) return '#67c23a' // 绿
  return '#909399' // 灰
}

// 跳转到股票详情
function goToStock(code: string) {
  router.push(`/stock/${code}`)
}

// 获取热度标签
function getHeatLabel(score: number): string {
  if (score >= 30) return '爆热'
  if (score >= 20) return '热门'
  if (score >= 10) return '活跃'
  if (score >= 5) return '平稳'
  return '低迷'
}

// 获取热度颜色
function getHeatColor(score: number): string {
  if (score >= 30) return '#f56c6c'
  if (score >= 20) return '#e6a23c'
  if (score >= 10) return '#67c23a'
  return '#909399'
}

onMounted(() => {
  fetchHotSectors()
})
</script>

<template>
  <div class="market-page">
    <el-row :gutter="20" class="mb-4">
      <el-col :span="24">
        <h1 class="page-title">市场行情</h1>
      </el-col>
    </el-row>

    <!-- 热门板块标题 -->
    <el-row :gutter="20" class="mb-4">
      <el-col :span="12">
        <span class="section-title">🔥 热门板块</span>
        <span class="section-subtitle">基于涨跌幅、成交量、龙头股表现综合计算热度</span>
      </el-col>
      <el-col :span="12" style="text-align: right;">
        <el-button text @click="fetchHotSectors">刷新</el-button>
      </el-col>
    </el-row>

    <!-- 热门板块列表 -->
    <el-card v-loading="loading" class="mb-4">
      <el-table
        :data="hotSectors"
        style="width: 100%"
        @row-click="selectSector"
        :row-class-name="() => 'sector-row'"
      >
        <el-table-column label="排名" width="70">
          <template #default="{ row }">
            <span
              class="rank-badge"
              :style="{ backgroundColor: getRankColor(row.rank) }"
            >
              {{ row.rank }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="板块名称" width="150">
          <template #default="{ row }">
            <div class="sector-name-cell">
              <span class="sector-name">{{ row.name }}</span>
              <span class="sector-type">{{ row.type === 'industry' ? '行业' : row.type === 'concept' ? '概念' : '地域' }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="热度评分" width="120">
          <template #default="{ row }">
            <div class="heat-cell">
              <span
                class="heat-score"
                :style="{ color: getHeatColor(row.heat_score) }"
              >
                {{ row.heat_score.toFixed(1) }}
              </span>
              <el-tag size="small" :style="{ backgroundColor: getHeatColor(row.heat_score), borderColor: getHeatColor(row.heat_score), color: '#fff' }">
                {{ getHeatLabel(row.heat_score) }}
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="涨跌幅" width="100">
          <template #default="{ row }">
            <span :class="getChangeClass(row.change_pct)" class="change-pct">
              {{ formatChange(row.change_pct) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="股票数量" width="90">
          <template #default="{ row }">
            <span class="stock-count">{{ row.stock_count }}</span>
          </template>
        </el-table-column>

        <el-table-column label="龙头股">
          <template #default="{ row }">
            <div class="lead-stocks">
              <span
                v-for="stock in row.lead_stocks?.slice(0, 3)"
                :key="stock.code"
                class="lead-stock-tag"
                :class="getChangeClass(stock.change_pct)"
                @click.stop="goToStock(stock.code)"
              >
                {{ stock.name }} {{ formatChange(stock.change_pct) }}
              </span>
              <span v-if="!row.lead_stocks?.length" class="no-data">--</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="热度原因" min-width="200">
          <template #default="{ row }">
            <span class="heat-reason">{{ row.heat_reason || row.reason || '--' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click.stop="selectSector(row)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 板块详情抽屉 -->
    <el-drawer
      v-model="selectedSector"
      :title="`板块详情: ${selectedSector?.name}`"
      size="600px"
      direction="rtl"
    >
      <template #default>
        <div v-if="selectedSector" class="sector-detail">
          <!-- 板块概览 -->
          <el-card class="detail-overview">
            <el-row :gutter="20">
              <el-col :span="8">
                <div class="detail-item">
                  <span class="detail-label">热度排名</span>
                  <span
                    class="detail-value rank-badge-large"
                    :style="{ backgroundColor: getRankColor(selectedSector.rank || 0) }"
                  >
                    #{{ selectedSector.rank }}
                  </span>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="detail-item">
                  <span class="detail-label">热度评分</span>
                  <span
                    class="detail-value"
                    :style="{ color: getHeatColor(selectedSector.heat_score) }"
                  >
                    {{ selectedSector.heat_score.toFixed(1) }}
                  </span>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="detail-item">
                  <span class="detail-label">涨跌幅</span>
                  <span
                    class="detail-value"
                    :class="getChangeClass(selectedSector.change_pct)"
                  >
                    {{ formatChange(selectedSector.change_pct) }}
                  </span>
                </div>
              </el-col>
            </el-row>

            <el-row :gutter="20" class="mt-4">
              <el-col :span="12">
                <div class="detail-item">
                  <span class="detail-label">板块类型</span>
                  <span class="detail-value">
                    {{ selectedSector.type === 'industry' ? '行业板块' : selectedSector.type === 'concept' ? '概念板块' : '地域板块' }}
                  </span>
                </div>
              </el-col>
              <el-col :span="12">
                <div class="detail-item">
                  <span class="detail-label">股票数量</span>
                  <span class="detail-value">{{ selectedSector.stock_count }}</span>
                </div>
              </el-col>
            </el-row>

            <div class="detail-reason mt-4">
              <span class="detail-label">热度原因</span>
              <p class="reason-text">{{ selectedSector.heat_reason || selectedSector.reason || '板块平稳' }}</p>
            </div>
          </el-card>

          <!-- 龙头股 -->
          <h3 class="detail-section-title">龙头股</h3>
          <el-card class="mb-4">
            <div class="lead-stocks-detail">
              <el-tag
                v-for="stock in selectedSector.lead_stocks"
                :key="stock.code"
                class="lead-stock-card"
                :class="getChangeClass(stock.change_pct)"
                @click="goToStock(stock.code)"
              >
                <div class="lead-stock-info">
                  <span class="lead-stock-name">{{ stock.name }}</span>
                  <span class="lead-stock-code">{{ stock.code }}</span>
                </div>
                <span class="lead-stock-change">{{ formatChange(stock.change_pct) }}</span>
              </el-tag>
              <span v-if="!selectedSector.lead_stocks?.length" class="no-data">暂无龙头股数据</span>
            </div>
          </el-card>

          <!-- 板块内股票列表 -->
          <h3 class="detail-section-title">板块股票</h3>
          <el-card v-loading="sectorDetailLoading">
            <el-table :data="sectorStocks" style="width: 100%" @row-click="goToStock">
              <el-table-column label="股票" width="120">
                <template #default="{ row }">
                  <div class="stock-cell">
                    <span class="stock-name">{{ row.name }}</span>
                    <span class="stock-code">{{ row.code }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="现价" width="80">
                <template #default="{ row }">
                  <span :class="getChangeClass(row.change_pct)">
                    {{ row.current_price.toFixed(2) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="涨跌幅" width="100">
                <template #default="{ row }">
                  <span :class="getChangeClass(row.change_pct)">
                    {{ formatChange(row.change_pct) }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="换手率" width="80">
                <template #default="{ row }">
                  {{ row.turnover_rate.toFixed(2) }}%
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.market-page {
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
  margin-top: 16px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.section-subtitle {
  font-size: 12px;
  color: #909399;
  margin-left: 12px;
}

.sector-row {
  cursor: pointer;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  color: #fff;
  font-weight: 600;
  font-size: 12px;
}

.rank-badge-large {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  color: #fff;
  font-weight: 600;
  font-size: 16px;
}

.sector-name-cell {
  display: flex;
  flex-direction: column;
}

.sector-name {
  font-weight: 600;
  color: #303133;
}

.sector-type {
  font-size: 12px;
  color: #909399;
}

.heat-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.heat-score {
  font-weight: 600;
  font-size: 16px;
}

.change-pct {
  font-weight: 600;
}

.stock-count {
  color: #606266;
}

.lead-stocks {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.lead-stock-tag {
  padding: 2px 8px;
  cursor: pointer;
  font-size: 12px;
}

.heat-reason {
  font-size: 13px;
  color: #606266;
}

.price-up {
  color: #f56c6c;
}

.price-down {
  color: #67c23a;
}

.no-data {
  color: #909399;
  font-size: 13px;
}

/* 详情样式 */
.sector-detail {
  padding: 0 16px;
}

.detail-overview {
  background-color: #f5f7fa;
}

.detail-item {
  display: flex;
  flex-direction: column;
}

.detail-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.detail-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.detail-reason {
  padding-top: 12px;
  border-top: 1px solid #e6e6e6;
}

.reason-text {
  margin: 8px 0 0 0;
  color: #606266;
  font-size: 14px;
}

.detail-section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 20px 0 12px 0;
}

.lead-stocks-detail {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.lead-stock-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  min-width: 140px;
  cursor: pointer;
}

.lead-stock-info {
  display: flex;
  flex-direction: column;
}

.lead-stock-name {
  font-weight: 600;
  color: #303133;
}

.lead-stock-code {
  font-size: 12px;
  color: #909399;
}

.lead-stock-change {
  font-weight: 600;
}

.stock-cell {
  display: flex;
  flex-direction: column;
}

.stock-name {
  font-weight: 600;
  color: #303133;
}

.stock-code {
  font-size: 12px;
  color: #909399;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}
</style>