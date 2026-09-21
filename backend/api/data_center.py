"""
数据采集 API 接口 - 简化版
只保留股票明细相关功能，数据全部来自Tushare
"""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel


router = APIRouter(prefix="/api/data-center", tags=["数据中心"])


class ImportResponse(BaseModel):
    success: bool
    message: str
    total_rows: int = 0
    success_count: int = 0
    error_count: int = 0
    errors: list = []


@router.get("/realtime/list")
def get_realtime_list(
    trade_date: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = 'pct_chg',
    order: str = 'desc',
    limit: int = 100,
    offset: int = 0,
):
    """
    获取股票实时行情列表（股票明细页面用）

    数据来源：Tushare Pro
    """
    from models.database import get_db_context
    from models.capital import StockRealtime
    from models.stock import Stock

    with get_db_context() as db:
        query = db.query(StockRealtime, Stock).join(
            Stock, StockRealtime.stock_id == Stock.id
        )

        if not trade_date:
            latest = db.query(StockRealtime).order_by(StockRealtime.trade_date.desc()).first()
            if latest:
                trade_date = latest.trade_date.strftime('%Y-%m-%d')

        if trade_date:
            try:
                parsed_date = datetime.strptime(trade_date, '%Y-%m-%d').date()
                query = query.filter(StockRealtime.trade_date == parsed_date)
            except ValueError:
                pass

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Stock.code.like(search_pattern)) | (Stock.name.like(search_pattern))
            )

        sort_column_map = {
            'pct_chg': StockRealtime.pct_chg,
            'turnover_rate': StockRealtime.turnover_rate,
            'volume_ratio': StockRealtime.volume_ratio,
            'amplitude': StockRealtime.amplitude,
            'amount': StockRealtime.amount,
            'volume': StockRealtime.volume,
            'total_market_cap': StockRealtime.total_market_cap,
            'float_market_cap': StockRealtime.float_market_cap,
            'close': StockRealtime.close,
            'change': StockRealtime.change,
            'stock_code': Stock.code,
            'stock_name': Stock.name,
        }
        sort_column = sort_column_map.get(sort_by, StockRealtime.pct_chg)

        if order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        total = query.count()
        results = query.offset(offset).limit(limit).all()

        items = []
        for realtime, stock in results:
            items.append({
                'stock_code': stock.code,
                'stock_name': stock.name,
                'trade_date': realtime.trade_date.strftime('%Y-%m-%d') if realtime.trade_date else None,
                'pre_close': float(realtime.pre_close) if realtime.pre_close else 0,
                'open': float(realtime.open) if realtime.open else 0,
                'high': float(realtime.high) if realtime.high else 0,
                'low': float(realtime.low) if realtime.low else 0,
                'close': float(realtime.close) if realtime.close else 0,
                'change': float(realtime.change) if realtime.change else 0,
                'pct_chg': float(realtime.pct_chg) if realtime.pct_chg else 0,
                'amplitude': float(realtime.amplitude) if realtime.amplitude else 0,
                'volume': float(realtime.volume) if realtime.volume else 0,
                'amount': float(realtime.amount) if realtime.amount else 0,
                'turnover_rate': float(realtime.turnover_rate) if realtime.turnover_rate else 0,
                'volume_ratio': float(realtime.volume_ratio) if realtime.volume_ratio else 0,
                'total_share': float(realtime.total_share) / 10000 if realtime.total_share else 0,
                'float_share': float(realtime.float_share) / 10000 if realtime.float_share else 0,
                'total_market_cap': float(realtime.total_market_cap) if realtime.total_market_cap else 0,
                'float_market_cap': float(realtime.float_market_cap) if realtime.float_market_cap else 0,
                'pe': float(realtime.pe) if realtime.pe else None,
                'pb': float(realtime.pb) if realtime.pb else None,
                'main_inflow': float(realtime.main_inflow) if realtime.main_inflow else 0,
                'main_volume': float(realtime.main_volume) if realtime.main_volume else 0,
                'weibi': float(realtime.weibi) if realtime.weibi else 0,
                'buy_price': float(realtime.buy_price) if realtime.buy_price else 0,
                'sell_price': float(realtime.sell_price) if realtime.sell_price else 0,
            })

        return {
            'trade_date': trade_date,
            'total': total,
            'items': items,
        }


