<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useScreenerStore } from '@/store/screener'
import { useDiscoveryStore } from '@/store/discovery'
import { ElMessage } from 'element-plus'

const router = useRouter()
const screenerStore = useScreenerStore()
const discoveryStore = useDiscoveryStore()

// 模式：discovery 或 screener
const mode = ref<'discovery' | 'screener'>('discovery')

// 缺省阈值说明
const thresholdDesc = {
  vol_ratio_min: '量比 > 1.5 表示放量',
  turnover_rate_min: '换手率 > 3% 表示活跃',
  change_pct_min: '涨幅 > 2% 表示有动力',
  change_pct_max: '涨幅 < 8% 避免高位',
  rsi_min: 'RSI > 30 避免超卖',
  rsi_max: 'RSI < 70 避免超买',
}

// 初始化
onMounted(async () => {
  await screenerStore.init()
  await discoveryStore.fetchDiscoveries()
})

// 监听筛选条件变化，自动查询
watch(
  () => screenerStore.filter,
  () => {
    if (mode.value === 'screener') {
      screenerStore.queryStocks()
    }
  },
  { deep: true }
)

// 执行发现
async function handleRunDiscovery() {
  await discoveryStore.runDiscovery({
    min_score: 60,
  })
  await discoveryStore.fetchDiscoveries()
}

// 模式切换
function switchMode(newMode: 'discovery' | 'screener') {
  mode.value = newMode
}

// 格式化数字
function formatNumber(num: number | undefined, decimals: number = 2): string {
  if (num === undefined || num === null) return '--'
  return num.toFixed(decimals)
}

// 格式化成交量
function formatVolume(vol: number | undefined): string {
  if (!vol) return '--'
  if (vol >= 1e8) return (vol / 1e8).toFixed(2) + '亿'
  if (vol >= 1e4) return (vol / 1e4).toFixed(2) + '万'
  return vol.toString()
}

// 涨跌幅样式
function getChangeClass(pct: number | undefined): string {
  if (pct === undefined || pct === null) return ''
  if (pct > 0) return 'price-up'
  if (pct < 0) return 'price-down'
  return ''
}

// 评分颜色
function getScoreColor(score: number | undefined): string {
  if (!score) return '#909399'
  if (score >= 80) return '#f56c6c'
  if (score >= 70) return '#e6a23c'
  if (score >= 60) return '#67c23a'
  return '#909399'
}

// 跳转到股票详情
function goToStock(code: string) {
  router.push(`/stock/${code}`)
}
</script>

