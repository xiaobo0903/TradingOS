"""
股票发现服务

核心逻辑：基于T-1日数据分析，找出处于低位、可能反弹的买入机会股票

信号来源：
- MACD/KDJ金叉（主要信号，权重高）
- K线形态（旭日东升、阳抱阴、早晨之星等，权重高）
- RSI超卖（主要信号）
- 放量/换手率（次要参考，权重较低）
- 价格位置（辅助判断）
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json

import pandas as pd
from sqlalchemy.orm import Session

from models.database import get_db_context
from models.stock import Stock, StockDaily
from models.indicator import StockIndicator
from models.discovery import StockDiscovery
from utils.logging import app_logger
from indicators.kline_patterns import KLinePatternRecognizer


@dataclass
class DiscoveryResult:
    """发现结果"""
    stock_id: int
    stock_code: str
    stock_name: str
    score: float
    reason: str
    conditions: List[str]  # 满足的条件列表
    data_snapshot: dict
    trade_date: date


class DiscoveryService:
    """
    股票发现服务 - 低位买入策略

    基于T-1日数据分析，找出处于低位、可能反弹的买入机会股票

    换手率/量比：仅作为流动性过滤，不是买卖信号
    真正的买入信号：RSI超卖、价格支撑位、MACD/KDJ低位金叉
    """

    # 缺省阈值配置
    DEFAULT_THRESHOLDS = {
        # 流动性指标（仅过滤，非买卖信号）
        'vol_ratio_min': 0.8,        # 最小量比（不能太冷清）
        'vol_ratio_max': 5.0,        # 最大量比（避免异常放量）

        # 趋势指标（仅过滤）
        'max_up_pct': 9.0,          # 涨幅上限（超过可能高位，回避）

        # 买入信号阈值
        'rsi_oversold': 35,         # RSI超卖阈值
        'rsi_overbought': 65,        # RSI超买阈值（回避）
        'boll_distance_pct': 5,       # 距布林下轨距离阈值(%)
        'kdj_oversold': 40,         # KDJ低位阈值
    }

    def __init__(self, thresholds: Dict = None):
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}
        self._capital_cache = None
        self._capital_cache_time = None

    def _get_capital_data(self, stock_codes: List[str]) -> Dict[str, Dict]:
        """获取资金流数据（带缓存）"""
        from datetime import datetime, timedelta

        # 缓存5分钟内的数据
        if self._capital_cache and self._capital_cache_time:
            if (datetime.now() - self._capital_cache_time).seconds < 300:
                return self._capital_cache

        try:
            from collectors.capital_flow_collector import CapitalFlowCollector
            collector = CapitalFlowCollector()

            # 批量获取资金流
            prefix_codes = [f"{'sh' if c.startswith(('6', '5')) else 'sz'}{c}" for c in stock_codes]
            capital_list = collector.collect(stock_codes=prefix_codes)

            # 构建资金流字典 {股票代码: {main_inflow, main_inflow_pct, ...}}
            capital_dict = {}
            for c in capital_list:
                capital_dict[c['stock_code']] = {
                    'main_inflow': c.get('main_inflow', 0),
                    'main_inflow_pct': c.get('main_inflow_pct', 0),
                    'super_large_inflow': c.get('super_large_inflow', 0),
                    'large_inflow': c.get('large_inflow', 0),
                }

            self._capital_cache = capital_dict
            self._capital_cache_time = datetime.now()
            return capital_dict
        except Exception as e:
            app_logger.error(f"获取资金流数据失败: {e}", category="DISCOVERY")
            return {}

    def analyze_stock(self, db: Session, stock: Stock, daily_data: List, indicators: Dict = None) -> Optional[Dict]:
        """
        分析单只股票 - 低位买入策略

        核心逻辑：
        1. MACD/KDJ 是主要买入信号（权重高）
        2. 放量/换手率 是次要参考（权重低）
        3. 价格位置是辅助判断

        Args:
            db: 数据库会话
            stock: 股票对象
            daily_data: 近20日日线数据（已排序，最新在前）
            indicators: 技术指标数据

        Returns:
            分析结果，包含满足的条件和评分
        """
        if not daily_data or len(daily_data) < 5:
            return None

        t = self.thresholds

        # 取T-1日数据（最新一条是昨日）
        yesterday = daily_data[0]
        prev_1 = daily_data[1] if len(daily_data) > 1 else None
        prev_5 = daily_data[1:6] if len(daily_data) > 5 else daily_data[1:]
        prev_20 = daily_data[1:21] if len(daily_data) > 20 else daily_data[1:]

        # ========== 1. 计算各指标 ==========
        current_close = float(yesterday.close or 0)
        change_pct = float(yesterday.change_pct or 0)

        # 计算量比
        vol_ratio = 0
        if len(prev_5) >= 5:
            avg_volume_5 = sum(float(d.volume or 0) for d in prev_5) / 5
            current_volume = float(yesterday.volume or 0)
            vol_ratio = current_volume / avg_volume_5 if avg_volume_5 > 0 else 0

        turnover_rate = float(yesterday.turnover_rate or 0)

        # 获取指标
        dif = indicators.get('dif') if indicators else None
        dea = indicators.get('dea') if indicators else None
        prev_dif = indicators.get('prev_dif') if indicators else None
        kdj_k = indicators.get('kdj_k') if indicators else None
        kdj_d = indicators.get('kdj_d') if indicators else None
        prev_kdj_k = indicators.get('prev_kdj_k') if indicators else None
        rsi6 = indicators.get('rsi6') if indicators else None

        # ========== 2. 主要买入信号：MACD/KDJ（金叉判断） ==========
        primary_conditions = []
        primary_scores = []

        # 2.1 MACD金叉（重要买入信号）
        has_macd_signal = False
        if dif is not None and dea is not None and prev_dif is not None:
            # 金叉：DIF从下方穿越DEA
            if prev_dif <= dea and dif > dea:
                primary_conditions.append("MACD金叉")
                primary_scores.append(35)
                has_macd_signal = True
                # DIF在零轴下方（负值区）金叉，反弹信号更强
                if dif < 0:
                    primary_scores.append(15)
                    primary_conditions.append("MACD零轴下方金叉")
                elif dif < 0.5:
                    primary_scores.append(8)
                    primary_conditions.append("MACD刚转正")

        # 2.2 KDJ金叉（重要买入信号）
        has_kdj_signal = False
        if kdj_k is not None and kdj_d is not None and prev_kdj_k is not None:
            # 金叉：K从下方穿越D
            if prev_kdj_k <= kdj_d and kdj_k > kdj_d:
                primary_conditions.append("KDJ金叉")
                primary_scores.append(30)
                has_kdj_signal = True
                # KDJ低位金叉（K<40），反弹信号更强
                if kdj_k < t['kdj_oversold']:
                    primary_scores.append(15)
                    primary_conditions.append(f"KDJ低位金叉(K={kdj_k:.1f})")
                elif kdj_k < 60:
                    primary_scores.append(5)
                    primary_conditions.append("KDJ中部金叉")

        # 2.3 RSI超卖（买入信号）
        has_rsi_signal = False
        if rsi6 is not None and rsi6 < t['rsi_oversold']:
            primary_conditions.append(f"RSI超卖({rsi6:.1f})")
            primary_scores.append(25)
            has_rsi_signal = True

        # 2.4 MACD底背离（价格止跌回升信号）
        # 条件：价格接近20日最低 + DIF形成上升趋势
        has_macd_divergence = False
        try:
            if len(daily_data) >= 20 and dif is not None:
                current_low = float(yesterday.low or 0)
                current_close = float(yesterday.close or 0)

                # 计算20日最低价和最低收盘价
                lows_20d = [float(d.low or 0) for d in daily_data[:20]]
                lowest_20d = min(lows_20d)
                closes_20d = [float(d.close or 0) for d in daily_data[:20]]

                # 获取历史DIF值
                prev_dif_val = indicators.get('prev_dif') if indicators else None
                prev2_dif_val = indicators.get('prev2_dif') if indicators else None
                prev3_dif_val = indicators.get('prev3_dif') if indicators else None

                # 价格接近20日最低（允许2%误差，找相对低位）
                price_near_low = current_low <= lowest_20d * 1.02

                # 计算DIF的3日变化率
                dif_change_pct = 0
                if prev3_dif_val and prev3_dif_val != 0:
                    dif_change_pct = (dif - prev3_dif_val) / abs(prev3_dif_val)

                # DIF上升趋势检测
                # 条件1：DIF连续3日上升（趋势明确）
                # 条件2：DIF底部抬高 > 15%（从底部反弹）
                # 条件3：DIF由负转正（零轴下方金叉后的延续）
                dif_uptrend = False
                trend_desc = ""

                if prev_dif_val is not None and prev2_dif_val is not None and prev3_dif_val is not None:
                    # 连续3日上升
                    if dif > prev_dif_val and prev_dif_val > prev2_dif_val and prev2_dif_val > prev3_dif_val:
                        dif_uptrend = True
                        trend_desc = "DIF连续3日上升"
                    # 底部抬高（DIF从低点明显回升）
                    elif dif > prev3_dif_val and dif_change_pct > 0.15:
                        dif_uptrend = True
                        trend_desc = f"DIF底部抬高({dif_change_pct*100:.0f}%)"
                elif prev_dif_val is not None:
                    # 只有2日数据，看是否有上升且dif处于低位
                    if dif > prev_dif_val and dif < 0.5:
                        dif_uptrend = True
                        trend_desc = f"DIF上升({((dif-prev_dif_val)/abs(prev_dif_val)*100):.0f}%)" if prev_dif_val != 0 else "DIF上升"

                # MACD底背离：价格相对低位 + DIF上升趋势
                if price_near_low and dif_uptrend:
                    primary_conditions.append(f"MACD底背离({trend_desc})")
                    primary_scores.append(30)
                    has_macd_divergence = True
        except Exception as e:
            app_logger.debug(f"MACD底背离检测失败: {e}", category="DISCOVERY")

        # ========== 2.5 K线形态识别（主要买入信号） ==========
        has_pattern_signal = False
        try:
            # 准备K线数据（最新在前，需要反转）
            kline_df = pd.DataFrame({
                'open': [float(d.open) for d in reversed(daily_data[:10])],
                'high': [float(d.high) for d in reversed(daily_data[:10])],
                'low': [float(d.low) for d in reversed(daily_data[:10])],
                'close': [float(d.close) for d in reversed(daily_data[:10])],
            })

            pattern_recognizer = KLinePatternRecognizer()
            patterns = pattern_recognizer.recognize(kline_df)

            for pattern in patterns:
                if pattern.signal == 'bullish':
                    primary_conditions.append(pattern.name)
                    primary_scores.append(pattern.score)
                    has_pattern_signal = True
                    app_logger.debug(f"识别到K线形态: {pattern.name} for {stock.code}", category="DISCOVERY")
        except Exception as e:
            app_logger.debug(f"K线形态识别失败: {e}", category="DISCOVERY")

        # 如果没有MACD/KDJ/RSI/形态/MACD底背离信号，则不符合条件
        has_primary_signal = has_macd_signal or has_kdj_signal or has_rsi_signal or has_pattern_signal or has_macd_divergence
        if not has_primary_signal:
            return None

        # ========== 3. 次要参考：放量/换手率（权重较低） ==========
        secondary_conditions = []
        secondary_scores = []

        # 3.1 量比参考
        if vol_ratio >= 1.5:
            secondary_conditions.append(f"放量(量比{vol_ratio:.2f})")
            secondary_scores.append(8)
        elif vol_ratio >= 1.2:
            secondary_conditions.append(f"温和放量(量比{vol_ratio:.2f})")
            secondary_scores.append(5)

        # 3.2 换手率参考
        if turnover_rate >= 3.0:
            secondary_conditions.append(f"换手率活跃({turnover_rate:.2f}%)")
            secondary_scores.append(8)
        elif turnover_rate >= 1.0:
            secondary_conditions.append(f"换手率正常({turnover_rate:.2f}%)")
            secondary_scores.append(4)

        # ========== 4. 价格位置辅助判断 ==========
        position_conditions = []
        position_scores = []

        # 4.1 接近20日最低（触底信号）
        if len(prev_20) >= 20:
            low_20d = min(float(d.low or 0) for d in prev_20)
            if low_20d > 0 and current_close <= low_20d * 1.02:
                position_conditions.append(f"接近20日最低({low_20d:.2f})")
                position_scores.append(10)

        # 4.2 低于MA20（相对低位）
        if len(prev_5) >= 5:
            ma20 = sum(float(d.close or 0) for d in daily_data[1:21][:20]) / min(20, len(daily_data) - 1) if len(daily_data) > 1 else 0
            if ma20 > 0 and current_close < ma20:
                distance_pct = (ma20 - current_close) / ma20 * 100
                position_conditions.append(f"低于MA20{distance_pct:.1f}%")
                position_scores.append(8)

        # 4.3 连续下跌（超跌反弹）
        if len(daily_data) >= 4:
            recent_changes = []
            for i in range(min(3, len(daily_data) - 1)):
                prev_close = float(daily_data[i+1].close or 0)
                curr_close = float(daily_data[i].close or 0)
                if prev_close > 0:
                    recent_changes.append((curr_close - prev_close) / prev_close * 100)

            if len(recent_changes) >= 3 and all(c < 0 for c in recent_changes):
                total_drop = sum(recent_changes)
                if total_drop < -5:
                    position_conditions.append(f"连续下跌{total_drop:.1f}%")
                    position_scores.append(12)

        # ========== 5. 综合评分 ==========
        all_conditions = primary_conditions + secondary_conditions + position_conditions
        all_scores = primary_scores + secondary_scores + position_scores

        total_score = sum(all_scores)
        condition_count = len(all_conditions)

        # 信号共振额外加分
        primary_count = len(primary_conditions)
        if primary_count >= 3:
            total_score += 15  # 多个主要信号共振
        elif primary_count == 2:
            total_score += 8   # 两个主要信号
        elif primary_count == 1 and len(secondary_conditions) >= 1:
            total_score += 3   # 一个主要信号+次要确认

        # 限制分数范围
        total_score = max(0, min(100, total_score))

        # 生成原因描述
        if primary_count >= 3:
            reason = f"MACD/KDJ共振，{primary_count}个主要信号"
        elif primary_count == 2:
            reason = f"双主要信号：{primary_conditions[0]} + {primary_conditions[1]}"
        elif primary_count == 1:
            reason = f"主要信号：{primary_conditions[0]}"
        else:
            reason = f"具备{condition_count}个参考信号"

        return {
            'stock_id': stock.id,
            'code': stock.code,
            'name': stock.name,
            'industry': stock.industry,
            'score': round(total_score, 1),
            'conditions': all_conditions,
            'reason': reason,
            'yesterday': {
                'date': str(yesterday.trade_date),
                'close': float(yesterday.close or 0),
                'change_pct': float(yesterday.change_pct or 0),
                'volume': float(yesterday.volume or 0),
                'turnover_rate': float(yesterday.turnover_rate or 0),
                'high': float(yesterday.high or 0),
                'low': float(yesterday.low or 0),
            },
            'indicators': indicators,
            'vol_ratio': vol_ratio,
        }

    def discover(
        self,
        period: str = 'short',
        limit: int = 50,
        min_score: float = 60.0,
        thresholds: Dict = None
    ) -> List[DiscoveryResult]:
        """
        执行股票发现

        Args:
            period: 分析周期 (暂未使用，保留兼容)
            limit: 返回结果数量限制
            min_score: 最低评分阈值
            thresholds: 自定义阈值

        Returns:
            发现结果列表
        """
        if thresholds:
            self.thresholds = {**self.DEFAULT_THRESHOLDS, **thresholds}

        app_logger.info(f"开始股票发现任务: 最低分={min_score}, 限制={limit}", category="DISCOVERY")
        app_logger.info(f"使用阈值: {self.thresholds}", category="DISCOVERY")

        results = []

        try:
            with get_db_context() as db:
                # 获取所有活跃股票
                stocks = db.query(Stock).filter(Stock.status == 'active').all()
                app_logger.info(f"共扫描 {len(stocks)} 只股票", category="DISCOVERY")

                for stock in stocks:
                    # 获取近20日日线数据
                    daily_data = db.query(StockDaily).filter(
                        StockDaily.stock_id == stock.id
                    ).order_by(StockDaily.trade_date.desc()).limit(21).all()

                    if not daily_data or len(daily_data) < 5:
                        continue

                    # 获取最新指标数据（需要多日数据检测趋势和背离）
                    indicators = None
                    indicator_list = db.query(StockIndicator).filter(
                        StockIndicator.stock_id == stock.id
                    ).order_by(StockIndicator.trade_date.desc()).limit(6).all()

                    if indicator_list and len(indicator_list) >= 1:
                        latest = indicator_list[0]
                        prev1 = indicator_list[1] if len(indicator_list) > 1 else None
                        prev2 = indicator_list[2] if len(indicator_list) > 2 else None
                        prev3 = indicator_list[3] if len(indicator_list) > 3 else None

                        indicators = {
                            'ma5': float(latest.ma5) if latest.ma5 else None,
                            'ma10': float(latest.ma10) if latest.ma10 else None,
                            'ma20': float(latest.ma20) if latest.ma20 else None,
                            'ma60': float(latest.ma60) if latest.ma60 else None,
                            'dif': float(latest.dif) if latest.dif else None,
                            'dea': float(latest.dea) if latest.dea else None,
                            'macd': float(latest.macd) if latest.macd else None,
                            'rsi6': float(latest.rsi6) if latest.rsi6 else None,
                            'rsi12': float(latest.rsi12) if latest.rsi12 else None,
                            'kdj_k': float(latest.kdj_k) if latest.kdj_k else None,
                            'kdj_d': float(latest.kdj_d) if latest.kdj_d else None,
                            # 历史数据用于检测趋势和背离
                            'prev_dif': float(prev1.dif) if prev1 and prev1.dif else None,
                            'prev2_dif': float(prev2.dif) if prev2 and prev2.dif else None,
                            'prev3_dif': float(prev3.dif) if prev3 and prev3.dif else None,
                            'prev_kdj_k': float(prev1.kdj_k) if prev1 and prev1.kdj_k else None,
                            'prev_dea': float(prev1.dea) if prev1 and prev1.dea else None,
                            'prev_kdj_d': float(prev1.kdj_d) if prev1 and prev1.kdj_d else None,
                        }

                    # 分析单只股票
                    analysis = self.analyze_stock(db, stock, daily_data, indicators)

                    if analysis and analysis['score'] >= min_score:
                        results.append(DiscoveryResult(
                            stock_id=stock.id,
                            stock_code=stock.code,
                            stock_name=stock.name,
                            score=analysis['score'],
                            reason=analysis['reason'],
                            conditions=analysis['conditions'],
                            data_snapshot={
                                'yesterday': analysis['yesterday'],
                                'indicators': analysis['indicators'],
                                'vol_ratio': analysis['vol_ratio'],
                            },
                            trade_date=date.today(),
                        ))

        except Exception as e:
            app_logger.error(f"股票发现执行失败: {e}", category="DISCOVERY")
            raise

        # 按评分排序
        results.sort(key=lambda x: x.score, reverse=True)

        # 限制返回数量
        final_results = results[:limit]
        app_logger.info(f"股票发现完成，找到 {len(final_results)} 只候选股票", category="DISCOVERY")

        return final_results

    def save_discoveries(self, discoveries: List[DiscoveryResult], discovery_type: str = 'buy_signal') -> int:
        """
        保存发现结果到数据库
        """
        saved_count = 0

        with get_db_context() as db:
            for d in discoveries:
                # 检查是否已存在今日该类型的发现记录
                existing = db.query(StockDiscovery).filter(
                    StockDiscovery.stock_id == d.stock_id,
                    StockDiscovery.discovery_type == discovery_type,
                    StockDiscovery.trade_date == d.trade_date,
                ).first()

                if existing:
                    existing.score = d.score
                    existing.reason = d.reason
                    existing.data_snapshot = json.dumps({
                        'conditions': d.conditions,
                        **d.data_snapshot
                    })
                else:
                    discovery = StockDiscovery(
                        stock_id=d.stock_id,
                        discovery_type=discovery_type,
                        score=d.score,
                        reason=d.reason,
                        data_snapshot=json.dumps({
                            'conditions': d.conditions,
                            **d.data_snapshot
                        }),
                        trade_date=d.trade_date,
                    )
                    db.add(discovery)

                saved_count += 1

            db.commit()

        return saved_count

    def get_discoveries(
        self,
        discovery_type: str = 'buy_signal',
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        获取已保存的发现记录
        """
        with get_db_context() as db:
            query = db.query(StockDiscovery).join(
                Stock, StockDiscovery.stock_id == Stock.id
            )

            if discovery_type:
                query = query.filter(StockDiscovery.discovery_type == discovery_type)

            # 获取最近3天的发现记录
            three_days_ago = date.today() - timedelta(days=3)
            query = query.filter(StockDiscovery.trade_date >= three_days_ago)

            discoveries = query.order_by(
                StockDiscovery.score.desc()
            ).offset(offset).limit(limit).all()

            results = []
            for d in discoveries:
                snapshot = json.loads(d.data_snapshot) if d.data_snapshot else {}

                # 获取股票所属板块（优先从sectors关系获取，否则用sector字段，再否则用industry）
                sectors = []
                if d.stock.sectors:
                    sectors = [s.name for s in d.stock.sectors]
                elif d.stock.sector:
                    sectors = [d.stock.sector]
                elif d.stock.industry:
                    sectors = [d.stock.industry]

                result = {
                    'id': d.id,
                    'stock_id': d.stock_id,
                    'code': d.stock.code,
                    'name': d.stock.name,
                    'industry': d.stock.industry,
                    'sectors': sectors,
                    'score': float(d.score),
                    'reason': d.reason,
                    'conditions': snapshot.get('conditions', []),
                    'trade_date': d.trade_date.isoformat() if d.trade_date else None,
                    'yesterday': snapshot.get('yesterday', {}),
                    'indicators': snapshot.get('indicators', {}),
                }
                results.append(result)

            return results


# 全局单例
_discovery_service: Optional[DiscoveryService] = None


def get_discovery_service(thresholds: Dict = None) -> DiscoveryService:
    """获取发现服务单例"""
    global _discovery_service
    if _discovery_service is None:
        _discovery_service = DiscoveryService(thresholds)
    return _discovery_service
