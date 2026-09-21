"""
WebSocket 实时行情
"""
from typing import Dict, Set
import json
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from providers.akshare_provider import AKShareProvider


router = APIRouter(prefix="/ws", tags=["WebSocket"])


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # client_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # stock_code -> set of client_ids
        self.subscriptions: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        ws = self.active_connections.pop(client_id, None)
        if ws:
            # 从所有订阅中移除
            for stock_code in self.subscriptions:
                self.subscriptions[stock_code].discard(client_id)

    def subscribe(self, client_id: str, stock_codes: list):
        for code in stock_codes:
            if code not in self.subscriptions:
                self.subscriptions[code] = set()
            self.subscriptions[code].add(client_id)

    def unsubscribe(self, client_id: str, stock_codes: list):
        for code in stock_codes:
            if code in self.subscriptions:
                self.subscriptions[code].discard(client_id)

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

    async def broadcast_price(self, stock_code: str, price_data: dict):
        if stock_code not in self.subscriptions:
            return

        message = json.dumps({
            'type': 'price',
            'data': price_data
        })

        for client_id in self.subscriptions[stock_code]:
            ws = self.active_connections.get(client_id)
            if ws:
                try:
                    await ws.send_text(message)
                except Exception:
                    pass


# 全局连接管理器
manager = ConnectionManager()


@router.websocket("/realtime")
async def websocket_realtime(websocket: WebSocket, client_id: str = None):
    """实时行情 WebSocket"""
    import uuid

    if not client_id:
        client_id = str(uuid.uuid4())

    await manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            action = message.get('action')

            if action == 'subscribe':
                codes = message.get('codes', [])
                manager.subscribe(client_id, codes)
                await manager.send_personal_message(
                    json.dumps({'type': 'subscribed', 'codes': codes}),
                    client_id
                )

            elif action == 'unsubscribe':
                codes = message.get('codes', [])
                manager.unsubscribe(client_id, codes)
                await manager.send_personal_message(
                    json.dumps({'type': 'unsubscribed', 'codes': codes}),
                    client_id
                )

            elif action == 'ping':
                await manager.send_personal_message(
                    json.dumps({'type': 'pong'}),
                    client_id
                )

    except WebSocketDisconnect:
        manager.disconnect(client_id)


async def price_update_task():
    """后台任务：定期更新实时价格"""
    provider = AKShareProvider()

    while True:
        try:
            # 获取所有订阅的股票
            subscribed_codes = list(manager.subscriptions.keys())

            if subscribed_codes:
                # 获取实时行情
                all_prices = provider.get_realtime_price()

                # 广播价格更新
                for code in subscribed_codes:
                    for price in all_prices:
                        if price.get('代码') == code:
                            await manager.broadcast_price(code, {
                                'code': code,
                                'name': price.get('名称'),
                                'price': price.get('最新价'),
                                'change_pct': price.get('涨跌幅'),
                                'volume': price.get('成交量'),
                                'amount': price.get('成交额'),
                            })
                            break

        except Exception as e:
            print(f"Price update error: {e}")

        await asyncio.sleep(5)  # 5秒更新一次
