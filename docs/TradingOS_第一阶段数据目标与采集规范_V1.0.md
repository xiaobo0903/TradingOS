# TradingOS 第一阶段数据目标与采集规范 V1.0

> **定位**：TradingOS 第一阶段数据建设的统一实施文档。  
> **目标**：建立“股票发现、初步筛选、技术分析、后续 AI 分析”所需要的稳定、完整、可追溯的数据基础。  
> **技术栈**：Vue 3 + Python/FastAPI。  
> **阶段边界**：暂不做自动交易，不以量化交易为核心。

---

## 1. 第一阶段建设目标

TradingOS 的核心不是重新制作一个传统行情软件，而是建立：

```text
全市场数据
    ↓
股票基础池
    ↓
行情数据
    ↓
指标计算
    ↓
股票发现 / 筛选
    ↓
股票分析
    ↓
后续 AI 分析
```

第一阶段重点不是“采集所有数据”，而是先建立可靠的数据底座。

必须达到：

1. A 股股票基础池完整；
2. 日线历史数据完整；
3. 1 分钟数据能够稳定获取；
4. 实时行情能够接入（数据源支持时）；
5. 成交量、成交额、换手率等核心行情字段完整；
6. 能够计算 MA / EMA / MACD / RSI / BOLL / KDJ；
7. 能够检测缺失、重复、断档、异常和延迟；
8. 为第二阶段股票发现和筛选提供标准数据。

---

# 2. 第一阶段必须获取的数据

## 2.1 股票基础资料

这是系统的股票主数据，属于低频数据。

### 必须字段

| 字段 | 说明 |
|---|---|
| stock_code | 股票代码 |
| stock_name | 股票名称 |
| exchange | SH / SZ / BJ |
| market | 沪市 / 深市 / 北交所 |
| security_type | 证券类型 |
| list_date | 上市日期 |
| delist_date | 退市日期，可为空 |
| status | 正常 / ST / *ST / 停牌 / 退市等 |
| is_st | 是否 ST |
| is_delisted | 是否退市 |
| total_shares | 总股本 |
| float_shares | 流通股本 |
| updated_at | 更新时间 |

后续可增加：

- 行业分类
- 概念分类
- 地域分类
- 主板 / 创业板 / 科创板 / 北交所
- 股票简称历史变化

---

# 3. 日线行情

日线是第一阶段最重要的历史行情数据之一。

## 3.1 必须字段

```text
stock_code
trade_date
open
high
low
close
pre_close
change
change_pct
volume
amount
```

建议增加：

```text
turnover_rate
amplitude
total_market_cap
float_market_cap
source
```

### 字段含义

- `open`：开盘价
- `high`：最高价
- `low`：最低价
- `close`：收盘价
- `pre_close`：前收盘价
- `change`：涨跌额
- `change_pct`：涨跌幅
- `volume`：成交量
- `amount`：成交额
- `turnover_rate`：换手率
- `amplitude`：振幅

---

# 4. 日线历史范围

建议：

```text
最低：2 年
推荐：5 年
理想：10 年
```

原因：

- 技术指标需要连续历史数据；
- 股票发现需要判断趋势；
- 后续 AI 需要历史上下文；
- 可以判断当前行情处于历史趋势的什么阶段。

**原则：保存原始行情，不只保存计算后的指标。**

---

# 5. 分钟行情

分钟数据主要服务：

- 分时分析；
- 短线分析；
- 量比；
- 盘中放量；
- 盘中回调；
- 盘中异动；
- 涨停分析；
- 后续实时 AI 分析。

## 5.1 第一阶段推荐

优先：

```text
1 分钟
5 分钟
```

其中：

### 1 分钟

作为核心原始分钟数据。

用于：

```text
分时走势
实时成交量
盘中放量
盘中回调
量比
短线异动
```

### 5 分钟

原则上可以由 1 分钟聚合得到：

```text
1分钟 → 5分钟
```

不一定需要再次向数据源付费获取。

---

# 6. 分钟数据字段

```text
stock_code
trade_datetime
open
high
low
close
volume
amount
```

建议增加：

```text
pre_close
change
change_pct
turnover_rate
source
fetch_time
```

`trade_datetime` 必须精确到分钟。

---

# 7. 实时行情

如果数据源支持实时行情，建立统一实时行情模型。

核心：

