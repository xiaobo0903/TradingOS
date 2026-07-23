<template>
  <div class="watchlist-page">
    <div class="page-header">
      <h1 class="page-title">我的自选股</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          添加股票
        </el-button>
        <el-button @click="sortByAI">
          <el-icon><Sort /></el-icon>
          AI排序
        </el-button>
      </div>
    </div>

    <div class="watchlist-content">
      <el-table :data="watchStocks" stripe style="width: 100%" @row-click="handleRowClick">
        <el-table-column prop="code" label="股票代码" width="100" />
        <el-table-column prop="name" label="股票名称" width="120">
          <template #default="{ row }">
            <div class="stock-name-cell">
              <span class="name">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="price" label="现价" width="100">
          <template #default="{ row }">
            <span class="price">{{ row.price.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="change" label="涨跌幅" width="100">
          <template #default="{ row }">
            <span :class="row.change >= 0 ? 'text-up' : 'text-down'">
              {{ row.change >= 0 ? '+' : '' }}{{ row.change.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="volumeRatio" label="量比" width="80" />
        <el-table-column prop="rsi" label="RSI" width="100">
          <template #default="{ row }">
            <el-progress
              :percentage="row.rsi"
              :color="getRSIColor(row.rsi)"
              :show-text="false"
              :stroke-width="6"
            />
            <span class="rsi-value">{{ row.rsi }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="aiScore" label="AI评分" width="120">
          <template #default="{ row }">
            <div class="ai-score-cell">
              <el-progress
                :percentage="row.aiScore"
                :color="getScoreColor(row.aiScore)"
                :show-text="false"
                :stroke-width="6"
              />
              <span class="score-value">{{ row.aiScore }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="trend" label="趋势" width="100">
          <template #default="{ row }">
            <el-tag :type="getTrendType(row.trend)" size="small">
              {{ row.trend }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" text size="small" @click.stop="analyzeStock(row.code)">
              分析
            </el-button>
            <el-button type="danger" text size="small" @click.stop="removeStock(row.code)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- AI Sorting Section -->
    <div class="ai-opportunities">
      <div class="section-header">
        <span class="section-title">AI推荐机会</span>
      </div>
      <div class="opportunity-list">
        <div v-for="stock in aiOpportunities" :key="stock.code" class="opportunity-card" @click="analyzeStock(stock.code)">
          <div class="opp-rank">{{ stock.rank }}</div>
          <div class="opp-info">
            <div class="opp-name">{{ stock.name }}</div>
            <div class="opp-reason">{{ stock.reason }}</div>
          </div>
          <div class="opp-score">
            <div class="score-label">AI评分</div>
            <div class="score-value">{{ stock.aiScore }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Stock Dialog -->
    <el-dialog v-model="showAddDialog" title="添加自选股" width="400px">
      <el-autocomplete
        v-model="addQuery"
        :fetch-suggestions="searchStock"
        placeholder="搜索股票代码或名称..."
        :trigger-on-focus="false"
        clearable
        class="add-stock-input"
        @select="handleAddStock"
      >
        <template #default="{ item }">
          <div class="search-item">
            <span class="stock-name">{{ item.value }}</span>
            <span class="stock-code">{{ item.code }}</span>
          </div>
        </template>
      </el-autocomplete>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Sort } from '@element-plus/icons-vue'

const router = useRouter()

const showAddDialog = ref(false)
const addQuery = ref('')

const watchStocks = ref([
  { code: '600519', name: '贵州茅台', price: 1650.25, change: 2.35, volumeRatio: 1.8, rsi: 68, aiScore: 88, trend: '强势' },
  { code: '000858', name: '五粮液', price: 168.5, change: 3.21, volumeRatio: 2.1, rsi: 72, aiScore: 85, trend: '强势' },
  { code: '002594', name: '比亚迪', price: 268.3, change: 4.56, volumeRatio: 2.5, rsi: 75, aiScore: 90, trend: '启动' },
  { code: '600036', name: '招商银行', price: 35.8, change: 1.89, volumeRatio: 1.3, rsi: 55, aiScore: 78, trend: '震荡' },
  { code: '601318', name: '中国平安', price: 48.2, change: 2.12, volumeRatio: 1.6, rsi: 62, aiScore: 82, trend: '偏强' }
])

const aiOpportunities = ref([
  { rank: 1, code: '002594', name: '比亚迪', reason: '趋势强 + 资金流入 + 技术突破', aiScore: 90 },
  { rank: 2, code: '600519', name: '贵州茅台', reason: 'MACD金叉 + 板块龙头', aiScore: 88 },
  { rank: 3, code: '300750', name: '宁德时代', reason: '放量上涨 + 主力吸筹', aiScore: 86 }
])

const searchStock = (query: string, cb: (results: Array<{ value: string; code: string }>) => void) => {
  const mockStocks = [
    { value: '贵州茅台', code: '600519' },
    { value: '五粮液', code: '000858' },
    { value: '比亚迪', code: '002594' },
    { value: '招商银行', code: '600036' },
    { value: '中国平安', code: '601318' },
    { value: '宁德时代', code: '300750' },
    { value: '隆基绿能', code: '601012' },
    { value: '海康威视', code: '002415' }
  ]
  cb(mockStocks.filter(s => s.value.includes(query) || s.code.includes(query)))
}

const handleAddStock = (item: { value: string; code: string }) => {
  const exists = watchStocks.value.find(s => s.code === item.code)
  if (!exists) {
    watchStocks.value.push({
      code: item.code,
      name: item.value,
      price: Math.random() * 500 + 50,
      change: (Math.random() - 0.5) * 10,
      volumeRatio: Math.random() * 3 + 0.5,
      rsi: Math.floor(Math.random() * 40) + 30,
      aiScore: Math.floor(Math.random() * 30) + 60,
      trend: '震荡'
    })
  }
  showAddDialog.value = false
  addQuery.value = ''
}

const removeStock = (code: string) => {
  const index = watchStocks.value.findIndex(s => s.code === code)
  if (index > -1) {
    watchStocks.value.splice(index, 1)
  }
}

const analyzeStock = (code: string) => {
  router.push(`/stock/${code}`)
}

const handleRowClick = (row: any) => {
  router.push(`/stock/${row.code}`)
}

const sortByAI = () => {
  watchStocks.value.sort((a, b) => b.aiScore - a.aiScore)
}

const getRSIColor = (rsi: number): string => {
  if (rsi > 70) return '#F5222D'
  if (rsi < 30) return '#52C41A'
  return '#1a73e8'
}

const getScoreColor = (score: number): string => {
  if (score >= 80) return '#52C41A'
  if (score >= 60) return '#FAAD14'
  return '#F5222D'
}

const getTrendType = (trend: string): string => {
  if (trend === '强势' || trend === '启动') return 'danger'
  if (trend === '偏强') return 'warning'
  if (trend === '震荡') return 'info'
  return 'success'
}
</script>

<style scoped>
.watchlist-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.watchlist-content {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
}

.watchlist-content :deep(.el-table) {
  background-color: transparent;
}

.watchlist-content :deep(.el-table th.el-table__cell) {
  background-color: transparent;
  color: var(--text-secondary);
}

.price {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.ai-score-cell,
.rsi-value-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-score-cell .el-progress,
.rsi-value-cell .el-progress {
  flex: 1;
}

.score-value,
.rsi-value {
  font-size: 12px;
  font-weight: 600;
  min-width: 24px;
}

.ai-opportunities {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
}

.section-header {
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
}

.opportunity-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.opportunity-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: var(--transition-fast);
}

.opportunity-card:hover {
  background: var(--bg-card-hover);
}

.opp-rank {
  width: 28px;
  height: 28px;
  background: var(--color-ai);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
}

.opp-info {
  flex: 1;
}

.opp-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.opp-reason {
  font-size: 11px;
  color: var(--text-secondary);
}

.opp-score {
  text-align: center;
}

.score-label {
  font-size: 10px;
  color: var(--text-secondary);
}

.score-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-ai);
}

.add-stock-input {
  width: 100%;
}

.search-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stock-name {
  font-weight: 600;
}

.stock-code {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
