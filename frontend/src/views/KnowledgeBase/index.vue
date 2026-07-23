<template>
  <div class="knowledge-page">
    <div class="page-header">
      <h1 class="page-title">股票知识库</h1>
    </div>

    <div class="knowledge-content">
      <!-- Category Tree -->
      <div class="category-panel">
        <div class="panel-title">知识分类</div>
        <el-tree
          :data="categories"
          :props="{ children: 'children', label: 'label' }"
          default-expand-all
          @node-click="handleCategoryClick"
        />
      </div>

      <!-- Knowledge Content -->
      <div class="content-panel">
        <!-- Knowledge List -->
        <div class="knowledge-list" v-if="!selectedArticle">
          <div class="section-title">{{ currentCategory || '全部知识' }}</div>
          <div class="article-list">
            <div
              v-for="article in filteredArticles"
              :key="article.id"
              class="article-card"
              @click="selectArticle(article)"
            >
              <div class="article-icon">{{ article.icon }}</div>
              <div class="article-info">
                <div class="article-title">{{ article.title }}</div>
                <div class="article-summary">{{ article.summary }}</div>
              </div>
              <div class="article-meta">
                <el-tag size="small">{{ article.category }}</el-tag>
              </div>
            </div>
          </div>
        </div>

        <!-- Article Detail -->
        <div class="article-detail" v-else>
          <div class="detail-header">
            <el-button text @click="selectedArticle = null">
              <el-icon><ArrowLeft /></el-icon>
              返回列表
            </el-button>
          </div>
          <div class="detail-content">
            <h2 class="detail-title">{{ selectedArticle.title }}</h2>
            <div class="detail-body" v-html="selectedArticle.content"></div>
          </div>
        </div>
      </div>

      <!-- AI Q&A Panel -->
      <div class="qa-panel">
        <div class="panel-title">AI问答</div>
        <div class="qa-container">
          <div class="qa-messages" ref="qaMessagesRef">
            <div v-for="(msg, index) in qaMessages" :key="index" class="qa-message" :class="msg.role">
              <div class="qa-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</div>
              <div class="qa-content">
                <div class="qa-text">{{ msg.content }}</div>
                <div class="qa-time">{{ msg.time }}</div>
              </div>
            </div>
          </div>
          <div class="qa-input">
            <el-input
              v-model="qaInput"
              placeholder="输入股票相关问题..."
              @keyup.enter="sendQuestion"
            />
            <el-button type="primary" @click="sendQuestion">提问</el-button>
          </div>
        </div>

        <!-- Quick Questions -->
        <div class="quick-questions">
          <div class="quick-title">常见问题</div>
          <div class="quick-list">
            <el-tag
              v-for="q in quickQuestions"
              :key="q"
              class="quick-tag"
              @click="askQuickQuestion(q)"
            >
              {{ q }}
            </el-tag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ArrowLeft } from '@element-plus/icons-vue'

const currentCategory = ref('')
const selectedArticle = ref<any>(null)
const qaInput = ref('')

const categories = [
  {
    label: '股票基础',
    children: [
      { label: '股票基本概念' },
      { label: 'PE和PB' },
      { label: '市值与流通' },
      { label: '交易规则' }
    ]
  },
  {
    label: '技术分析',
    children: [
      { label: 'K线基础' },
      { label: '均线系统' },
      { label: 'MACD指标' },
      { label: 'RSI指标' },
      { label: 'BOLL指标' },
      { label: 'KDJ指标' }
    ]
  },
  {
    label: 'K线形态',
    children: [
      { label: '底部形态' },
      { label: '顶部形态' },
      { label: '持续形态' }
    ]
  },
  {
    label: '主力行为',
    children: [
      { label: '吸筹特征' },
      { label: '洗盘识别' },
      { label: '出货信号' }
    ]
  },
  {
    label: '交易心理',
    children: [
      { label: '恐惧与贪婪' },
      { label: '止损原则' },
      { label: '仓位管理' }
    ]
  }
]