<template>
  <div class="screener-page">
    <el-row :gutter="20" class="mb-4">
      <el-col :span="24">
        <h1 class="page-title">股票发现</h1>
      </el-col>
    </el-row>

    <!-- 模式切换 -->
    <el-card class="mb-4">
      <el-radio-group v-model="mode" class="mode-switch">
        <el-radio-button value="discovery">📊 智能发现</el-radio-button>
        <el-radio-button value="screener">🔍 条件筛选</el-radio-button>
      </el-radio-group>

      <div class="mode-desc">
        <span v-if="mode === 'discovery'">
          基于T-1日数据分析，找出满足买入条件的股票
        </span>
        <span v-else>
          通过多条件组合筛选股票
        </span>
      </div>

      <div v-if="mode === 'discovery'" class="threshold-info">
        <span class="threshold-title">发现条件（缺省阈值）：</span>
        <el-tag size="small" type="info" class="threshold-tag">量比 > 1.5</el-tag>
        <el-tag size="small" type="info" class="threshold-tag">换手率 > 3%</el-tag>
        <el-tag size="small" type="info" class="threshold-tag">涨幅 2%~8%</el-tag>
        <el-tag size="small" type="info" class="threshold-tag">MACD金叉</el-tag>
        <el-tag size="small" type="info" class="threshold-tag">KDJ金叉</el-tag>
        <span class="threshold-hint">（至少满足2个条件）</span>
      </div>
    </el-card>

    <!-- 智能发现模式 -->
    <div v-if="mode === 'discovery'">
      <el-card class="mb-4">
        <div class="discovery-actions">
          <el-button
            type="primary"
            size="large"
            :loading="discoveryStore.running"
            @click="handleRunDiscovery"
          >
            {{ discoveryStore.running ? '分析中...' : '🚀 执行发现' }}
          </el-button>
          <span v-if="discoveryStore.lastRunTime" class="last-run-time">
            上次运行: {{ discoveryStore.lastRunTime }}
          </span>
        </div>
      </el-card>

      <!-- 发现结果列表 -->
      <el-card v-loading="discoveryStore.loading">
        <template #header>
          <div class="card-header">
            <span>发现结果</span>
            <span class="result-count">共 {{ discoveryStore.discoveries.length }} 只</span>
          </div>
        </template>

        <el-table
          :data="discoveryStore.discoveries"
          stripe
          style="width: 100%"
          @row-click="(row: any) => goToStock(row.code)"
        >
          <el-table-column label="股票" width="120" fixed>
            <template #default="{ row }">
              <div class="stock-cell">
                <span class="stock-name">{{ row.name }}</span>
                <span class="stock-code">{{ row.code }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="评分" width="80" sortable>
            <template #default="{ row }">
              <span
                class="score-value"
                :style="{ color: getScoreColor(row.score) }"
              >
                {{ row.score.toFixed(1) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="T-1收盘" width="100">
            <template #default="{ row }">
              <span :class="getChangeClass(row.change_pct)">
                {{ formatNumber(row.close) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="涨幅" width="100" sortable sort-by="change_pct">
            <template #default="{ row }">
              <span :class="getChangeClass(row.change_pct)">
                {{ row.change_pct > 0 ? '+' : '' }}{{ formatNumber(row.change_pct) }}%
              </span>
            </template>
          </el-table-column>

          <el-table-column label="换手率" width="80">
            <template #default="{ row }">
              {{ formatNumber(row.turnover_rate) }}%
            </template>
          </el-table-column>

          <el-table-column label="满足条件" min-width="300">
            <template #default="{ row }">
              <div class="conditions">
                <el-tag
                  v-for="(cond, idx) in row.conditions"
                  :key="idx"
                  size="small"
                  type="success"
                  class="condition-tag"
                >
                  {{ cond }}
                </el-tag>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="分析结论" min-width="150">
            <template #default="{ row }">
              <span class="reason-text">{{ row.reason }}</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click.stop="goToStock(row.code)">
                分析
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 条件筛选模式 -->
    <div v-if="mode === 'screener'">
      <!-- 行情条件 -->
      <el-card class="mb-4">
        <div class="filter-section">
          <span class="filter-title">行情条件</span>
        </div>

        <el-row :gutter="20">
          <el-col :span="6">
            <span class="filter-label">涨幅 %</span>
            <el-input-number
              v-model="screenerStore.filter.min_change_pct"
              placeholder="最小"
              size="small"
              :controls="false"
              style="width: 80px"
            />
            <span class="filter-separator">~</span>
            <el-input-number
              v-model="screenerStore.filter.max_change_pct"
              placeholder="最大"
              size="small"
              :controls="false"
              style="width: 80px"
            />
          </el-col>
          <el-col :span="6">
            <span class="filter-label">价格</span>
            <el-input-number
              v-model="screenerStore.filter.min_price"
              placeholder="最低"
              size="small"
              :controls="false"
              style="width: 80px"
            />
            <span class="filter-separator">~</span>
            <el-input-number
              v-model="screenerStore.filter.max_price"
              placeholder="最高"
              size="small"
              :controls="false"
              style="width: 80px"
            />
          </el-col>
          <el-col :span="6">
            <span class="filter-label">换手率 %</span>
            <el-input-number
              v-model="screenerStore.filter.min_turnover_rate"
              placeholder="最小"
              size="small"
              :controls="false"
              style="width: 80px"
            />
          </el-col>
          <el-col :span="6">
            <span class="filter-label">成交量</span>
            <el-input-number
              v-model="screenerStore.filter.min_volume"
              placeholder="最小"
              size="small"
              :controls="false"
              style="width: 100px"
            />
          </el-col>
        </el-row>

        <el-row :gutter="20" class="mt-4">
          <el-col :span="6">
            <span class="filter-label">市场</span>
            <el-select v-model="screenerStore.filter.market" placeholder="全部" clearable size="small" style="width: 120px">
              <el-option
                v-for="m in screenerStore.marketOptions"
                :key="m.value"
                :label="m.label"
                :value="m.value"
              />
            </el-select>
          </el-col>
          <el-col :span="6">
            <span class="filter-label">行业</span>
            <el-select v-model="screenerStore.filter.industry" placeholder="全部" clearable size="small" style="width: 150px">
              <el-option
                v-for="ind in screenerStore.industries"
                :key="ind"
                :label="ind"
                :value="ind"
              />
            </el-select>
          </el-col>
          <el-col :span="6">
            <span class="filter-label">排序</span>
            <el-select v-model="screenerStore.filter.sort_by" size="small" style="width: 100px">
              <el-option
                v-for="s in screenerStore.sortOptions"
                :key="s.value"
                :label="s.label"
                :value="s.value"
              />
            </el-select>
            <el-select v-model="screenerStore.filter.sort_order" size="small" style="width: 80px">
              <el-option label="降序" value="desc" />
              <el-option label="升序" value="asc" />
            </el-select>
          </el-col>
        </el-row>

        <div class="filter-actions mt-4">
          <el-button type="primary" @click="screenerStore.queryStocks" :loading="screenerStore.loading">查询</el-button>
          <el-button @click="screenerStore.resetFilter">重置</el-button>
          <span class="result-count">共 {{ screenerStore.total }} 只</span>
        </div>
      </el-card>

      <!-- 筛选结果列表 -->
      <el-card v-loading="screenerStore.loading">
        <template #header>
          <div class="card-header">
            <span>筛选结果</span>
          </div>
        </template>

        <el-table
          :data="screenerStore.stocks"
          stripe
          style="width: 100%"
          @row-click="(row: any) => goToStock(row.code)"
        >
          <el-table-column label="股票" width="120" fixed>
            <template #default="{ row }">
              <div class="stock-cell">
                <span class="stock-name">{{ row.name }}</span>
                <span class="stock-code">{{ row.code }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="现价" width="100">
            <template #default="{ row }">
              <span :class="getChangeClass(row.change_pct)">
                {{ formatNumber(row.current_price) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="涨跌幅" width="100" sortable sort-by="change_pct">
            <template #default="{ row }">
              <span :class="getChangeClass(row.change_pct)">
                {{ row.change_pct > 0 ? '+' : '' }}{{ formatNumber(row.change_pct) }}%
              </span>
            </template>
          </el-table-column>

          <el-table-column label="成交量" width="100">
            <template #default="{ row }">
              {{ formatVolume(row.volume) }}
            </template>
          </el-table-column>

          <el-table-column label="换手率" width="80">
            <template #default="{ row }">
              {{ formatNumber(row.turnover_rate) }}%
            </template>
          </el-table-column>

          <el-table-column label="发现原因">
            <template #default="{ row }">
              <span class="reason-text">{{ row.reason || '--' }}</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click.stop="goToStock(row.code)">
                分析
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.screener-page {
  padding: 0;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.mb-4 {
  margin-bottom: 20px;
}

.mt-4 {
  margin-top: 16px;
}

.mode-switch {
  margin-bottom: 12px;
}

.mode-desc {
  color: #606266;
  font-size: 14px;
  margin-bottom: 12px;
}

.threshold-info {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.threshold-title {
  font-weight: 600;
  color: #303133;
  margin-right: 8px;
}

.threshold-tag {
  margin-right: 4px;
}

.threshold-hint {
  color: #909399;
  font-size: 12px;
  margin-left: 8px;
}

.discovery-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.last-run-time {
  color: #909399;
  font-size: 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-count {
  color: #909399;
  font-size: 14px;
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

.score-value {
  font-weight: 600;
  font-size: 16px;
}

.price-up {
  color: #f56c6c;
}

.price-down {
  color: #67c23a;
}

.conditions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.condition-tag {
  margin-right: 4px;
}

.reason-text {
  font-size: 13px;
  color: #606266;
}

.filter-section {
  margin-bottom: 12px;
}

.filter-title {
  font-weight: 600;
  color: #303133;
}

.filter-label {
  display: inline-block;
  margin-right: 8px;
  color: #606266;
  font-size: 14px;
  min-width: 60px;
}

.filter-separator {
  margin: 0 4px;
  color: #909399;
}

.filter-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}
</style>