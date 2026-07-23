TradingOS 数据库设计文档 V1.0

产品：TradingOS 智能股票分析系统
数据库版本：V1.0
数据库选型：PostgreSQL + TimescaleDB（时序数据扩展）+ Redis（实时缓存）
后端：Python FastAPI
前端：Vue3

1. 数据库整体架构设计

TradingOS的数据特点：

股票基础信息（低频）
日线历史数据（长期）
分钟级行情（高频）
实时盘口数据（超高频）
技术指标数据（计算型）
AI分析结果（文本型）

因此采用：

                 TradingOS Database


                       |
        --------------------------------

        PostgreSQL业务数据库

        - 用户
        - 股票信息
        - 策略
        - 自选股
        - 交易记录


        TimescaleDB时序数据库

        - 分钟行情
        - Tick数据
        - 成交明细
        - 资金流


        Redis缓存

        - 实时行情
        - 热点股票
        - 排名数据


        AI数据库

        - 知识库
        - 分析报告
        - 向量数据

2. 数据库Schema规划

建议分Schema管理：

tradingos

├── base
│
├── market
│
├── indicator
│
├── fund
│
├── strategy
│
├── ai
│
├── user
│
└── system

3. 基础数据表（base）
3.1 股票基本信息表
stock_info

用途：

保存所有A股股票基础资料。

字段	类型	说明
id	bigserial	主键
symbol	varchar(10)	股票代码
name	varchar(50)	股票名称
exchange	varchar(10)	交易所
industry	varchar(50)	行业
sector	varchar(50)	板块
market_cap	decimal	市值
float_cap	decimal	流通市值
listing_date	date	上市日期
status	varchar	状态

示例：

600519
贵州茅台
SH
白酒
消费
3.2 股票分类表
stock_category

用于：

热点
概念
行业

字段：

id

category_name

category_type

description


例如：

人工智能
新能源
半导体
机器人

4. 行情数据表（market）

这是系统核心。

4.1 日K数据表
stock_daily_k

TimescaleDB hypertable

字段：

字段	类型
id	bigserial
symbol	varchar
trade_date	date
open	decimal
high	decimal
low	decimal
close	decimal
volume	bigint
amount	decimal
turnover	decimal

索引：

(symbol,trade_date)

4.2 分钟K线
stock_minute_k

支持：

1分钟

5分钟

15分钟

30分钟

字段：

id

symbol

timestamp

period


open

high

low

close


volume

amount


示例：

600519

2026-07-22 09:35

5min

4.3 Tick成交数据
stock_tick

用途：

盘口分析。

字段：

id

symbol

timestamp

price

volume

amount

direction



direction:

BUY
SELL
UNKNOWN

4.4 五档盘口
stock_order_book

保存：

买卖五档。

字段：

id

symbol

timestamp


bid_price1

bid_volume1


...

ask_price5

ask_volume5

5. 成交分析数据库
5.1 成交明细
transaction_detail

字段：

id

symbol

time

price

volume

amount


direction


large_order


direction:

主动买

主动卖

5.2 大单数据
large_order

用于：

主力分析。

字段：

id

symbol

time


price

volume

amount


level



level:

100万+

500万+

1000万+

6. 资金数据模块
6.1 股票资金流向
stock_money_flow

字段：

id

symbol

trade_date


main_inflow

main_outflow

net_inflow


super_large

large

medium

small

6.2 北向资金
north_money

字段：

date

sh_connect

sz_connect

total

7. 技术指标数据库

原则：

不要每次重新计算。

保存结果。

7.1 技术指标表
technical_indicator

字段：

id

symbol

trade_date


ma5

ma10

ma20

ma60


ema12

ema26


dif

dea

macd


rsi


boll_upper

boll_mid

boll_lower


kdj_k

kdj_d

kdj_j

7.2 技术信号表
technical_signal

保存：

买卖信号。

字段：

id

symbol

date


signal_type


confidence


description


signal_type:

MACD金叉

RSI超卖

BOLL突破

均线多头


例如：

600519

MACD金叉

85%

短线趋势转强

8. K线形态数据库
candle_pattern

保存：

AI识别结果。

字段：

id

symbol

date


pattern_name


position


score


description


例如：

早晨之星

底部

82

反转概率较高

9. 主力行为分析
9.1 主力行为表
main_force_behavior

字段：

id

symbol

date


behavior


score


reason


behavior:

吸筹

洗盘

拉升

出货

对敲

10. 股票评分系统
stock_score

用于智能选股。

字段：

id

symbol

date


technical_score

fund_score

emotion_score

hot_score


total_score


rank


例如：

贵州茅台

92分

A+

11. 热点数据
market_hotspot

字段：

id

date


sector


rise_percent


money_inflow


stock_count


12. 新闻数据
news

字段：

id

title

content


source


publish_time


related_stock


sentiment



sentiment:

利好

利空

中性

13. AI分析数据库
13.1 AI股票分析报告
ai_stock_report

字段：

id


symbol


date


trend


score


analysis


risk


suggestion


model



保存：

LLM生成结果。

示例：
{
"trend":"上涨",

"score":85,

"risk":"RSI过高",

"suggestion":"等待回调"
}

13.2 AI对话记录
ai_chat

字段：

id

user_id

question

answer

create_time

14. RAG知识库
knowledge_document

保存：

股票知识。

字段：

id

title

category


content


source


例如：

MACD指标使用方法

K线形态

量价关系

knowledge_vector

向量数据库：

推荐：

Milvus / pgvector

字段：

id

document_id

embedding

15. 用户系统
用户表
user
id

username

password

email

role

create_time

自选股
favorite_stock

字段：

id

user_id

symbol

group_name

remark

交易记录
trade_record

字段：

id

user_id

symbol


buy_price

sell_price


volume


profit


reason

16. 策略系统
trading_strategy

字段：

id

name

description


conditions



例如：

{
"MACD":"金叉",

"RSI":"<30",

"volume":"放量"
}

17. 系统监控
data_source

数据接口管理。

字段：

id

name

url

status

last_update

data_error

数据异常。

字段：

id

source

error

time

status


支持：

人工修复。

18. Redis缓存设计

实时数据：

stock:600519:latest


market:index


hot:list


rank:strong_stock


19. 数据更新任务

使用：

Celery + Redis

任务：

任务	频率
实时行情	5秒
分钟K线	1分钟
资金流	5分钟
技术指标	收盘后
AI报告	每日
20. 数据流设计
行情接口

 ↓

采集服务

 ↓

Kafka

 ↓

TimescaleDB


 ↓

指标计算服务

 ↓

AI分析服务


 ↓

Vue3展示

21. TradingOS数据库核心关系
stock_info

    |

    |

stock_daily_k

    |

technical_indicator

    |

technical_signal

    |

ai_stock_report


22. V1.0数据库重点实现

第一阶段必须完成：

✅ 股票基础数据
✅ 日K数据
✅ 分钟行情
✅ 成交量数据
✅ 技术指标计算
✅ AI分析结果
✅ 自选股管理
✅ 数据监控

这个数据库设计可以直接支撑后续：

Vue3 TradingOS前端开发
Python FastAPI后端
量化分析引擎
LLM + RAG智能分析
实时行情系统