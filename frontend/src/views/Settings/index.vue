<template>
  <div class="settings-page">
    <div class="page-header">
      <h1 class="page-title">系统设置</h1>
    </div>

    <div class="settings-content">
      <!-- Basic Settings -->
      <div class="settings-section">
        <div class="section-title">基础设置</div>
        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-label">主题模式</div>
            <div class="setting-desc">选择系统界面主题</div>
          </div>
          <el-radio-group v-model="settings.theme">
            <el-radio label="dark">深色</el-radio>
            <el-radio label="light">浅色</el-radio>
          </el-radio-group>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-label">自选股同步</div>
            <div class="setting-desc">自动同步自选股到云端</div>
          </div>
          <el-switch v-model="settings.syncEnabled" />
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-label">消息通知</div>
            <div class="setting-desc">接收系统消息和提醒</div>
          </div>
          <el-switch v-model="settings.notifications" />
        </div>
      </div>

      <!-- AI Settings -->
      <div class="settings-section">
        <div class="section-title">AI模型设置</div>
        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-label">AI模型</div>
            <div class="setting-desc">选择用于分析的AI模型</div>
          </div>
          <el-select v-model="settings.aiModel" style="width: 200px">
            <el-option label="Qwen3-14B" value="qwen3-14b" />
            <el-option label="Qwen3-32B" value="qwen3-32b" />
            <el-option label="DeepSeek-R1" value="deepseek-r1" />
          </el-select>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-label">AI响应温度</div>
            <div class="setting-desc">控制AI输出的随机性（0-1）</div>
          </div>
          <el-slider v-model="settings.temperature" :min="0" :max="1" :step="0.1" style="width: 200px" />
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-label">RAG知识库</div>
            <div class="setting-desc">启用检索增强生成</div>
          </div>
          <el-switch v-model="settings.ragEnabled" />
        </div>
      </div>

      <!-- Data Settings -->
      <div class="settings-section">
        <div class="section-title">数据设置</div>
        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-label">数据源</div>
            <div class="setting-desc">选择行情数据源</div>
          </div>
          <el-select v-model="settings.dataSource" style="width: 200px">
            <el-option label="东方财富" value="eastmoney" />
            <el-option label="新浪财经" value="sina" />
            <el-option label="腾讯财经" value="tencent" />
          </el-select>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-label">刷新频率</div>
            <div class="setting-desc">行情数据自动刷新间隔</div>
          </div>
          <el-select v-model="settings.refreshInterval" style="width: 200px">
            <el-option label="3秒" :value="3" />
            <el-option label="5秒" :value="5" />
            <el-option label="10秒" :value="10" />
            <el-option label="30秒" :value="30" />
          </el-select>
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-label">缓存数据</div>
            <div class="setting-desc">本地缓存历史数据</div>
          </div>
          <el-switch v-model="settings.cacheEnabled" />
        </div>
      </div>

      <!-- Alert Settings -->
      <div class="settings-section">
        <div class="section-title">预警设置</div>
        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-label">涨跌幅预警</div>
            <div class="setting-desc">自选股涨跌幅超过设定值时提醒</div>
          </div>
          <el-input-number v-model="settings.priceAlertThreshold" :min="1" :max="20" /> %
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-label">异动提醒</div>
            <div class="setting-desc">股票出现异常波动时提醒</div>
          </div>
          <el-switch v-model="settings.abnormalAlert" />
        </div>

        <div class="setting-item">
          <div class="setting-info">
            <div class="setting-label">涨停提醒</div>
            <div class="setting-desc">自选股涨停时发送通知</div>
          </div>
          <el-switch v-model="settings.limitUpAlert" />
        </div>
      </div>

      <!-- About -->
      <div class="settings-section">
        <div class="section-title">关于</div>
        <div class="about-info">
          <div class="about-item">
            <span class="about-label">版本</span>
            <span class="about-value">v1.0.0</span>
          </div>
          <div class="about-item">
            <span class="about-label">构建日期</span>
            <span class="about-value">2026-07-22</span>
          </div>
          <div class="about-item">
            <span class="about-label">技术栈</span>
            <span class="about-value">Vue3 + FastAPI + PostgreSQL</span>
          </div>
        </div>
        <div class="about-actions">
          <el-button>检查更新</el-button>
          <el-button>导出设置</el-button>
          <el-button type="danger" text>恢复默认</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'

const settings = reactive({
  theme: 'dark',
  syncEnabled: true,
  notifications: true,
  aiModel: 'qwen3-14b',
  temperature: 0.7,
  ragEnabled: true,
  dataSource: 'eastmoney',
  refreshInterval: 5,
  cacheEnabled: true,
  priceAlertThreshold: 5,
  abnormalAlert: true,
  limitUpAlert: true
})
</script>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 800px;
}

.settings-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-info {
  flex: 1;
}

.setting-label {
  font-weight: 500;
  margin-bottom: 4px;
}

.setting-desc {
  font-size: 12px;
  color: var(--text-secondary);
}

.about-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.about-item {
  display: flex;
  gap: 16px;
}

.about-label {
  color: var(--text-secondary);
  min-width: 80px;
}

.about-value {
  font-weight: 500;
}

.about-actions {
  display: flex;
  gap: 8px;
}
</style>
