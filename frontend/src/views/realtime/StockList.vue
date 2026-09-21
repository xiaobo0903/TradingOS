<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useRealtimeStore } from '@/store/realtime'
import { ElMessage, ElMessageBox } from 'element-plus'
import { subDays, format, isWeekend, previousFriday } from 'date-fns'
import { dataCenterApi } from '@/api/dataCenter'
import { UploadFilled } from '@element-plus/icons-vue'

const router = useRouter()
const realtimeStore = useRealtimeStore()

const searchInput = ref('')

// 上传相关
const uploadDialogVisible = ref(false)
const uploadLoading = ref(false)
const uploadFile = ref<File | null>(null)
const importResult = ref<{
  success: boolean
  message: string
  total_rows: number
  success_count: number
  error_count: number
  errors: { row: number; message: string; data: string }[]
} | null>(null)

// 计算上一个交易日（默认定位到前一日，如果是周末则取上周五）
function getPreviousTradingDay(): Date {
  let date = subDays(new Date(), 1)
  // 如果是周末，取上周五
  if (isWeekend(date)) {
    date = previousFriday(date)
  }
  return date
}

const selectedDate = ref(format(getPreviousTradingDay(), 'yyyy-MM-dd'))

// 获取数据
async function fetchData() {
  try {
    await realtimeStore.fetchStocks()
  } catch (e: any) {
    ElMessage.error(e.message || '获取数据失败')
  }
}

// 初始化
onMounted(() => {
  realtimeStore.setTradeDate(selectedDate.value)
  fetchData()
})

// 日期变更
function handleDateChange(date: string) {
  realtimeStore.setTradeDate(date)
  fetchData()
}

// 搜索
function handleSearch() {
  realtimeStore.setSearch(searchInput.value)
  fetchData()
}

// 排序
function handleSortChange({ prop, order }: any) {
  if (prop) {
    realtimeStore.sortBy = prop
    realtimeStore.order = order === 'ascending' ? 'asc' : 'desc'
    fetchData()
  }
}

// 分页
function handlePageChange(page: number) {
  realtimeStore.setPage(page)
  fetchData()
}

// 跳转到股票详情
function goToStock(code: string) {
  router.push(`/stock/${code}`)
}

// 格式化数字
function formatNumber(num: number | undefined | null, decimals: number = 2): string {
  if (num === undefined || num === null) return '--'
  return num.toFixed(decimals)
}

// 格式化市值
function formatMarketCap(value: number | undefined | null): string {
  if (!value) return '--'
  if (value >= 1e12) return (value / 1e12).toFixed(2) + '万亿'
  if (value >= 1e8) return (value / 1e8).toFixed(2) + '亿'
  if (value >= 1e4) return (value / 1e4).toFixed(2) + '万'
  return value.toString()
}

// 格式化股本（单位已是亿）
function formatShare(value: number | undefined | null): string {
  if (!value) return '--'
  return value.toFixed(2) + '亿'
}

// 涨跌幅样式
function getChangeClass(pct: number | undefined | null): string {
  if (pct === undefined || pct === null) return ''
  if (pct > 0) return 'price-up'
  if (pct < 0) return 'price-down'
  return ''
}

// 成交额格式化
function formatAmount(value: number | undefined | null): string {
  if (!value) return '--'
  if (value >= 1e8) return (value / 1e8).toFixed(2) + '亿'
  if (value >= 1e4) return (value / 1e4).toFixed(2) + '万'
  return value.toFixed(2)
}

// 打开上传弹窗
function openUploadDialog() {
  uploadFile.value = null
  importResult.value = null
  uploadDialogVisible.value = true
}

// 文件选择
function handleFileChange(file: any) {
  uploadFile.value = file.raw
}

// 上传CSV
async function handleUpload() {
  if (!uploadFile.value) {
    ElMessage.warning('请选择CSV文件')
    return
  }

  uploadLoading.value = true
  importResult.value = null

  try {
    const formData = new FormData()
    formData.append('file', uploadFile.value)

    const result = await dataCenterApi.importStockData(selectedDate.value, formData)
    importResult.value = result

    if (result.success) {
      ElMessage.success(result.message)
    } else {
      ElMessage.warning(result.message)
    }
  } catch (e: any) {
    ElMessage.error(e.message || '导入失败')
  } finally {
    uploadLoading.value = false
  }
}