const articles = [
  { id: 1, title: 'MACD指标详解', icon: '📊', category: '技术分析', summary: 'MACD是技术分析中最常用的指标之一，本 文详细介绍MACD的计算方法和实战应用。', content: '<p>MACD指标是 Moving Average Convergence Divergence 的缩写，中文译为指数平滑异同移动平均线。</p><h3>一、计算方法</h3><p>1. 计算短期EMA（通常为12日）<br>2. 计算长期EMA（通常为26日）<br>3. DIF = EMA12 - EMA26<br>4. DEA = DIF的9日EMA<br>5. MACD柱 = 2 × (DIF - DEA)</p><h3>二、应用规则</h3><p>1. 金叉：DIF上穿DEA，买入信号<br>2. 死叉：DIF下穿DEA，卖出信号<br>3. 零轴：DIF和DEA在零轴上方为多头市场</p>' },
  { id: 2, title: 'RSI指标详解', icon: '📈', category: '技术分析', summary: 'RSI是衡量股价变动速度和幅度的指标，本 文介绍RSI的使用技巧。', content: '<p>RSI (Relative Strength Index) 相对强弱指数，由Welles Wilder提出。</p><h3>一、计算公式</h3><p>RSI = 100 - 100/(1+RS)<br>其中RS = N日内涨幅均值/N日内跌幅均值</p><h3>二、应用规则</h3><p>1. RSI > 70：超买区域，注意风险<br>2. RSI < 30：超卖区域，关注机会<br>3. RSI背离：价格创新低但RSI未创新低，底部信号</p>' },
  { id: 3, title: '早晨之星形态', icon: '🌟', category: 'K线形态', summary: '早晨之星是重要的底部反转形态，本 文详细讲解其特征和识别方法。', content: '<p>早晨之星是由三根K线组成的底部反转形态。</p><h3>形态特征</h3><p>1. 第一根：下跌趋势中的大阴线<br>2. 第二根：小实体K线，星线<br>3. 第三根：上涨的大阳线，收复第一根大部分失地</p><h3>识别要点</h3><p>1. 必须出现在下跌趋势中<br>2. 第三根K线必须放量上涨<br>3. 整体形态类似星星在黎明前升起</p>' },
  { id: 4, title: '主力吸筹特征', icon: '💰', category: '主力行为', summary: '识别主力吸筹行为是跟庄盈利的关键，本 文总结主力吸筹的技术特征。', content: '<p>主力吸筹是指机构投资者在低位大量买入股票的行为。</p><h3>主要特征</h3><p>1. 低位成交量放大<br>2. 股价震荡但重心不下移<br>3. 大单频繁出现<br>4. 换手率温和提升<br>5. 下跌时缩量，上涨时放量</p>' },
  { id: 5, title: 'BOLL布林带详解', icon: '🔴', category: '技术分析', summary: '布林带是判断股价波动范围的指标，本 文介绍其计算和应用方法。', content: '<p>BOLL指标由John Bollinger发明，由上轨、中轨、下轨三条线组成。</p><h3>计算方法</h3><p>中轨 = MA20<br>上轨 = 中轨 + 2×标准差<br>下轨 = 中轨 - 2×标准差</p><h3>应用规则</h3><p>1. 突破上轨：强势上涨<br>2. 跌破下轨：弱势<br>3. 开口扩大：行情启动<br>4. 收口：行情盘整</p>' }
]

const filteredArticles = computed(() => {
  if (!currentCategory.value) return articles
  return articles.filter(a => a.category === currentCategory.value)
})

const qaMessages = ref([
  {
    role: 'assistant',
    content: '您好！我是股票知识库AI助手。请问有什么关于股票投资的问题想要了解？',
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
])

const quickQuestions = [
  '什么是MACD金叉？',
  '如何判断主力吸筹？',
  'RSI多少算超买？',
  '早晨之星形态特征',
  'BOLL指标使用技巧'
]

const handleCategoryClick = (data: any) => {
  currentCategory.value = data.label
}

const selectArticle = (article: any) => {
  selectedArticle.value = article
}

const sendQuestion = () => {
  if (!qaInput.value.trim()) return

  qaMessages.value.push({
    role: 'user',
    content: qaInput.value,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  })

  setTimeout(() => {
    qaMessages.value.push({
      role: 'assistant',
      content: '感谢您的问题。关于"' + qaInput.value + '"，建议您查看知识库中的相关技术指标详解，或者咨询更专业的内容。您可以点击常见问题快速获取答案。',
      time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    })
  }, 1000)

  qaInput.value = ''
}

const askQuickQuestion = (question: string) => {
  qaInput.value = question
  sendQuestion()
}
</script>

<style scoped>
.knowledge-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.knowledge-content {
  flex: 1;
  display: grid;
  grid-template-columns: 240px 1fr 320px;
  gap: 16px;
  min-height: 0;
}

.category-panel,
.qa-panel {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
  overflow-y: auto;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 16px;
}

.category-panel :deep(.el-tree) {
  background: transparent;
  color: var(--text-primary);
}

.category-panel :deep(.el-tree-node__content) {
  height: 36px;
}

.content-panel {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 16px;
  overflow-y: auto;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
}

.article-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.article-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition-fast);
}

.article-card:hover {
  background: var(--bg-card-hover);
}

.article-icon {
  font-size: 28px;
}

.article-info {
  flex: 1;
}

.article-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.article-summary {
  font-size: 12px;
  color: var(--text-secondary);
}

.article-detail {
  display: flex;
  flex-direction: column;
}

.detail-header {
  margin-bottom: 16px;
}

.detail-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
}

.detail-body {
  line-height: 1.8;
}

.detail-body :deep(h3) {
  font-size: 16px;
  font-weight: 600;
  margin: 16px 0 8px;
}

.detail-body :deep(p) {
  margin-bottom: 12px;
}

.qa-container {
  display: flex;
  flex-direction: column;
  height: 300px;
}

.qa-messages {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.qa-message {
  display: flex;
  gap: 8px;
}

.qa-avatar {
  font-size: 20px;
}

.qa-content {
  flex: 1;
}

.qa-text {
  padding: 10px;
  border-radius: var(--radius-md);
  font-size: 13px;
  line-height: 1.5;
}

.qa-message.user .qa-text {
  background: var(--color-info);
  color: white;
}

.qa-message.assistant .qa-text {
  background: var(--bg-secondary);
}

.qa-time {
  font-size: 10px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.qa-input {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.qa-input .el-input {
  flex: 1;
}

.quick-questions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.quick-title {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.quick-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-tag {
  cursor: pointer;
  font-size: 11px;
}
</style>