```text
stock_code
timestamp
price
pre_close
open
high
low
volume
amount
change
change_pct
```

如果数据源支持五档盘口，再增加：

```text
bid1_price
bid1_volume
...
bid5_price
bid5_volume

ask1_price
ask1_volume
...
ask5_price
ask5_volume
```

实时行情和历史分钟行情应分开设计。

推荐：

```text
行情接入层
    ↓
标准行情模型
    ↓
Redis
    ↓
WebSocket
    ↓
Vue3
```

历史数据进入 PostgreSQL / TimescaleDB。

---

# 8. 成交量与成交额

第一阶段必须保存：

```text
volume
amount
```

后续用于计算：

- 成交量变化率；
- 量价关系；
- 放量；
- 缩量；
- 量价背离；
- 成交量均值；
- 成交量异常。

---

# 9. 换手率

如果数据源能够提供，第一阶段直接保存：

```text
turnover_rate
```

用于：

- 股票活跃度；
- 强势股发现；
- 高换手股票发现；
- 放量分析；
- 涨停分析。

---

# 10. 量比

量比是非常重要的盘中指标。

如果数据源直接提供，可以保存：

```text
volume_ratio
```

否则由系统自行计算。

建议保存：

```text
当前量比
5日同期量比基准
10日同期量比基准
```

主要用于：

- 盘中放量；
- 异动发现；
- 股票发现；
- 强势股筛选。

---

# 11. 技术指标

第一阶段必须由程序计算，**不要让 LLM 自己计算指标**。

数据链：

```text
原始行情
   ↓
Indicator Engine
   ↓
技术指标
   ↓
Analysis Engine
   ↓
AI
```

---

# 12. MA 移动平均线

至少：

```text
MA5
MA10
MA20
MA30
MA60
MA120
MA250
```

用于：

- 短期趋势；
- 中期趋势；
- 长期趋势；
- 多头排列；
- 空头排列；
- 金叉；
- 死叉；
- 支撑 / 压力；
- 股票筛选。

---

# 13. EMA

至少：

```text
EMA5
EMA10
EMA12
EMA20
EMA26
EMA60
```

其中：

```text
EMA12
EMA26
```

直接服务 MACD。

---

# 14. MACD

至少保存：

```text
DIF
DEA
MACD_HIST
```

建议同时保存：

```text
EMA12
EMA26
```

重点分析：

### 趋势

```text
DIF > 0
DEA > 0
```

### 金叉

```text
DIF 上穿 DEA
```

### 死叉

```text
DIF 下穿 DEA
```

### 0 轴

记录：

```text
DIF 与 0 轴关系
DEA 与 0 轴关系
```

### 柱状图

分析：

```text
红柱扩大
红柱缩短
绿柱扩大
绿柱缩短
```

---

# 15. RSI

第一阶段：

```text
RSI6
RSI12
RSI24
```

主要用于：

- 超买；
- 超卖；
- 强弱；
- RSI 金叉；
- RSI 死叉；
- RSI 背离。

**不能简单把 RSI > 80 或 RSI < 20 当成绝对买卖规则，应作为综合分析因素。**

---

# 16. BOLL

至少：

```text
BOLL_UPPER
BOLL_MIDDLE
BOLL_LOWER
```

建议：

```text
BOLL_WIDTH
BOLL_POSITION
```

用于分析：

- 开口；
- 收口；
- 紧口；
- 波动率变化；
- 价格与上轨关系；
- 价格与中轨关系；
- 价格与下轨关系。

---

# 17. KDJ

第一阶段：

```text
K
D
J
```

推荐周期：

```text
9, 3, 3
```

用于：

- 超买；
- 超卖；
- 金叉；
- 死叉；
- 50 轴；
- 与 MACD 综合分析。

---

# 18. 不只保存指标数值

TradingOS 不应该只保存：

```text
MACD = 0.25
RSI = 67
```

还要生成结构化技术状态。

例如：

```json
{
  "macd": {
    "dif": 0.25,
    "dea": 0.18,
    "hist": 0.07,
    "trend": "bullish",
    "cross": "golden_cross",
    "zero_axis": "above"
  }
}
```

推荐建立统一：

```text
TechnicalSnapshot
```

这样股票发现、筛选和 AI 都可以直接使用。

---

# 19. 数据质量管理

第一阶段必须具备：

