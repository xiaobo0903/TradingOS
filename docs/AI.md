TradingOS AI智能分析系统设计文档 V1.0

产品名称：TradingOS AI智能分析系统
版本：V1.0
系统定位：AI驱动的股票研究与交易辅助分析平台

1. AI系统建设目标

TradingOS AI不是简单的聊天机器人，而是一个：

基于实时行情数据、技术指标、资金行为、市场情绪和专业投资知识库，通过多Agent协同完成股票分析、风险判断和交易辅助决策的智能分析系统。

核心能力：

实时数据
    |
    |
技术指标计算
    |
    |
资金行为分析
    |
    |
市场环境分析
    |
    |
RAG知识增强
    |
    |
AI Agent推理
    |
    |
智能投资分析报告

2. AI整体架构设计
2.1 总体架构
                     用户

                      |
                      |

              TradingOS AI入口


                      |

                  AI Agent Manager


                      |

 ------------------------------------------------

 |             |              |                |

市场分析Agent 股票分析Agent  主力分析Agent  复盘Agent


 |             |              |                |


 ------------------------------------------------


                      |

              AI Decision Engine


                      |

 ------------------------------------------------

 |                    |                         |

实时行情             技术指标                  知识库

 |                    |                         |

行情数据库        Indicator Engine           RAG Vector DB


                      |

                    LLM


                      |

               AI分析结果

3. AI核心模块设计

TradingOS AI由以下模块组成：

模块	作用
AI Agent管理器	任务调度
股票分析Agent	个股分析
市场Agent	大盘判断
资金Agent	主力行为分析
技术分析Agent	指标解释
情绪Agent	热点分析
复盘Agent	每日总结
RAG知识库	专业知识增强
Prompt管理	分析规则控制
4. AI Agent系统设计
4.1 Agent架构

采用：

Planner

  |

Reasoning

  |

Tool Calling

  |

Answer Generation


例如用户：

贵州茅台现在是否适合买入？

Agent流程：

用户问题

 ↓

股票分析Agent


 ↓

获取数据


 ↓

调用工具


 ↓

读取：

K线

MACD

RSI

BOLL

资金

新闻


 ↓

LLM推理


 ↓

生成报告

5. 股票分析Agent设计
5.1 功能定位

负责：

个股综合分析
买卖机会判断
风险提示
输入数据
基础数据
股票名称

行业

市值

PE

PB

成长性

技术数据
K线

均线

MACD

RSI

BOLL

KDJ

成交量

换手率

量比

资金数据
主力净流入

大单

北向资金

龙虎榜

情绪数据
热点

新闻

政策

市场情绪

5.2 股票分析Prompt设计

系统Prompt：

你是一名专业A股投资分析师。

你的任务：

根据股票实时数据、技术指标、
资金流向、市场环境，
进行客观分析。


要求：

1. 不预测确定涨跌
2. 给出概率判断
3. 分析风险
4. 给出操作策略


分析维度：

一、趋势

二、技术指标

三、资金行为

四、市场情绪

五、风险因素

六、交易计划

6. 技术指标AI分析系统

这是TradingOS核心能力。

传统软件：

显示指标。

TradingOS：

理解指标。

6.1 MACD智能分析

输入：

DIF

DEA

MACD柱

0轴位置

金叉死叉

背离


AI判断：

例如：

MACD:

DIF=0.8

DEA=0.5


DIF上穿DEA

位于0轴上方


AI:

当前处于多头趋势，
短线强度增强。

但需要关注成交量是否同步放大。

6.2 RSI智能分析

输入：

RSI6

RSI12

RSI24


规则：

RSI >80

超买风险


RSI <20

超卖机会


RSI底背离

关注反转


AI输出：

RSI目前72，

虽然处于强势区域，

但接近超买区域，

不建议追高。

6.3 BOLL智能分析

输入：

上轨

中轨

下轨

价格位置

开口状态


分析：

价格突破上轨

+
成交量放大


判断：

强势突破


风险：

短线乖离过大

6.4 KDJ智能分析

分析：

K

D

J

金叉

死叉

超买

超卖

7. 技术形态AI识别

建立：

Pattern Recognition Agent

识别：

买入形态
早晨之星

旭日东升

底部放量

均线金叉

突破箱体

卖出形态
黄昏之星

