"""
股票基础信息采集模块
使用新浪/腾讯财经 API 获取 A 股实时行情
"""

import subprocess
import json
import re
from typing import List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockCollector:
    """股票信息采集器"""

    def __init__(self):
        self.sina_base_url = "https://hq.sinajs.cn/list="
        self.tencent_base_url = "http://qt.gtimg.cn/q="

    def _curl_request(self, url: str, headers: dict = None) -> str:
        """使用 curl 发起请求"""
        cmd = ["curl", "-s", "--noproxy", "*"]
        if headers:
            for k, v in headers.items():
                cmd.extend(["-H", f"{k}: {v}"])
        cmd.append(url)

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            # 返回 GBK 解码后的字符串
            return result.stdout.decode("gbk", errors="replace")
        except Exception as e:
            logger.error(f"curl 请求失败: {e}")
            return ""

    def get_stock_tencent(self, symbol: str) -> Optional[dict]:
        """
        使用腾讯 API 获取单只股票信息

        Args:
            symbol: 股票代码，如 "600519"
        """
        code = symbol if symbol.startswith(("sh", "sz")) else (
            f"sh{symbol}" if symbol.startswith("6") else f"sz{symbol}"
        )

        url = f"{self.tencent_base_url}{code}"
        response = self._curl_request(url)

        if not response:
            return None

        # 解析返回数据
        # 格式: v_sh600519="1~名称~代码~现价~昨收~今开~成交量~..."
        match = re.search(r'="([^"]+)"', response)
        if not match:
            return None

        fields = match.group(1).split("~")
        if len(fields) < 50:
            return None

        try:
            return {
                "code": fields[2],
                "name": fields[1],
                "price": float(fields[3]),
                "change": float(fields[3]) - float(fields[4]),
                "change_percent": (float(fields[3]) - float(fields[4])) / float(fields[4]) * 100,
                "open": float(fields[5]),
                "high": float(fields[33]),
                "low": float(fields[34]),
                "volume": int(fields[6]) * 100,  # 成交量（手）
                "amount": float(fields[37]) if fields[37] else 0,  # 成交额（元）
                "turnover": float(fields[38]) if fields[38] else 0,  # 换手率
                "pe": float(fields[39]) if fields[39] else 0,  # 市盈率
                "volume_ratio": float(fields[49]) if len(fields) > 49 and fields[49] else 0,  # 量比
            }
        except (ValueError, IndexError) as e:
            logger.warning(f"解析股票 {symbol} 数据失败: {e}")
            return None

    def get_stocks_spot(self, symbols: List[str] = None) -> List[dict]:
        """
        批量获取股票实时行情

        Args:
            symbols: 股票代码列表，如 ["600519", "000001"]。None 则获取主要指数。
        """
        if not symbols:
            # 默认获取主要股票
            symbols = ["600519", "000858", "002594", "600036", "601318", "300750"]

        results = []
        for symbol in symbols:
            info = self.get_stock_tencent(symbol)
            if info:
                results.append(info)

        return results

    def get_index_spot(self) -> List[dict]:
        """
        获取大盘指数实时行情
        """
        # 上证指数、深证成指、创业板指、科创50
        indices = ["sh000001", "sz399001", "sz399006", "sh000688"]

        results = []
        for code in indices:
            info = self.get_stock_tencent(code)
            if info:
                results.append(info)

        return results

    def get_stock_sina(self, symbol: str) -> Optional[dict]:
        """
        使用新浪 API 获取单只股票信息
        """
        code = symbol if symbol.startswith(("sh", "sz")) else (
            f"sh{symbol}" if symbol.startswith("6") else f"sz{symbol}"
        )

        url = f"{self.sina_base_url}{code}"
        headers = {"Referer": "https://finance.sina.com.cn"}
        response = self._curl_request(url, headers=headers)

        if not response:
            return None

        # 格式: var hq_str_sh600519="名称,现价,昨收,今开,最高,最低,..."
        match = re.search(r'="([^"]+)"', response)
        if not match:
            return None

        fields = match.group(1).split(",")
        if len(fields) < 32:
            return None

        try:
            return {
                "code": fields[0] if len(fields) > 0 else symbol,
                "name": fields[0] if len(fields) > 0 else "",
                "open": float(fields[1]) if fields[1] else 0,
                "close": float(fields[3]) if fields[3] else 0,  # 当前价格
                "high": float(fields[4]) if fields[4] else 0,
                "low": float(fields[5]) if fields[5] else 0,
                "volume": int(float(fields[8])) if fields[8] else 0,
                "amount": float(fields[9]) if fields[9] else 0,
            }
        except (ValueError, IndexError) as e:
            logger.warning(f"解析股票 {symbol} 数据失败: {e}")
            return None


if __name__ == "__main__":
    collector = StockCollector()

    # 测试获取单只股票
    print("=== 测试获取贵州茅台 (600519) ===")
    info = collector.get_stock_tencent("600519")
    if info:
        print(f"代码: {info['code']}")
        print(f"名称: {info['name']}")
        print(f"现价: {info['price']}")
        print(f"涨跌: {info['change']:.2f} ({info['change_percent']:.2f}%)")
        print(f"换手率: {info['turnover']:.2f}%")

    # 测试获取指数
    print("\n=== 测试获取大盘指数 ===")
    indices = collector.get_index_spot()
    for idx in indices:
        print(f"{idx['name']}: {idx['price']} ({idx['change_percent']:.2f}%)")

    # 测试批量获取
    print("\n=== 测试批量获取 ===")
    stocks = collector.get_stocks_spot(["600519", "000858", "002594"])
    print(f"获取到 {len(stocks)} 只股票")
