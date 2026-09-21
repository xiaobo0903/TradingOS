<script setup lang="ts">
import { ref, computed } from 'vue'
import { sectorApi, type CSVImportResponse, type ImportedDataItem } from '@/api/sector'
import { ElMessage, ElMessageBox } from 'element-plus'

const emit = defineEmits<{
  (e: 'imported'): void
}>()

// 状态
const loading = ref(false)
const uploading = ref(false)
const importResult = ref<CSVImportResponse | null>(null)
const importedData = ref<ImportedDataItem[]>([])
const importedTotal = ref(0)

// 表单数据
const sectorName = ref('')
const tradeDate = ref(new Date().toISOString().split('T')[0])
const uploadFile = ref<File | null>(null)

// 文件选择
function handleFileChange(file: any) {
  uploadFile.value = file.raw
}

// 上传CSV
async function handleImport() {
  if (!sectorName.value) {
    ElMessage.warning('请输入板块名称')
    return
  }
  if (!tradeDate.value) {
    ElMessage.warning('请选择数据日期')
    return
  }
  if (!uploadFile.value) {
    ElMessage.warning('请选择CSV文件')
    return
  }

  uploading.value = true
  try {
    const result = await sectorApi.importCSV(sectorName.value, tradeDate.value, uploadFile.value)
    importResult.value = result

    if (result.success) {
      ElMessage.success(`导入成功！共 ${result.imported} 条`)
      if (result.unmatched_codes.length > 0) {
        ElMessage.warning(`有 ${result.unmatched_codes.length} 个股票代码无法匹配`)
      }
      // 刷新导入数据列表
      await fetchImportedData()
      emit('imported')
    } else {
      ElMessage.error(result.errors[0] || '导入失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '导入失败')
  } finally {
    uploading.value = false
  }
}

// 获取已导入数据
async function fetchImportedData() {
  loading.value = true
  try {
    const result = await sectorApi.getImportedData({
      sector_name: sectorName.value || undefined,
      trade_date: tradeDate.value || undefined,
      limit: 100
    })
    importedData.value = result.items
    importedTotal.value = result.total
  } catch (e) {
    console.error('获取导入数据失败:', e)
  } finally {
    loading.value = false
  }
}

// 下载模板
function downloadTemplate() {
  sectorApi.getCSVTemplate().then(template => {
    const headers = template.columns.map(c => c.name).join(',')
    const example = template.example.map((row: any) =>
      template.columns.map(c => row[c.name] || '').join(',')
    ).join('\n')
    const csv = `${headers}\n${example}`
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = template.filename
    link.click()
    URL.revokeObjectURL(url)
  })
}

// 重置表单
function resetForm() {
  sectorName.value = ''
  tradeDate.value = new Date().toISOString().split('T')[0]
  uploadFile.value = null
  importResult.value = null
}
</script>

<template>
  <div class="csv-import">
    <el-card class="mb-4">
      <template #header>
        <span>CSV导入板块数据</span>
        <el-button text @click="downloadTemplate" size="small" style="float: right;">
          下载模板
        </el-button>
      </template>

      <el-form :model="{ sectorName, tradeDate }" label-width="100px">
        <el-form-item label="板块名称">
          <el-input
            v-model="sectorName"
            placeholder="如：锂电池、芯片概念"
            style="width: 300px"
          />
        </el-form-item>

        <el-form-item label="数据日期">
          <el-date-picker
            v-model="tradeDate"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 200px"
          />
        </el-form-item>

        <el-form-item label="CSV文件">
          <el-upload
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            accept=".csv"
            drag
          >
            <el-icon><upload-filled /></el-icon>
            <div>拖拽文件或点击上传</div>
            <template #tip>
              <div class="el-upload__tip">支持 UTF-8 或 GBK 编码的 CSV 文件</div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleImport" :loading="uploading">
            导入数据
          </el-button>
          <el-button @click="fetchImportedData">查看已导入数据</el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 导入结果 -->
    <el-card v-if="importResult" class="mb-4">
      <template #header>
        <span>导入结果</span>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="总行数">
          {{ importResult.total_rows }}
        </el-descriptions-item>
        <el-descriptions-item label="成功导入">
          <el-tag type="success">{{ importResult.imported }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="跳过">
          {{ importResult.skipped }}
        </el-descriptions-item>
        <el-descriptions-item label="无法匹配的股票">
          {{ importResult.unmatched_codes.length }}
        </el-descriptions-item>
      </el-descriptions>

      <div v-if="importResult.unmatched_codes.length > 0" class="mt-4">
        <el-alert type="warning" :closable="false">
          <template #title>
            以下股票代码在系统中未找到：
          </template>
          <div>{{ importResult.unmatched_codes.join(', ') }}</div>
        </el-alert>
      </div>

      <div v-if="importResult.preview.length > 0" class="mt-4">
        <h4>预览（前10条）</h4>
        <el-table :data="importResult.preview" size="small" stripe>
          <el-table-column prop="stock_code" label="股票代码" width="100" />
          <el-table-column prop="stock_name" label="股票名称" />
          <el-table-column prop="close" label="收盘价" width="100" />
          <el-table-column prop="change_pct" label="涨跌幅" width="100">
            <template #default="{ row }">
              <span :class="parseFloat(row.change_pct) >= 0 ? 'text-up' : 'text-down'">
                {{ row.change_pct }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="matched" label="匹配状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.matched ? 'success' : 'danger'" size="small">
                {{ row.matched ? '已匹配' : '未匹配' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 已导入数据列表 -->
    <el-card v-loading="loading">
      <template #header>
        <span>已导入数据</span>
        <span class="ml-4 text-gray">共 {{ importedTotal }} 条</span>
      </template>

      <el-table :data="importedData" stripe size="small" max-height="400">
        <el-table-column prop="sector_name" label="板块" width="120" />
        <el-table-column prop="trade_date" label="日期" width="100" />
        <el-table-column prop="stock_code" label="代码" width="100" />
        <el-table-column prop="stock_name" label="名称" />
        <el-table-column prop="close" label="收盘价" width="80" />
        <el-table-column prop="change_pct" label="涨跌幅" width="80">
          <template #default="{ row }">
            <span :class="parseFloat(row.change_pct) >= 0 ? 'text-up' : 'text-down'">
              {{ row.change_pct }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="volume" label="成交量" width="100" />
        <el-table-column prop="turnover_rate" label="换手率" width="80">
          <template #default="{ row }">
            {{ row.turnover_rate }}%
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.csv-import {
  padding: 0;
}

.mb-4 {
  margin-bottom: 20px;
}

.mt-4 {
  margin-top: 16px;
}

.ml-4 {
  margin-left: 16px;
}

.text-up {
  color: #f56c6c;
}

.text-down {
  color: #67c23a;
}

.text-gray {
  color: #909399;
  font-size: 12px;
}
</style>
