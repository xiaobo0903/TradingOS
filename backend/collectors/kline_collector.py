"""
K线数据采集模块
使用新浪财经 API 获取日K、分钟K线数据
"""

import subprocess
import json
import re
from typing import List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KlineCollector:
    """K线数据采集器"""

    def __init__(self):
        self.sina_kline_url = "https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData"

    def _curl_request(self, url: str, params: dict = None) -> str:
        """使用 curl 发起请求"""
        cmd = ["curl", "-s", "--noproxy", "*"]

        if params:
            query = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{url}?{query}"

        cmd.append(url)

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            return result.stdout.decode("utf-8", errors="replace")
        except Exception as e:
            logger.error(f"curl 请求失败: {e}")
            return ""

    def get_daily_kline(
        self,
        symbol: str,
        days: int = 100,
        scale: int = 240,
    ) -> List[dict]:
        """
        获取日K线数据

        Args:
            symbol: 股票代码，如 "600519"
            days: 获取天数
            scale: K线周期（默认240分钟=日K）
        """
        code = symbol if symbol.startswith(("sh", "sz")) else (
            f"sh{symbol}" if symbol.startswith("6") else f"sz{symbol}"
        )

        params = {
            "symbol": code,
            "scale": scale,
            "ma": "no",  # 不需要新浪的MA，我们自己计算
            "datalen": days,
        }

        logger.info(f"正在获取 {symbol} 日K线数据...")
        response = self._curl_request(self.sina_kline_url, params)

        if not response:
            return []

        try:
            data = json.loads(response)
            records = []
            for item in data:
                records.append({
                    "symbol": symbol,
                    "trade_date": item.get("day"),
                    "open": float(item.get("open", 0)),
                    "high": float(item.get("high", 0)),
                    "low": float(item.get("low", 0)),
                    "close": float(item.get("close", 0)),
                    "volume": int(item.get("volume", 0)),
                })
            logger.info(f"获取到 {len(records)} 条K线数据")
            return records
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"解析K线数据失败: {e}")
            return []

    def get_minute_kline(
        self,
        symbol: str,
        period: int = 5,
        days: int = 5,
    ) -> List[dict]:
        """
        获取分钟K线数据

        Args:
            symbol: 股票代码，如 "600519"
            period: 分钟周期（1, 5, 15, 30, 60）
            days: 获取天数
        """
        code = symbol if symbol.startswith(("sh", "sz")) else (
            f"sh{symbol}" if symbol.startswith("6") else f"sz{symbol}"
        )

        # 新浪分钟K线接口
        params = {
            "symbol": code,
            "scale": period,
            "ma": "no",
            "datalen": days * 78,  # 每天大约78个5分钟K线
        }

        logger.info(f"正在获取 {symbol} {period}分钟K线数据...")
        response = self._curl_request(self.sina_kline_url, params)

        if not response:
            return []

        try:
            data = json.loads(response)
            records = []
            for item in data:
                records.append({
                    "symbol": symbol,
                    "timestamp": item.get("day"),
                    "period": f"{period}min",
                    "open": float(item.get("open", 0)),
                    "high": float(item.get("high", 0)),
                    "low": float(item.get("low", 0)),
                    "close": float(item.get("close", 0)),
                    "volume": int(item.get("volume", 0)),
                })
            logger.info(f"获取到 {len(records)} 条分钟K线数据")
            return records
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"解析分钟K线数据失败: {e}")
            return []

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        获取最新价格（用于计算涨跌）
        """
        code = symbol if symbol.startswith(("sh", "sz")) else (
            f"sh{symbol}" if symbol.startswith("6") else f"sz{symbol}"
        )

        url = f"https://hq.sinajs.cn/list={code}"
        headers = {"Referer": "https://finance.sina.com.cn"}

        cmd = ["curl", "-s", "--noproxy", "*", "-H", f"Referer: {headers['Referer']}", url]
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            response = result.stdout.decode("gbk", errors="replace")

            match = re.search(r'="([^"]+)"', response)
            if match:
                fields = match.group(1).split(",")
                if len(fields) > 3:
                    return float(fields[3])
        except Exception as e:
            logger.error(f"获取最新价格失败: {e}")

        return None


if __name__ == "__main__":
    collector = KlineCollector()

    # 测试获取日K线
    print("=== 测试获取日K线 (贵州茅台 600519) ===")
    klines = collector.get_daily_kline("600519", days=10)
    if klines:
        print(f"获取 {len(klines)} 条数据")
        print("最新5条:")
        for k in klines[-5:]:
            print(f"  {k['trade_date']}: 开{k['open']} 高{k['high']} 低{k['low']} 收{k['close']} 量{k['volume']}")

    # 测试获取分钟K线
    print("\n=== 测试获取5分钟K线 ===")
    minute_klines = collector.get_minute_kline("600519", period=5, days=1)
    if minute_klines:
        print(f"获取 {len(minute_klines)} 条数据")
        print("最新3条:")
        for k in minute_klines[-3:]:
            print(f"  {k['timestamp']}: 收{k['close']}")
