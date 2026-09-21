# 股票发现模块 - 设计文档与实现核查

> 更新时间：2026-08-28
> 状态：开发中

---

## 一、四层处理逻辑

股票发现采用四层结构，将全市场股票逐步筛选为值得关注的候选股票。

### 第一层：市场扫描

从全市场扫描股票的基础数据：

| 数据项 | 设计要求 | 当前实现 | 状态 |
|-------|---------|---------|-----|
| 股票价格 | ✅ | ✅ open/high/low/close | 符合 |
| 涨跌幅 | ✅ | ✅ change_pct | 符合 |
| 成交量 | ✅ | ✅ volume | 符合 |
| 成交额 | ✅ | ✅ amount | 符合 |
| 换手率 | ✅ | ✅ turnover_rate | 符合 |
| 量比 | ✅ | ✅ vol_ratio = 今日成交量/5日均量 | **已实现** |
| 近5日最高/最低 | ✅ | ✅ recent_high / recent_low | **已实现** |
| 市值 | ✅ | ❌ 未获取 | 缺失 |
| 所属行业 | ✅ | ✅ industry | 符合 |
| 所属概念 | ✅ | ❌ 未获取 | 缺失 |
| 资金数据 | ✅ | ✅ 腾讯财经主力/大单/中单/小单净流入 | **已接入** |
| 人气数据 | ✅ | ❌ 未获取 | 缺失 |
| 技术指标 | ✅ | ✅ MA/MACD/RSI/KDJ/BOLL | 符合 |

### 第二层：行为筛选

判断股票当前发生了什么行为：

| 行为类型 | 设计要求 | 当前实现 | 阈值/逻辑 | 状态 |
|---------|---------|---------|----------|-----|
| 强势股 | 今日强势股 | ✅ | change_pct > 3% | 符合 |
| 成交量异常 | 放量/缩量 | ✅ 放量 | volume > avg + 2*std 或 量比>2 | 符合 |
| 放量上涨 | 放量+上涨 | ✅ | 组合 strong + volume_surge | 符合 |
| 缩量上涨 | 缩量+上涨 | ✅ | vol_ratio < 0.8 且 change_pct > 0 | **已实现** |
| 资金流入 | 资金净流入 | ✅ | 腾讯财经 main_inflow_pct > 15% | **已实现** |
| 换手率异常 | 换手率异常 | ✅ | turnover_rate > 10% | 符合 |
| 人气排名 | 涨幅靠前+放量 | ✅ | change_pct > 2% + volume_surge | 符合 |
| 板块热点 | 板块涨幅靠前 | ✅ | 通过所属industry板块涨跌幅评估 | **已实现** |
| 龙头候选 | 多因素综合 | ❌ | **未实现独立龙头评估** | 部分缺失 |
| 突破候选 | 突破近期高点 | ✅ | high > recent_max | 符合 |
| 回调候选 | 从高点回调 | ✅ | pullback > 5% + change_pct < 0 | 符合 |
| 超跌候选 | 超跌 | ✅ | change_pct < -5% 且 RSI < 30 | **已实现** |
| 技术指标共振 | 多指标同时满足 | ✅ | MACD金叉 + KDJ金叉 + MA多头 (≥2) | **已实现** |
| 新高 | 创近期新高 | ✅ | price >= max * 0.99 | 符合 |
| 新低 | 创近期新低 | ✅ | price <= min * 1.01 | **已实现** |
| 涨停相关 | 涨停 | ✅ | change_pct >= 9.9% | 符合 |
| 大单异常 | 大单异动 | ✅ | turnover_rate > 10% | 符合 |
| 分时异常 | 分时异常 | ❌ | **未实现**（需要分钟数据） | 缺失 |
| 基本面较好 | 基本面筛选 | ❌ | **未实现**（需要财务数据） | 缺失 |
| 多周期趋势较好 | 多周期向上 | ❌ | **未实现** | 缺失 |

### 第三层：趋势筛选

从不同持有周期进行分析：

#### 短期（1-5日关注）

| 指标 | 设计要求 | 当前实现 | 状态 |
|-----|---------|---------|-----|
| 分时 | ✅ | ❌ 未实现 | 缺失 |
| MA5 | ✅ | ✅ | 符合 |
| MA10 | ✅ | ✅ | 符合 |
| RSI | ✅ | ✅ | 符合 |
| KDJ | ✅ | ✅ | 符合 |
| MACD | ✅ | ✅ | 符合 |
| 量比 | ✅ | ✅ vol_ratio = 今日成交量/5日均量 | **已实现** |
| 换手率 | ✅ | ✅ | 符合 |
| 涨停 | ✅ | ✅ | 符合 |
| 资金异动 | ✅ | ✅ main_inflow_pct > 15% | **已实现** |

#### 中期（20-60日关注）