// 下载CSV模板
function downloadTemplate() {
  const template = `序号1,序号2,股票代码,名称,主力净量,主力净流入,换手%,委比%,买一价,卖一价
1,1,600519,贵州茅台,0,0,0.5,0,0,0
2,2,000858,五粮液,0,0,0.3,0,0,0`

  const blob = new Blob([template], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = '股票数据导入模板.csv'
  link.click()
  URL.revokeObjectURL(url)
}

// 当前页
const currentPage = computed(() => {
  return Math.floor(realtimeStore.offset / realtimeStore.limit) + 1
})

// 总页数
const totalPages = computed(() => {
  return Math.ceil(realtimeStore.total / realtimeStore.limit)
})
</script>

<template>
  <div class="stock-list-page">
    <el-row :gutter="20" class="mb-4">
      <el-col :span="24">
        <h1 class="page-title">股票明细</h1>
      </el-col>
    </el-row>

    <!-- 搜索和筛选 -->
    <el-card class="mb-4">
      <el-row :gutter="20" align="middle">
        <el-col :span="8">
          <el-input
            v-model="searchInput"
            placeholder="搜索股票代码或名称"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button @click="handleSearch">搜索</el-button>
            </template>
          </el-input>
        </el-col>
        <el-col :span="8">
          <el-date-picker
            v-model="selectedDate"
            type="date"
            placeholder="选择交易日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :clearable="false"
            @change="handleDateChange"
            class="date-picker"
          />
        </el-col>
        <el-col :span="8" class="text-right">
          <span class="data-info">
            共 {{ realtimeStore.total }} 只股票
          </span>
        </el-col>
      </el-row>
    </el-card>

    <!-- 数据表格 -->
    <el-card v-loading="realtimeStore.loading">
      <template #header>
        <div class="card-header">
          <span>股票列表</span>
          <div>
            <el-button type="primary" size="small" @click="openUploadDialog">
              导入数据
            </el-button>
            <span class="result-count">{{ realtimeStore.stocks.length }} 条/页</span>
          </div>
        </div>
      </template>

      <el-table
        :data="realtimeStore.stocks"
        stripe
        style="width: 100%"
        @sort-change="handleSortChange"
        @row-click="(row: any) => goToStock(row.stock_code)"
        class="stock-table"
      >
        <el-table-column label="代码" prop="stock_code" width="90" sortable fixed>
          <template #default="{ row }">
            <span class="stock-code">{{ row.stock_code }}</span>
          </template>
        </el-table-column>

        <el-table-column label="名称" prop="stock_name" width="100" sortable>
          <template #default="{ row }">
            <span class="stock-name">{{ row.stock_name }}</span>
          </template>
        </el-table-column>

        <el-table-column label="涨幅%" prop="pct_chg" width="80" sortable>
          <template #default="{ row }">
            <span :class="getChangeClass(row.pct_chg)">
              {{ formatNumber(row.pct_chg) }}%
            </span>
          </template>
        </el-table-column>

        <el-table-column label="现价" prop="close" width="80" sortable>
          <template #default="{ row }">
            <span :class="getChangeClass(row.pct_chg)">
              {{ formatNumber(row.close) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="涨跌" prop="change" width="80" sortable>
          <template #default="{ row }">
            <span :class="getChangeClass(row.change)">
              {{ formatNumber(row.change) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="量比" prop="volume_ratio" width="70" sortable>
          <template #default="{ row }">
            {{ formatNumber(row.volume_ratio) }}
          </template>
        </el-table-column>

        <el-table-column label="换手%" prop="turnover_rate" width="80" sortable>
          <template #default="{ row }">
            {{ formatNumber(row.turnover_rate) }}%
          </template>
        </el-table-column>

        <el-table-column label="振幅%" prop="amplitude" width="80" sortable>
          <template #default="{ row }">
            {{ formatNumber(row.amplitude) }}%
          </template>
        </el-table-column>

        <el-table-column label="总量" prop="volume" width="100" sortable>
          <template #default="{ row }">
            {{ formatAmount(row.volume) }}
          </template>
        </el-table-column>

        <el-table-column label="总金额" prop="amount" width="100" sortable>
          <template #default="{ row }">
            {{ formatAmount(row.amount) }}
          </template>
        </el-table-column>

        <el-table-column label="总市值" prop="total_market_cap" width="100" sortable>
          <template #default="{ row }">
            {{ formatMarketCap(row.total_market_cap) }}
          </template>
        </el-table-column>

        <el-table-column label="流通市值" prop="float_market_cap" width="100" sortable>
          <template #default="{ row }">
            {{ formatMarketCap(row.float_market_cap) }}
          </template>
        </el-table-column>

        <el-table-column label="昨收" prop="pre_close" width="80">
          <template #default="{ row }">
            {{ formatNumber(row.pre_close) }}
          </template>
        </el-table-column>

        <el-table-column label="今开" prop="open" width="80">
          <template #default="{ row }">
            {{ formatNumber(row.open) }}
          </template>
        </el-table-column>

        <el-table-column label="最高" prop="high" width="80">
          <template #default="{ row }">
            <span :class="getChangeClass(row.pct_chg)">
              {{ formatNumber(row.high) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="最低" prop="low" width="80">
          <template #default="{ row }">
            <span :class="getChangeClass(row.pct_chg)">
              {{ formatNumber(row.low) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="总股本" prop="total_share" width="100">
          <template #default="{ row }">
            {{ formatShare(row.total_share) }}
          </template>
        </el-table-column>

        <el-table-column label="流通股本" prop="float_share" width="100">
          <template #default="{ row }">
            {{ formatShare(row.float_share) }}
          </template>
        </el-table-column>

        <el-table-column label="PE" prop="pe" width="80">
          <template #default="{ row }">
            {{ formatNumber(row.pe) }}
          </template>
        </el-table-column>

        <el-table-column label="PB" prop="pb" width="80">
          <template #default="{ row }">
            {{ formatNumber(row.pb) }}
          </template>
        </el-table-column>

        <el-table-column label="主力净流入" prop="main_inflow" width="110" sortable>
          <template #default="{ row }">
            <span :class="getChangeClass(row.main_inflow)">
              {{ formatAmount(row.main_inflow) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="委比%" prop="weibi" width="80" sortable>
          <template #default="{ row }">
            {{ formatNumber(row.weibi) }}%
          </template>
        </el-table-column>

        <el-table-column label="买一价" prop="buy_price" width="80">
          <template #default="{ row }">
            {{ formatNumber(row.buy_price) }}
          </template>
        </el-table-column>

        <el-table-column label="卖一价" prop="sell_price" width="80">
          <template #default="{ row }">
            {{ formatNumber(row.sell_price) }}
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          :page-sizes="[50, 100, 200, 500]"
          :page-size="realtimeStore.limit"
          :total="realtimeStore.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="(size: number) => { realtimeStore.limit = size; realtimeStore.offset = 0; fetchData() }"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 上传弹窗 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="导入股票数据"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="upload-content">
        <div class="template-download">
          <span>CSV格式要求：</span>
          <el-button type="text" @click="downloadTemplate">下载模板文件</el-button>
        </div>

        <el-table :data="[{ date: selectedDate }]" border size="small">
          <el-table-column prop="date" label="导入日期" />
        </el-table>

        <div class="upload-tip">
          <p>CSV文件格式（无表头），共10列：</p>
          <ol>
            <li>序号1（忽略）</li>
            <li>序号2（忽略）</li>
            <li>股票代码</li>
            <li>名称</li>
            <li>主力净量</li>
            <li>主力净流入（元）</li>
            <li>换手%</li>
            <li>委比%</li>
            <li>买一价</li>
            <li>卖一价</li>
          </ol>
        </div>

        <el-upload
          class="upload-demo"
          drag
          :auto-upload="false"
          :limit="1"
          accept=".csv"
          :on-change="handleFileChange"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">将CSV文件拖到此处，或<em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip">只能上传CSV文件</div>
          </template>
        </el-upload>

        <!-- 导入结果 -->
        <div v-if="importResult" class="import-result">
          <el-alert
            :title="importResult.message"
            :type="importResult.success ? 'success' : 'warning'"
            :closable="false"
            show-icon
          />
          <div class="result-summary">
            <span>总行数：{{ importResult.total_rows }}</span>
            <span class="success">成功：{{ importResult.success_count }}</span>
            <span class="error">失败：{{ importResult.error_count }}</span>
          </div>

          <!-- 错误详情 -->
          <el-collapse v-if="importResult.errors.length > 0" class="error-details">
            <el-collapse-item title="查看错误详情" name="errors">
              <el-table :data="importResult.errors" size="small" max-height="200">
                <el-table-column prop="row" label="行号" width="60" />
                <el-table-column prop="message" label="错误信息" />
                <el-table-column prop="data" label="原始数据" show-overflow-tooltip />
              </el-table>
            </el-collapse-item>
          </el-collapse>
        </div>
      </div>

      <template #footer>
        <el-button @click="uploadDialogVisible = false">关闭</el-button>
        <el-button
          type="primary"
          :loading="uploadLoading"
          :disabled="!uploadFile"
          @click="handleUpload"
        >
          确认导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.stock-list-page {
  padding: 20px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.mb-4 {
  margin-bottom: 16px;
}

.text-right {
  text-align: right;
  line-height: 40px;
}

.data-info {
  color: #909399;
  font-size: 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header > div {
  display: flex;
  align-items: center;
  gap: 12px;
}

.result-count {
  color: #909399;
  font-size: 14px;
}

.stock-table {
  cursor: pointer;
}

.stock-code {
  color: #409eff;
  font-family: monospace;
}

.stock-name {
  font-weight: 500;
}

.price-up {
  color: #f56c6c;
}

.price-down {
  color: #67c23a;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.date-picker {
  width: 100%;
}

.upload-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.template-download {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
}

.upload-tip {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
}

.upload-tip p {
  margin: 0 0 8px 0;
}

.upload-tip ol {
  margin: 0;
  padding-left: 20px;
}

.upload-tip li {
  line-height: 1.8;
}

.import-result {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.result-summary {
  display: flex;
  gap: 20px;
  font-size: 14px;
}

.result-summary .success {
  color: #67c23a;
}

.result-summary .error {
  color: #f56c6c;
}

.error-details {
  margin-top: 8px;
}
</style>