@router.post("/import/csv", response_model=ImportResponse)
async def import_stock_data(
    trade_date: str,
    file: UploadFile = File(...),
):
    """
    通过CSV文件导入股票数据
    """
    from models.database import get_db_context
    from models.stock import Stock
    from models.capital import StockRealtime
    import csv
    import io
    import re

    if not file.filename.endswith('.csv'):
        return ImportResponse(
            success=False,
            message="只支持CSV格式文件",
            total_rows=0,
            success_count=0,
            error_count=0,
            errors=[]
        )

    content = await file.read()
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text = content.decode('gbk')
        except:
            return ImportResponse(
                success=False,
                message="文件编码不支持，请使用UTF-8或GBK编码",
                total_rows=0,
                success_count=0,
                error_count=0,
                errors=[]
            )

    text = re.sub(r',+', ',', text)

    def clean_number(val: str) -> float:
        if not val or not val.strip():
            return 0
        val = val.strip()
        multiplier = 1
        if '亿' in val:
            multiplier = 100000000
            val = val.replace('亿', '')
        elif '万' in val:
            multiplier = 10000
            val = val.replace('万', '')
        for unit in ['元', '%', ' ', '　']:
            val = val.replace(unit, '')
        try:
            return float(val) * multiplier
        except ValueError:
            return 0

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)

    if len(rows) == 0:
        return ImportResponse(
            success=False,
            message="CSV文件为空",
            total_rows=0,
            success_count=0,
            error_count=0,
            errors=[]
        )

    try:
        parsed_date = datetime.strptime(trade_date, '%Y-%m-%d').date()
    except ValueError:
        return ImportResponse(
            success=False,
            message=f"日期格式错误: {trade_date}，正确格式：YYYY-MM-DD",
            total_rows=0,
            success_count=0,
            error_count=0,
            errors=[]
        )

    success_count = 0
    error_count = 0
    errors = []
    expected_columns = 10

    with get_db_context() as db:
        for row_idx, row in enumerate(rows, start=1):
            if not row or len(row) == 0 or all(not cell.strip() for cell in row):
                continue

            if len(row) != expected_columns:
                errors.append({
                    'row': row_idx,
                    'message': f'列数错误，期望{expected_columns}列，实际{len(row)}列',
                    'data': ','.join(row)[:100]
                })
                error_count += 1
                continue

            try:
                stock_code = row[2].strip()
                stock_name = row[3].strip()
                main_volume = clean_number(row[4])  # 主力净量
                main_inflow = clean_number(row[5])  # 主力净流入（元）
                turnover_rate = clean_number(row[6]) if row[6].strip() else None  # 换手%
                weibi = clean_number(row[7]) if row[7].strip() else None  # 委比%
                buy_price = clean_number(row[8]) if row[8].strip() else None  # 买一价
                sell_price = clean_number(row[9]) if row[9].strip() else None  # 卖一价

                if not stock_code:
                    errors.append({
                        'row': row_idx,
                        'message': '股票代码不能为空',
                        'data': ','.join(row)[:100]
                    })
                    error_count += 1
                    continue

                stock = db.query(Stock).filter(Stock.code == stock_code).first()
                if not stock:
                    errors.append({
                        'row': row_idx,
                        'message': f'股票代码 {stock_code} 不存在',
                        'data': ','.join(row)[:100]
                    })
                    error_count += 1
                    continue

                existing = db.query(StockRealtime).filter(
                    StockRealtime.stock_id == stock.id,
                    StockRealtime.trade_date == parsed_date
                ).first()

                if existing:
                    existing.main_inflow = main_inflow if main_inflow else existing.main_inflow
                    existing.main_volume = main_volume if main_volume else existing.main_volume
                    existing.turnover_rate = turnover_rate if turnover_rate is not None else existing.turnover_rate
                    existing.weibi = weibi if weibi is not None else existing.weibi
                    existing.buy_price = buy_price if buy_price is not None else existing.buy_price
                    existing.sell_price = sell_price if sell_price is not None else existing.sell_price
                else:
                    realtime = StockRealtime(
                        stock_id=stock.id,
                        trade_date=parsed_date,
                        main_inflow=main_inflow,
                        main_volume=main_volume,
                        turnover_rate=turnover_rate,
                        weibi=weibi,
                        buy_price=buy_price,
                        sell_price=sell_price,
                        volume=0,
                        pre_close=0,
                        open=0,
                        high=0,
                        low=0,
                        close=0,
                        change=0,
                        pct_chg=0,
                        amplitude=0,
                    )
                    db.add(realtime)

                success_count += 1

            except ValueError as e:
                errors.append({
                    'row': row_idx,
                    'message': f'数据类型错误: {str(e)}',
                    'data': ','.join(row)[:100]
                })
                error_count += 1
            except Exception as e:
                errors.append({
                    'row': row_idx,
                    'message': f'处理失败: {str(e)}',
                    'data': ','.join(row)[:100]
                })
                error_count += 1

        db.commit()

    message = f"导入完成：成功{success_count}行，失败{error_count}行"
    if error_count > 0:
        message += "，请查看错误详情"

    return ImportResponse(
        success=error_count == 0,
        message=message,
        total_rows=len(rows),
        success_count=success_count,
        error_count=error_count,
        errors=errors[:100]
    )


@router.get("/status")
def get_data_status():
    """获取数据状态"""
    from models.database import get_db_context
    from models.capital import StockRealtime
    from models.stock import Stock

    with get_db_context() as db:
        stock_count = db.query(Stock).filter(Stock.status == 'active').count()
        realtime_count = db.query(StockRealtime).count()

        latest = db.query(StockRealtime).order_by(StockRealtime.trade_date.desc()).first()
        latest_date = latest.trade_date.strftime('%Y-%m-%d') if latest else None

        return {
            'stocks': stock_count,
            'realtime_records': realtime_count,
            'latest_date': latest_date,
        }