| 指标 | 设计要求 | 当前实现 | 状态 |
|-----|---------|---------|-----|
| MA20 | ✅ | ✅ | 符合 |
| MA30 | ✅ | ✅ | 符合 |
| MA60 | ✅ | ✅ | 符合 |
| MACD | ✅ | ✅ | 符合 |
| BOLL | ✅ | ✅ | 符合 |
| 成交量结构 | ✅ | ❌ 未实现 | 缺失 |
| 板块趋势 | ✅ | ❌ 未实现 | 缺失 |

#### 长期（基本面关注）

| 指标 | 设计要求 | 当前实现 | 状态 |
|-----|---------|---------|-----|
| 基本面 | ✅ | ❌ 未实现 | 缺失 |
| 营收 | ✅ | ❌ 未实现 | 缺失 |
| 净利润 | ✅ | ❌ 未实现 | 缺失 |
| ROE | ✅ | ❌ 未实现 | 缺失 |
| 现金流 | ✅ | ❌ 未实现 | 缺失 |
| 负债 | ✅ | ❌ 未实现 | 缺失 |
| 行业成长性 | ✅ | ❌ 未实现 | 缺失 |
| 估值 | ✅ | ❌ 未实现 | 缺失 |
| 长周期趋势 | ✅ | ❌ 未实现 | 缺失 |

### 第四层：综合评分

#### 评分权重配置

| 维度 | 短线(设计) | 短线(实现) | 中线(设计) | 中线(实现) | 长线(设计) | 长线(实现) |
|-----|-----------|-----------|-----------|-----------|-----------|-----------|
| 趋势 | 10% | 10% | 15% | 15% | 15% | 15% |
| 量能 | 20% | 20% | 15% | 15% | 10% | 10% |
| 资金 | 20% | ✅ 20% | 15% | ✅ 15% | 10% | ✅ 10% |
| 板块 | 15% | ✅ 15% | 20% | ✅ 20% | 20% | ✅ 20% |
| 人气 | 10% | 10% | - | 5% | - | 5% |
| 技术 | 25% | 25% | 高 | 30% | 15% | 15% |
| 基本面 | - | 0% | 中 | 0% | 高 | 25% |

**更新说明**：
- ✅ 资金分：已接入腾讯财经资金流数据，根据主力净流入占比计算
- ✅ 板块分：已接入新浪财经板块数据，根据板块涨跌幅计算
- ⚠️ 基本面分：长线有25%权重但未实现数据获取

---

## 二、当前实现架构

```
backend/services/discovery_service.py
├── scan_market()           # 市场扫描层
├── detect_behaviors()      # 行为筛选层
├── analyze_trends()        # 趋势筛选层
└── calculate_score()       # 综合评分层
```

### 核心数据结构

```python
# 股票数据
{
    'stock_id': int,
    'code': str,
    'name': str,
    'industry': str,
    'today': {
        'open': float,
        'high': float,
        'low': float,
        'close': float,
        'volume': float,
        'amount': float,
        'change_pct': float,
        'turnover_rate': float,
        'amplitude': float,
    },
    'history': [  # 近4日数据
        {'date': date, 'close': float, 'volume': float, 'change_pct': float}
    ],
    'avg_volume': float,
    'vol_std': float,
}

# 行为标签
{
    'strong': bool,        # 强势股
    'volume_surge': bool,  # 放量股
    'breakout': bool,      # 突破股
    'pullback': bool,      # 回调股
    'limit_up': bool,      # 涨停股
    'new_high': bool,      # 新高
    'large_order': bool,   # 大单异常
    'sentiment': bool,     # 人气股
}

# 趋势分析
{
    'short': 'up' | 'down' | 'neutral',
    'medium': 'up' | 'down' | 'neutral',
    'long': 'up' | 'down' | 'neutral',
    'signals': ['MA5>MA10', 'MACD金叉', ...]
}
```

---

## 三、缺失功能清单

### P0 - 影响发现准确性（高优先级）

| 功能 | 当前状态 | 实现方案 |
|-----|---------|---------|
| 资金分计算 | ✅ 已实现 | 腾讯财经资金流数据 |
| 板块分计算 | ✅ 已实现 | 新浪财经板块数据 |
| 量比计算 | ✅ 已实现 | 今日成交量/5日均量 |

### P1 - 功能完整性（中优先级）

| 功能 | 当前状态 | 实现方案 |
|-----|---------|---------|
| 资金流入识别 | ✅ 已实现 | main_inflow_pct > 15% |
| 板块热点 | ✅ 已实现 | 通过industry关联板块涨跌幅 |
| 龙头候选评估 | ❌ 未实现 | 综合涨幅+成交额+换手率+板块强度 |
| 缩量上涨识别 | ✅ 已实现 | vol_ratio < 0.8 且 change_pct > 0 |
| 超跌候选识别 | ✅ 已实现 | change_pct < -5% 且 RSI < 30 |
| 技术指标共振 | ✅ 已实现 | MACD金叉 + KDJ金叉 + MA多头 (≥2) |