```text
缺失检测
重复检测
时间断档检测
异常值检测
数据延迟检测
数据源异常检测
```

每条数据建议记录：

```text
source
data_time
fetch_time
status
version
```

---

# 20. 分钟数据缺失

例如：

```text
09:35
09:36
09:37
09:38
09:39
```

如果：

```text
09:36
09:37
09:38
```

缺失，则产生：

```text
DataMissingEvent
```

例如：

```json
{
  "stock_code": "600xxx",
  "data_type": "1min",
  "start_time": "09:36",
  "end_time": "09:38",
  "status": "missing",
  "source": "source_a"
}
```

---

# 21. 数据补采

第一阶段必须支持：

```text
自动补采
手动补采
失败重试
切换数据源
忽略
```

页面可以显示：

```text
数据异常

股票：600xxx
数据类型：1分钟

缺失：
09:36 ～ 09:38

原因：
数据源返回异常

[立即补采]
[切换数据源]
[忽略]
```

---

# 22. 多数据源

业务系统不能绑定某一家数据接口。

架构：

```text
DataSource A
DataSource B
DataSource C
       ↓
Collector
       ↓
Normalizer
       ↓
Validator
       ↓
Storage
```

统一输出：

```text
NormalizedMarketData
```

业务层只使用统一模型。

---

# 23. 采集频率

| 数据 | 建议频率 |
|---|---|
| 股票基础资料 | 每日 / 低频 |
| 日线 | 每个交易日收盘后 |
| 1分钟 | 交易时间高频 |
| 5分钟 | 由1分钟聚合 |
| 实时行情 | 高实时性 |
| 技术指标 | 行情更新后计算 |
| 数据质量检查 | 持续 |
| 历史补采 | 按任务执行 |

---

# 24. 推荐数据库结构

```text
stock_master
daily_quotes
minute_quotes
realtime_quotes
technical_indicators
data_quality_records
data_fetch_tasks
```

Redis：

```text
realtime:stock:{code}
realtime:market
realtime:sector
```

---

# 25. stock_master

```text
id
stock_code
stock_name
exchange
market
security_type
list_date
delist_date
status
is_st
is_delisted
total_shares
float_shares
created_at
updated_at
```

---

# 26. daily_quotes

```text
id
stock_code
trade_date
open
high
low
close
pre_close
change
change_pct
volume
amount
turnover_rate
amplitude
total_market_cap
float_market_cap
source
created_at
```

唯一约束：

```text
(stock_code, trade_date)
```

---

# 27. minute_quotes

```text
id
stock_code
trade_datetime
open
high
low
close
volume
amount
change
change_pct
source
fetch_time
```

唯一约束：

```text
(stock_code, trade_datetime)
```

---

# 28. technical_indicators

```text
stock_code
data_time
period

ma5
ma10
ma20
ma30
ma60
ma120
ma250

ema5
ema10
ema12
ema20
ema26
ema60

dif
dea
macd_hist

rsi6
rsi12
rsi24

boll_upper
boll_middle
boll_lower
boll_width

k
d
j

created_at
```

---

# 29. 第一阶段暂时不必强制采集的数据

以下数据价值很高，但可以放到后续：

```text
Level-2
逐笔盘口
龙虎榜
细分主力资金
新闻全文
公告全文
研报
舆情
股票人气
概念热度
扩展资金数据
```

第一阶段不要因为这些数据阻塞整个系统建设。

---

# 30. 第一阶段完成后的能力

系统至少应该能够：

### 查看股票

```text
股票代码
股票名称
最新价格
涨跌幅
成交量
成交额
换手率
量比
```

### 查看历史走势

```text
日K
周K
月K
```

### 查看分钟走势

```text
1分钟
5分钟
```

### 查看技术指标

```text
MA
EMA
MACD
RSI
BOLL
KDJ
```

### 判断基本技术状态

```text
上涨
下跌
震荡
趋势转换
```

### 判断数据质量

```text
正常
延迟
缺失
异常
```

---

# 31. 为股票发现提供的数据

第一阶段完成后，应直接支持第二阶段：

```text
涨幅
成交量
成交额
换手率
量比
MA
EMA
MACD
RSI
BOLL
KDJ
```

进一步形成：

```text
趋势
+
量价
+
技术指标
+
活跃度
```

再进入：

