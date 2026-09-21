<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { dataCenterApi } from '@/api/dataCenter'
import { ElMessage } from 'element-plus'

const dataStatus = ref<any>(null)
const loading = ref(false)
const collecting = ref<string>('')

onMounted(async () => {
  await fetchStatus()
})

async function fetchStatus() {
  loading.value = true
  try {
    dataStatus.value = await dataCenterApi.getStatus()
  } catch (e) {
    console.error('获取数据状态失败:', e)
  } finally {
    loading.value = false
  }
}

async function handleCollect(type: string) {
  try {
    collecting.value = type
    let result

    switch (type) {
      case 'stocks':
        result = await dataCenterApi.collectStocks()
        break
      case 'daily':
        result = await dataCenterApi.collectDaily()
        break
      case 'sectors':
        result = await dataCenterApi.collectSectors()
        break
      case 'capital-flow':
        result = await dataCenterApi.collectCapitalFlow()
        break
      case 'all':
        result = await dataCenterApi.collectAll()
        break
      case 'history':
        result = await dataCenterApi.syncHistory(365)
        break
      default:
        collecting.value = ''
        return
    }

    if (result?.success) {
      ElMessage.success(result.message)
    } else {
      ElMessage.error(result?.message || '采集失败')
    }

    await fetchStatus()
  } catch (e) {
    ElMessage.error('采集失败')
  } finally {
    collecting.value = ''
  }
}
</script>

<template>
  <div class="data-center">
    <el-row :gutter="20" class="mb-4">
      <el-col :span="24">
        <h1 class="page-title">数据中心</h1>
      </el-col>
    </el-row>

    <!-- 数据状态 -->
    <el-card class="status-card mb-4" v-loading="loading">
      <template #header>
        <span>数据状态</span>
        <el-button text @click="fetchStatus" size="small" style="float: right;">
          刷新
        </el-button>
      </template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="股票数量">
          {{ dataStatus?.database?.stocks || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="日线数据">
          {{ dataStatus?.database?.daily_records || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="指标数据">
          {{ dataStatus?.database?.indicator_records || 0 }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 基础数据采集 -->
    <el-card class="mb-4">
      <template #header>
        <span>基础数据采集</span>
      </template>
      <el-space wrap>
        <el-button
          type="primary"
          :loading="collecting === 'stocks'"
          @click="handleCollect('stocks')"
        >
          采集股票列表
        </el-button>
        <el-button
          type="success"
          :loading="collecting === 'daily'"
          @click="handleCollect('daily')"
        >
          采集日线数据
        </el-button>
      </el-space>
      <div class="tip-text">
        说明：股票列表包含基本信息，日线数据包含价格、成交量、涨跌幅等，是技术指标计算的基础
      </div>
    </el-card>

    <!-- 历史数据同步 -->
    <el-card class="mb-4">
      <template #header>
        <span>历史数据同步（Tushare - 耗时较长）</span>
      </template>
      <el-space wrap>
        <el-button
          type="warning"
          size="large"
          :loading="collecting === 'history'"
          @click="handleCollect('history')"
        >
          同步近3个月历史数据
        </el-button>
      </el-space>
      <div class="tip-text">
        说明：从Tushare同步近3个月日线数据并计算技术指标，预计耗时15-20分钟，请耐心等待
      </div>
    </el-card>

    <!-- 实时数据采集 -->
    <el-card class="mb-4">
      <template #header>
        <span>实时数据采集（股票发现依赖此数据）</span>
      </template>
      <el-space wrap>
        <el-button
          type="info"
          :loading="collecting === 'sectors'"
          @click="handleCollect('sectors')"
        >
          采集板块数据
        </el-button>
        <el-button
          type="danger"
          :loading="collecting === 'capital-flow'"
          @click="handleCollect('capital-flow')"
        >
          采集资金流数据
        </el-button>
      </el-space>
      <div class="tip-text">
        说明：板块数据和资金流数据用于股票发现的评分计算，采集一次可支持多次发现
      </div>
    </el-card>

    <!-- 一键采集 -->
    <el-card class="mb-4">
      <template #header>
        <span>一键采集（不包含历史数据）</span>
      </template>
      <el-space>
        <el-button
          type="success"
          size="large"
          :loading="collecting === 'all'"
          @click="handleCollect('all')"
        >
          一键采集（板块+资金流）
        </el-button>
      </el-space>
      <div class="tip-text">
        说明：同时采集板块数据+资金流数据，不包含日线历史数据
      </div>
    </el-card>

    <!-- 采集说明 -->
    <el-card>
      <template #header>
        <span>数据采集说明</span>
      </template>
      <el-steps direction="vertical" :space="60" active-line-width="2px">
        <el-step title="采集股票列表" description="从Tushare获取全市场股票基本信息（代码、名称、行业等）" />
        <el-step title="同步历史数据" description="从Tushare获取近3个月日线数据，并计算MA、MACD、RSI、KDJ等技术指标" />
        <el-step title="采集板块数据" description="从新浪财经获取行业/概念板块涨跌幅（175个板块）" />
        <el-step title="采集资金流数据" description="从腾讯财经获取个股主力/大单/中单/小单净流入数据" />
        <el-step title="执行股票发现" description="基于以上数据，进行四层股票发现分析" />
      </el-steps>
    </el-card>
  </div>
</template>

<style scoped>
.data-center {
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

.tip-text {
  margin-top: 12px;
  font-size: 12px;
  color: #909399;
}
</style>