### P2 - 增强功能（低优先级）

| 功能 | 当前状态 | 实现方案 |
|-----|---------|---------|
| 新低识别 | ✅ 已实现 | price <= min(history) * 1.01 |
| 分时异常 | ❌ 未实现 | 需分钟数据接入 |
| 基本面筛选 | ❌ 未实现 | 需 Tushare 财务数据接口 |
| 多周期趋势共振 | ❌ 未实现 | 短中长期趋势同时向上 |

---

## 四、后续优化计划

### Phase 1：数据源接入 ✅ 已完成
- [x] 接入资金流数据（腾讯财经）
- [x] 接入板块数据（新浪财经）
- [x] 修复资金分/板块分始终为50的问题

### Phase 2：功能增强 ✅ 已完成
- [x] 实现量比计算
- [x] 添加缩量上涨识别
- [x] 添加超跌候选识别
- [x] 添加技术指标共振识别
- [x] 添加新低识别
- [ ] 接入基本面数据（Tushare 财务数据）

### Phase 3：高级功能
- [ ] 龙头候选评估算法
- [ ] 多周期趋势综合分析
- [ ] 分时异常识别（需分钟数据）

---

## 五、数据依赖

| 数据源 | 用途 | 优先级 | 备注 |
|-------|-----|-------|-----|
| Tushare daily | 日线数据 + 技术指标 | P0 | ✅ 已接入 |
| Tushare stock_basic | 股票列表 | P0 | ✅ 已接入 |
| 腾讯财经资金流 | 主力/大单/中单/小单净流入 | P0 | ✅ 已接入（2026-08-28） |
| 新浪财经板块 | 板块涨跌幅/热度/龙头股 | P0 | ✅ 已接入（2026-08-28） |
| Tushare 财务 | 基本面数据 | P1 | 待接入 |
| 腾讯/新浪分时 | 分钟数据 | P2 | 待接入 |

---

## 六、API 接口

| 接口 | 方法 | 说明 |
|-----|-----|-----|
| `/api/discovery/types` | GET | 获取发现类型列表 |
| `/api/discovery/run` | POST | 执行发现任务 |
| `/api/discovery/list` | GET | 获取发现结果列表 |
| `/api/discovery/hot` | GET | 获取热门发现（首页用） |

---

## 七、相关文件

| 文件 | 说明 |
|-----|-----|
| `backend/services/discovery_service.py` | 股票发现服务核心逻辑 |
| `backend/api/discovery.py` | Discovery API 接口 |
| `backend/models/discovery.py` | StockDiscovery 数据模型 |
| `backend/collectors/sector_collector.py` | 板块数据采集器（新浪财经） |
| `backend/collectors/capital_flow_collector.py` | 资金流数据采集器（腾讯财经） |
| `backend/collect_sector_capital.py` | 板块和资金流数据采集脚本 |
| `frontend/src/api/discovery.ts` | 前端 API 客户端 |
| `frontend/src/store/discovery.ts` | 前端 Pinia Store |
| `frontend/src/views/discovery/Discovery.vue` | 发现页面 |

---

## 八、每日数据采集计划

### 采集任务总览

| 任务 | 数据源 | 接口/方法 | 采集频率 | 耗时 | 依赖模块 |
|-----|-------|----------|---------|------|---------|
| 股票列表 | Tushare | `stock_basic` | 每周一次 | ~1分钟 | 股票发现 |
| 日线数据 | Tushare | `daily` | 每日收盘后 | ~30分钟 | 技术指标、股票发现 |
| 技术指标 | 本地计算 | `calculator` | 随日线数据 | ~5分钟 | 技术指标、股票发现 |
| 板块数据 | 新浪财经 | `vip.stock.finance.sina.com.cn` | 每日盘中 | ~1分钟 | 股票发现 |
| 资金流数据 | 腾讯财经 | `qt.gtimg.cn` | 每日盘中 | ~5分钟 | 股票发现 |

---

### 详细采集说明

#### 1. 股票列表（每周一次）

**用途**：更新股票基础信息（名称、行业、上市状态等）

**数据源**：Tushare `stock_basic`

**接口**：
```python
pro.stock_basic(
    ts_code='',
    market='',
    status='',
    fields='ts_code,symbol,name,area,industry,market,list_date,is_hs'
)
```

**采集时间**：每周一 09:00

**采集位置**：
- API: `POST /api/data-center/collect/stocks`
- 脚本: `python3 backend/import_real_data.py`

---

#### 2. 日线数据（每日一次）

**用途**：获取股票历史价格、成交量、涨跌幅

**数据源**：Tushare `daily`