```text
股票发现
```

---

# 32. AI 接口预留

虽然 AI 可以后置，但第一阶段的数据结构必须能够支持 AI。

LLM 不负责：

```text
计算 MA
计算 MACD
计算 RSI
计算 BOLL
计算 KDJ
判断数据是否缺失
```

这些必须由程序完成。

LLM 负责：

```text
解释
总结
对比
发现多维数据关系
生成分析报告
风险提示
回答用户问题
```

推荐：

```text
原始数据
    ↓
指标计算
    ↓
结构化技术数据
    ↓
规则分析
    ↓
LLM
    ↓
自然语言分析
```

---

# 33. 第一阶段最终数据流

```text
                 ┌──────────────┐
                 │  数据源 A     │
                 └──────┬───────┘
                        │
                 ┌──────▼───────┐
                 │  数据源 B     │
                 └──────┬───────┘
                        │
                 ┌──────▼───────┐
                 │   Collector   │
                 └──────┬───────┘
                        ↓
                 ┌───────────────┐
                 │  Normalizer   │
                 └──────┬────────┘
                        ↓
                 ┌───────────────┐
                 │   Validator   │
                 └──────┬────────┘
                        ↓
             ┌──────────┴──────────┐
             ↓                     ↓
      PostgreSQL/TimescaleDB      Redis
             ↓                     ↓
      Indicator Engine          WebSocket
             ↓                     ↓
      TechnicalSnapshot           Vue3
             ↓
      股票发现 / 股票筛选
             ↓
      股票深度分析
             ↓
          后续 AI
```

---

# 34. 第一阶段验收清单

## 股票基础数据

- [ ] A股股票池完整
- [ ] 股票代码唯一
- [ ] 股票名称完整
- [ ] 交易所信息完整
- [ ] 上市状态正确
- [ ] ST 状态可识别

## 日线

- [ ] 历史日线完整
- [ ] OHLC 完整
- [ ] 成交量完整
- [ ] 成交额完整
- [ ] 交易日期无异常断档

## 分钟

- [ ] 1分钟可以稳定获取
- [ ] 交易时间连续
- [ ] 缺失可以检测
- [ ] 缺失可以补采
- [ ] 5分钟可以聚合

## 指标

- [ ] MA
- [ ] EMA
- [ ] MACD
- [ ] RSI
- [ ] BOLL
- [ ] KDJ

全部可以由程序自动计算。

## 数据质量

- [ ] 重复检测
- [ ] 缺失检测
- [ ] 时间断档检测
- [ ] 异常值检测
- [ ] 数据源状态检测
- [ ] 延迟检测

## 数据架构

- [ ] 数据源与业务解耦
- [ ] 支持增加数据源
- [ ] 数据统一标准化
- [ ] 支持定时任务
- [ ] 支持失败重试
- [ ] 支持手动补采

---

# 35. 第一阶段核心原则

### 原则一：数据先于 AI

没有可靠的数据，AI 分析没有意义。

### 原则二：计算先于语言模型

指标必须由程序计算，LLM 只负责理解和解释。

### 原则三：原始数据必须保留

不要只保存最终指标。

### 原则四：多周期

至少同时支持：

```text
1分钟
5分钟
日线
周线
月线
```

### 原则五：数据质量优先

缺失、重复、断档和异常必须能够被发现。

### 原则六：数据源解耦

未来更换数据源不能影响业务层。

### 原则七：第一阶段不要过度建设

先完成：

```text
股票基础数据
+
日线
+
1分钟
+
实时行情
+
成交量
+
换手率
+
量比
+
MA / EMA
+
MACD
+
RSI
+
BOLL
+
KDJ
+
数据质量
```

形成稳定的数据底座，再进入股票发现和筛选。

---

# 36. 最终目标

第一阶段不是为了把 TradingOS 做成一个“数据仓库”。

而是为了建立一个能够真正支持下面闭环的数据基础：

```text
全市场
   ↓
发现股票
   ↓
筛选股票
   ↓
技术分析
   ↓
判断趋势
   ↓
加入关注
   ↓
持续跟踪
   ↓
数据发生变化
   ↓
重新分析
   ↓
后续 AI 辅助解释
```

**第一阶段完成的标志：不是“采集了多少数据”，而是这些数据已经可以可靠地支撑 TradingOS 的股票发现与分析。**
