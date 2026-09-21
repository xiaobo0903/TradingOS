"""
K线形态识别

识别经典K线形态，用于判断涨跌信号
"""
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import pandas as pd


@dataclass
class KLinePattern:
    """K线形态"""
    name: str           # 形态名称
    signal: str         # 信号：bullish/bearish/neutral
    score: int          # 评分权重
    description: str    # 描述


class KLinePatternRecognizer:
    """
    K线形态识别器

    支持的形态：
    - 旭日东升：强烈看涨反转
    - 阳抱阴：看涨吞噬
    - 上涨插线（孕育线）：看涨待变
    - 向上跳空：跳空高开
    - 红三兵：三连阳
    - 早晨之星：三日反转形态
    - 上升三法：上升整理形态
    """

    # 形态定义及权重
    PATTERNS = {
        'xuri_dongsheng': KLinePattern('旭日东升', 'bullish', 35, '强烈看涨反转'),
        'yang_bao_yin': KLinePattern('阳抱阴', 'bullish', 30, '看涨吞噬'),
        'shangzhang_chaxian': KLinePattern('上涨插线', 'bullish', 25, '看涨孕育'),
        'xiangshang_tiaokong': KLinePattern('向上跳空', 'bullish', 28, '跳空高开'),
        'hong san bing': KLinePattern('红三兵', 'bullish', 32, '三连阳强势'),
        'zaochen_star': KLinePattern('早晨之星', 'bullish', 35, '重要反转信号'),
        'shangsheng_sanfa': KLinePattern('上升三法', 'bullish', 28, '上升整理形态'),
    }

    def __init__(self):
        pass

    def recognize(self, df: pd.DataFrame, include_other: bool = True) -> List[KLinePattern]:
        """
        识别K线形态

        Args:
            df: 包含OHLC数据的DataFrame，需包含 open, high, low, close 列
            include_other: 是否识别其他辅助形态

        Returns:
            识别出的形态列表
        """
        if len(df) < 3:
            return []

        patterns = []

        # 确保数据格式正确
        if not all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            return []

        # 转为numpy数组便于计算
        opens = df['open'].values
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values

        n = len(df)

        # 1. 旭日东升：连续下跌后，出现一根大阴线，然后出现一根大阳线收复
        # 识别：连续3天下跌，最后一天收盘价 > 前两天开盘价
        if self._check_xuri_dongsheng(opens, highs, lows, closes):
            patterns.append(self.PATTERNS['xuri_dongsheng'])

        # 2. 阳抱阴（看涨吞噬）：今日阳线实体完全包裹昨日阴线实体
        if n >= 2 and self._check_yang_bao_yin(opens, closes):
            patterns.append(self.PATTERNS['yang_bao_yin'])

        # 3. 上涨插线（孕育线）：今日K线实体在昨日K线实体之内
        if n >= 2 and self._check_shangzhang_chaxian(opens, closes):
            patterns.append(self.PATTERNS['shangzhang_chaxian'])

        # 4. 向上跳空：今日最低价 > 昨日最高价
        if n >= 2 and self._check_xiangshang_tiaokong(lows, highs):
            patterns.append(self.PATTERNS['xiangshang_tiaokong'])

        # 5. 红三兵：连续三根阳线，逐日走高
        if n >= 3 and self._check_hong_san_bing(opens, closes, highs):
            patterns.append(self.PATTERNS['hong san bing'])

        # 6. 早晨之星：三根K线组合，第一天下跌，第二天十字星，第三天上涨
        if n >= 3 and self._check_zaochen_star(opens, closes, highs, lows):
            patterns.append(self.PATTERNS['zaochen_star'])

        # 7. 上升三法：上涨后小幅回调但不破第一根阳线实体
        if n >= 5 and self._check_shangsheng_sanfa(opens, closes):
            patterns.append(self.PATTERNS['shangsheng_sanfa'])

        return patterns

    def _is_bullish_candle(self, open_price: float, close_price: float) -> bool:
        """判断是否阳线（收盘价 > 开盘价）"""
        return close_price > open_price

    def _is_bearish_candle(self, open_price: float, close_price: float) -> bool:
        """判断是否阴线（收盘价 < 开盘价）"""
        return close_price < open_price

    def _body_size(self, open_price: float, close_price: float) -> float:
        """计算实体大小"""
        return abs(close_price - open_price)

    def _is_gap_up(self, today_low: float, yesterday_high: float, threshold: float = 0.01) -> bool:
        """判断是否向上跳空（今日最低价 > 昨日最高价）"""
        if yesterday_high <= 0:
            return False
        return today_low > yesterday_high * (1 + threshold)

    def _check_xuri_dongsheng(self, opens, highs, lows, closes) -> bool:
        """
        旭日东升：
        连续下跌后，出现一根大阴线，然后出现一根大阳线，收盘价高于前一根阴线开盘价
        """
        if len(opens) < 4:
            return False

        # 最近3天连续下跌
        down_days = 0
        for i in range(2, -1, -1):
            if closes[i] < closes[i + 1] if i + 1 < len(closes) else False:
                down_days += 1

        if down_days < 2:
            return False

        # 今日是阳线，收盘价 > 前两天阴线开盘价
        if not self._is_bullish_candle(opens[0], closes[0]):
            return False

        # 阳线实体应该较大
        if self._body_size(opens[0], closes[0]) < self._body_size(opens[1], closes[1]) * 0.8:
            return False

        # 收盘价高于前一根阴线开盘价
        return closes[0] > opens[1]

    def _check_yang_bao_yin(self, opens, closes) -> bool:
        """
        阳抱阴（看涨吞噬）：
        今日阳线实体完全包裹昨日阴线实体
        """
        today_open, today_close = opens[0], closes[0]
        yesterday_open, yesterday_close = opens[1], closes[1]

        # 昨日是阴线
        if not self._is_bearish_candle(yesterday_open, yesterday_close):
            return False

        # 今日是阳线
        if not self._is_bullish_candle(today_open, today_close):
            return False

        # 阳线实体包裹阴线实体
        return today_open < yesterday_open and today_close > yesterday_close

    def _check_shangzhang_chaxian(self, opens, closes) -> bool:
        """
        上涨插线（孕育线/待变线）：
        今日K线实体在昨日K线实体之内（阳线孕育在阴线内）
        """
        if len(opens) < 2:
            return False

        today_open, today_close = opens[0], closes[0]
        yesterday_open, yesterday_close = opens[1], closes[1]

        # 昨日阴线，今日阳线
        if not (self._is_bearish_candle(yesterday_open, yesterday_close) and
                self._is_bullish_candle(today_open, today_close)):
            return False

        # 今日实体在昨日实体范围内
        return (today_open > yesterday_close and today_close < yesterday_open) or \
               (today_open >= yesterday_open and today_close <= yesterday_close)

    def _check_xiangshang_tiaokong(self, lows, highs) -> bool:
        """
        向上跳空：
        今日最低价 > 昨日最高价
        """
        if len(lows) < 2 or len(highs) < 2:
            return False

        return self._is_gap_up(lows[0], highs[1])

    def _check_hong_san_bing(self, opens, closes, highs) -> bool:
        """
        红三兵：
        连续三根阳线，逐日走高
        """
        if len(opens) < 3:
            return False

        # 三连阳
        for i in range(3):
            if not self._is_bullish_candle(opens[i], closes[i]):
                return False

        # 逐日走高（收盘价）
        return closes[0] > closes[1] > closes[2]

    def _check_zaochen_star(self, opens, closes, highs, lows) -> bool:
        """
        早晨之星：
        三日形态，第一天下跌（阴线），第二天十字星，第三天上涨（阳线）
        """
        if len(opens) < 3:
            return False

        # 第一天：阴线（下跌）
        if not self._is_bearish_candle(opens[2], closes[2]):
            return False

        # 第二天：星线（实体很小，上下影线较长）
        star_open, star_close = opens[1], closes[1]
        star_body = abs(star_close - star_open)
        star_upper = highs[1] - max(star_open, star_close)
        star_lower = min(star_open, star_close) - lows[1]

        # 实体小于上下影线的1/3
        if star_body > star_upper or star_body > star_lower:
            return False

        # 第三天：阳线，收盘价显著高于第一天开盘价
        if not self._is_bullish_candle(opens[0], closes[0]):
            return False

        # 第三天阳线实体应该较大
        if self._body_size(opens[0], closes[0]) < self._body_size(opens[2], closes[2]) * 0.6:
            return False

        # 收盘价应超过第一天实体中点
        first_mid = (opens[2] + closes[2]) / 2
        return closes[0] > first_mid

    def _check_shangsheng_sanfa(self, opens, closes) -> bool:
        """
        上升三法：
        上升趋势中出现一小波回调，但不跌破第一根大阳线的开盘价
        """
        if len(opens) < 5:
            return False

        # 第一天：大阳线
        first_body = self._body_size(opens[4], closes[4])
        if not (self._is_bullish_candle(opens[4], closes[4]) and first_body > 0):
            return False

        first_open = opens[4]
        first_close = closes[4]

        # 中间2-3天回调，但收盘价不低于第一天开盘价
        for i in range(1, 4):
            if closes[i] < first_open:
                return False

        # 最后一天：阳线收盘价创新高
        if not self._is_bullish_candle(opens[0], closes[0]):
            return False

        return closes[0] > first_close

    def get_pattern_signals(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        获取所有形态的详细信号

        Returns:
            包含各形态识别结果的字典
        """
        patterns = self.recognize(df)

        result = {
            'patterns_found': [p.name for p in patterns],
            'total_score': sum(p.score for p in patterns),
            'bullish_count': sum(1 for p in patterns if p.signal == 'bullish'),
            'details': []
        }

        for p in patterns:
            result['details'].append({
                'name': p.name,
                'signal': p.signal,
                'score': p.score,
                'description': p.description
            })

        return result