**接口**：
```python
pro.daily(ts_code='600000.SH', start_date='20260101', end_date='20260828')
```

**采集时间**：每个交易日 16:00 之后（Tushare收盘后数据更新）

**采集字段**：
| 字段 | 说明 |
|-----|------|
| trade_date | 交易日期 |
| ts_code | 股票代码 |
| open | 开盘价 |
| high | 最高价 |
| low | 最低价 |
| close | 收盘价 |
| vol | 成交量 |
| amount | 成交额 |
| pct_chg | 涨跌幅 |

**采集位置**：
- API: `POST /api/data-center/collect/daily`
- 脚本: `python3 backend/import_real_data.py`

---

#### 3. 技术指标（每日一次）

**用途**：计算 MA、MACD、RSI、KDJ、BOLL 等技术指标

**数据源**：基于日线数据本地计算

**计算指标**：
| 指标 | 周期 | 说明 |
|-----|------|------|
| MA | 5/10/20/30/60/120/250 | 移动平均线 |
| EMA | 12/26 | 指数移动平均 |
| MACD | - | DIF, DEA, MACD柱 |
| RSI | 6/12/24 | 相对强弱指数 |
| BOLL | 20 | 布林带 |
| KDJ | 9 | 随机指标 |

**计算时间**：随日线数据采集后自动计算

**计算位置**：`backend/indicators/calculator.py`

---

#### 4. 板块数据（每日多次）

**用途**：获取行业/概念板块涨跌幅，用于股票发现评分

**数据源**：新浪财经

**接口**：
```
https://vip.stock.finance.sina.com.cn/q/view/newFLJK.php?param=class
```

**返回数据**：
| 字段 | 说明 |
|-----|------|
| code | 板块代码 |
| name | 板块名称 |
| stock_count | 成分股数量 |
| change_pct | 涨跌幅 |
| lead_stock_code | 龙头股代码 |
| lead_stock_name | 龙头股名称 |

**采集时间**：每日 09:30-15:00 每30分钟一次

**采集位置**：
- API: `POST /api/data-center/collect/sectors`
- 脚本: `python3 backend/collect_sector_capital.py`
- 采集器: `backend/collectors/sector_collector.py`

---

#### 5. 资金流数据（每日多次）

**用途**：获取主力/大单/中单/小单净流入，用于股票发现评分

**数据源**：腾讯财经

**接口**：
```
https://qt.gtimg.cn/q=sh600000,sz000001
```

**返回数据**：
| 字段 | 说明 | 单位 |
|-----|------|------|
| main_inflow | 主力净流入 | 元 |
| main_inflow_pct | 主力净流入占比 | % |
| super_large_inflow | 超大单净流入 | 元 |
| large_inflow | 大单净流入 | 元 |
| medium_inflow | 中单净流入 | 元 |
| small_inflow | 小单净流入 | 元 |

**采集时间**：每日 09:30-15:00 每30分钟一次

**采集位置**：
- API: `POST /api/data-center/collect/capital-flow`
- 脚本: `python3 backend/collect_sector_capital.py`
- 采集器: `backend/collectors/capital_flow_collector.py`

---

### 推荐采集流程

#### 交易日采集顺序

```
09:00  - 更新股票列表（如需）
09:30  - 采集板块数据
09:35  - 采集资金流数据
10:00  - 采集板块数据
10:05  - 采集资金流数据
...     - 每30分钟重复
15:00  - 最后一次资金流采集
16:00  - 采集日线数据 + 计算技术指标
16:10  - 采集板块数据（收盘更新）
16:15  - 采集资金流数据（收盘更新）
17:00  - 执行股票发现任务
```

#### 一键采集

```bash
# 一键采集板块+资金流
curl -X POST "http://localhost:8000/api/data-center/collect/all"

# 同步历史数据（如需）
curl -X POST "http://localhost:8000/api/data-center/sync/history?days=90"
```

---

### 数据存储位置

| 数据 | 表名 | 存储位置 |
|-----|------|---------|
| 股票列表 | `stock` | PostgreSQL |
| 日线数据 | `stock_daily` | PostgreSQL + TimescaleDB |
| 技术指标 | `stock_indicator` | PostgreSQL + TimescaleDB |
| 资金流向 | `stock_capital` | PostgreSQL |
| 板块数据 | `sector` | PostgreSQL |
| 股票发现 | `stock_discovery` | PostgreSQL |

---

### 前端操作入口

数据中心页面 (`/data-center`)：

1. **采集股票列表** - 获取全市场股票基本信息
2. **同步历史数据** - 从Tushare拉取历史日线和技术指标
3. **采集板块数据** - 新浪财经行业/概念板块涨跌幅
4. **采集资金流数据** - 腾讯财经个股资金流向
5. **一键采集** - 同时采集板块+资金流