乌云盖顶

断头铡刀

顶部放量

MACD顶背离


识别流程：

K线数据

 |

Pattern模型

 |

形态标签

 |

AI解释

8. 主力行为AI分析
Main Force Agent

目标：

识别：

吸筹
洗盘
拉升
出货

输入：

成交量

大单

委托盘口

换手率

涨跌幅

资金流


案例：

数据：

上涨5%

成交量放大3倍

大单净流入

换手15%


AI：

判断：

资金主动进入概率较高。

可能处于启动阶段。

关注：

后续量能是否持续。

9. 涨停板AI分析

专门设计：

LimitUp Agent

分析：

一字板
无量涨停

通常代表强烈利好。

放量涨停

分析：

涨停未打开

成交量较大

说明：

存在分歧，

但多方占优势。

炸板分析

判断：

封板次数

打开次数

成交量

位置


分类：

洗盘型

吸筹型

出货型

10. 市场环境Agent

负责：

大盘判断。

输入：

沪指

深成指

创业板

北向资金

美元指数

美股

商品价格

利率

政策


输出：

当前市场：

震荡偏强


风险：

成交量不足


策略：

控制仓位

11. 情绪分析Agent

数据：

涨停数量

跌停数量

连板高度

成交金额

热点板块

新闻


生成：

市场温度。

例如：

市场情绪：

75分


状态：

赚钱效应增强


建议：

积极寻找热点龙头

12. AI每日复盘系统

每天15:30自动运行。

生成：

《每日市场复盘报告》

内容：

一、今日指数表现


二、成交量变化


三、热点板块


四、涨停分析


五、资金流向


六、强势股票


七、风险提示


八、明日关注方向

13. RAG知识库设计
13.1 数据来源

包括：

投资理论
价值投资

技术分析

量价关系

趋势理论

技术指标
MACD

RSI

BOLL

KDJ

均线

实战案例
涨停案例

龙头股案例

顶部案例

洗盘案例

13.2 文档处理流程
PDF

Markdown

网页

股票书籍


 |

文本切割


 |

Embedding


 |

Vector DB


 |

检索


 |

LLM

14. 向量数据库设计

采用：

pgvector

表：

ai_knowledge

字段：

id

title

content

category

embedding

created_time

15. Prompt管理系统

数据库：

ai_prompt

字段：

id

name

version

prompt

model

temperature


支持：

股票分析Prompt
复盘Prompt
K线Prompt
主力Prompt
16. AI模型选择

根据你的本地环境：

24G显存

推荐：

通用分析
Qwen3-14B

Qwen3-32B-GGUF

DeepSeek-R1-Distill-Qwen


部署：

llama.cpp

vLLM

Ollama

17. AI调用流程
用户请求

↓

API

↓

Agent Router

↓

判断任务


↓

调用：

行情工具

指标工具

知识库


↓

LLM推理


↓

生成结果


↓

保存AI报告

18. AI分析结果数据结构

JSON:

{
 "stock":"600519",

 "trend":"上涨",

 "score":86,


 "technical":

 {
 "MACD":"金叉",
 "RSI":"偏高",
 "BOLL":"突破"
 },


 "fund":

 {
 "main":"流入"
 },


 "risk":

 [
 "短线涨幅较大"
 ],


 "suggestion":

 "等待回调"

}

19. AI风险控制原则

必须遵守：

不给确定买卖指令
不承诺收益
提供概率分析
强调风险
20. TradingOS AI最终能力

完成后系统具备：

✅ 自动读取股票数据
✅ 自动分析MACD/RSI/BOLL/KDJ
✅ 自动识别K线形态
✅ 自动分析主力行为
✅ 自动生成股票报告
✅ 自动每日复盘
✅ AI问答股票问题
✅ 根据历史案例辅助判断

21. V1.0开发路线
Phase 1

AI基础：

LLM接入
Prompt系统
股票分析Agent
Phase 2

专业增强：

RAG知识库
指标解释
K线识别
Phase 3

智能化：

多Agent协同
自动选股
自动复盘
Phase 4

高级功能：

策略回测Agent
模拟交易Agent
个性化投资助手
TradingOS AI核心定位
传统股票软件:

告诉你发生了什么


TradingOS:

告诉你为什么发生

并辅助你理解下一步风险