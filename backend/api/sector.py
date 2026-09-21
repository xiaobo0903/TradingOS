"""
板块 API 接口
"""
import csv
import io
import json
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.database import get_db, get_db_context
from models.stock import Stock, StockDaily
from models.sector import Sector, SectorDaily, SectorStockDaily
from utils.logging import app_logger


router = APIRouter(prefix="/api/sector", tags=["板块"])


class SectorItem(BaseModel):
    """板块项"""
    code: str
    name: str
    type: str
    change_pct: float = 0
    stock_count: int = 0
    lead_stocks: List[dict] = []
    heat_score: float = 0
    reason: str = ""


class SectorDetail(BaseModel):
    """板块详情"""
    code: str
    name: str
    type: str
    change_pct: float
    turnover_rate: float = 0
    stock_count: int
    lead_stocks: List[dict]
    heat_rank: int = 0
    heat_reason: str = ""
    history: List[dict] = []


class SectorStockItem(BaseModel):
    """板块内股票项"""
    code: str
    name: str
    change_pct: float
    volume: int
    turnover_rate: float
    reason: str = ""


class SectorListResponse(BaseModel):
    """板块列表响应"""
    total: int
    items: List[SectorItem]


class CSVImportRequest(BaseModel):
    """CSV导入请求（用于预览）"""
    sector_name: str
    trade_date: str
    rows: List[dict]


class CSVImportResponse(BaseModel):
    """CSV导入响应"""
    success: bool
    total_rows: int
    imported: int
    skipped: int
    errors: List[str]
    preview: List[dict]
    unmatched_codes: List[str]  # 无法匹配的股票代码


def calculate_heat_score(sector_data: dict) -> float:
    """计算板块热度评分"""
    score = 0

    # 涨跌幅贡献 (权重 40%)
    change_pct = sector_data.get('change_pct', 0)
    if change_pct > 0:
        score += min(change_pct * 4, 40)  # 涨得越多分数越高
    else:
        score += max(change_pct * 2, -20)  # 跌的越多扣分越多

    # 成交量贡献 (权重 30%)
    volume_ratio = sector_data.get('volume_ratio', 1)
    if volume_ratio > 1:
        score += min((volume_ratio - 1) * 15, 30)  # 放量越多分数越高
    elif volume_ratio < 1:
        score += max((volume_ratio - 1) * 20, -15)  # 缩量扣分

    # 股票数量贡献 (权重 10%)
    stock_count = sector_data.get('stock_count', 0)
    score += min(stock_count * 0.1, 10)

    # 龙头股表现贡献 (权重 20%)
    lead_performance = sector_data.get('lead_performance', 0)
    if lead_performance > 0:
        score += min(lead_performance * 2, 20)

    return round(score, 2)


def get_heat_reason(sector_data: dict) -> str:
    """根据板块数据生成热度原因"""
    reasons = []
    change_pct = sector_data.get('change_pct', 0)
    volume_ratio = sector_data.get('volume_ratio', 1)
    lead_performance = sector_data.get('lead_performance', 0)

    if change_pct >= 5:
        reasons.append("涨幅领先")
    elif change_pct >= 3:
        reasons.append("表现强势")
    elif change_pct > 0:
        reasons.append("小幅上涨")

    if volume_ratio > 2:
        reasons.append("成交量激增")
    elif volume_ratio > 1.5:
        reasons.append("明显放量")

    if lead_performance >= 5:
        reasons.append("龙头股涨停带动")
    elif lead_performance >= 3:
        reasons.append("龙头股表现突出")

    if change_pct < -3:
        reasons.append("回调幅度较大")

    return "、".join(reasons) if reasons else "板块平稳"


@router.get("/csv-template")
def get_csv_template():
    """获取CSV导入模板"""
    return {
        'filename': 'sector_stock_data.csv',
        'columns': [
            {'name': 'sector_name', 'description': '板块名称', 'required': True},
            {'name': 'trade_date', 'description': '日期 (YYYY-MM-DD)', 'required': True},
            {'name': 'stock_code', 'description': '股票代码（6位）', 'required': True},
            {'name': 'stock_name', 'description': '股票名称', 'required': False},
            {'name': 'close', 'description': '收盘价', 'required': False},
            {'name': 'change_pct', 'description': '涨跌幅(%)', 'required': False},
            {'name': 'volume', 'description': '成交量', 'required': False},
            {'name': 'turnover_rate', 'description': '换手率(%)', 'required': False},
            {'name': 'open', 'description': '开盘价', 'required': False},
            {'name': 'high', 'description': '最高价', 'required': False},
            {'name': 'low', 'description': '最低价', 'required': False},
            {'name': 'amount', 'description': '成交额', 'required': False},
        ],
        'example': [
            {'sector_name': '锂电池', 'trade_date': '2026-09-13', 'stock_code': '000001', 'stock_name': '平安银行', 'close': '11.74', 'change_pct': '2.5', 'volume': '832461', 'turnover_rate': '1.2'},
            {'sector_name': '锂电池', 'trade_date': '2026-09-13', 'stock_code': '600519', 'stock_name': '贵州茅台', 'close': '1650.00', 'change_pct': '-1.2', 'volume': '123456', 'turnover_rate': '0.5'},
        ]
    }


@router.get("/imported-data")
def get_imported_sector_data(
    sector_name: Optional[str] = Query(None, description="板块名称（模糊匹配）"),
    trade_date: Optional[str] = Query(None, description="数据日期 YYYY-MM-DD"),
    limit: int = Query(50, description="返回数量"),
    offset: int = Query(0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """获取已导入的板块数据"""
    query = db.query(SectorStockDaily)

    if sector_name:
        # 查找板块ID
        sector = db.query(Sector).filter(Sector.name.like(f"%{sector_name}%")).first()
        if sector:
            query = query.filter(SectorStockDaily.sector_id == sector.id)

    if trade_date:
        try:
            parsed_date = datetime.strptime(trade_date, '%Y-%m-%d').date()
            query = query.filter(SectorStockDaily.trade_date == parsed_date)
        except ValueError:
            pass

    total = query.count()
    records = query.order_by(
        SectorStockDaily.trade_date.desc(),
        SectorStockDaily.change_pct.desc()
    ).offset(offset).limit(limit).all()

    items = []
    for r in records:
        items.append({
            'id': r.id,
            'sector_id': r.sector_id,
            'sector_name': r.sector.name if r.sector else '',
            'stock_code': r.stock_code,
            'stock_name': r.stock_name,
            'trade_date': r.trade_date.strftime('%Y-%m-%d') if r.trade_date else '',
            'close': r.close,
            'change_pct': r.change_pct,
            'volume': r.volume,
            'turnover_rate': r.turnover_rate,
            'open': r.open,
            'high': r.high,
            'low': r.low,
            'amount': r.amount,
        })

    return {
        'total': total,
        'items': items
    }


@router.post("/import-csv", response_model=CSVImportResponse)
async def import_sector_csv(
    sector_name: str = Form(..., description="板块名称"),
    trade_date: str = Form(..., description="数据日期 YYYY-MM-DD"),
    file: UploadFile = File(..., description="CSV文件"),
):
    """
    导入板块数据CSV文件

    CSV格式要求：
    - sector_name: 板块名称
    - trade_date: 日期 (YYYY-MM-DD)
    - stock_code: 股票代码（6位字符串，确保前导零不丢失）
    - stock_name: 股票名称
    - close: 收盘价
    - change_pct: 涨跌幅
    - volume: 成交量
    - turnover_rate: 换手率

    其他可选字段：open, high, low, amount
    """
    # 解析CSV
    content = await file.read()
    try:
        decoded_content = content.decode('utf-8-sig')  # 处理BOM
    except UnicodeDecodeError:
        try:
            decoded_content = content.decode('gbk')
        except UnicodeDecodeError:
            return CSVImportResponse(
                success=False,
                total_rows=0,
                imported=0,
                skipped=0,
                errors=["无法解码文件，请确保文件为UTF-8或GBK编码"],
                preview=[],
                unmatched_codes=[]
            )

    # 解析CSV
    reader = csv.DictReader(io.StringIO(decoded_content))
    rows = []
    for row in reader:
        rows.append(row)

    if not rows:
        return CSVImportResponse(
            success=False,
            total_rows=0,
            imported=0,
            skipped=0,
            errors=["CSV文件为空"],
            preview=[],
            unmatched_codes=[]
        )

    # 验证日期格式
    try:
        parsed_date = datetime.strptime(trade_date, '%Y-%m-%d').date()
    except ValueError:
        return CSVImportResponse(
            success=False,
            total_rows=len(rows),
            imported=0,
            skipped=0,
            errors=[f"日期格式错误: {trade_date}，应为 YYYY-MM-DD"],
            preview=[],
            unmatched_codes=[]
        )

    # 构建股票代码到ID的映射（使用字符串键）
    with get_db_context() as db:
        all_stocks = db.query(Stock).all()
        stock_code_to_id = {s.code: s.id for s in all_stocks}
        stock_code_to_name = {s.code: s.name for s in all_stocks}

    # 查找或创建板块
    sector_id = None
    with get_db_context() as db:
        sector = db.query(Sector).filter(Sector.name == sector_name).first()
        if sector:
            sector_id = sector.id
        else:
            # 根据名称猜测板块类型
            sector_type = 'concept'
            if '行业' in sector_name or '产业' in sector_name:
                sector_type = 'industry'
            elif '地域' in sector_name or '地区' in sector_name:
                sector_type = 'region'

            new_sector = Sector(
                code=f"sector_{sector_name[:10]}",
                name=sector_name,
                type=sector_type
            )
            db.add(new_sector)
            db.commit()
            sector_id = new_sector.id

    # 处理数据
    imported_count = 0
    skipped_count = 0
    errors = []
    preview = []
    unmatched_codes = set()

    with get_db_context() as db:
        for i, row in enumerate(rows):
            try:
                stock_code = row.get('stock_code', '').strip()
                stock_name = row.get('stock_name', '').strip()
                close = row.get('close', '').strip()
                change_pct = row.get('change_pct', '').strip()
                volume = row.get('volume', '').strip()
                turnover_rate = row.get('turnover_rate', '').strip()
                open_price = row.get('open', '').strip()
                high = row.get('high', '').strip()
                low = row.get('low', '').strip()
                amount = row.get('amount', '').strip()

                # 验证股票代码（必须是6位字符串）
                if not stock_code:
                    errors.append(f"第{i+2}行：股票代码为空")
                    skipped_count += 1
                    continue

                # 标准化股票代码（补齐到6位）
                stock_code = stock_code.zfill(6)

                # 检查股票是否存在于库中
                stock_id = stock_code_to_id.get(stock_code)
                if not stock_id:
                    unmatched_codes.add(stock_code)
                    # 仍然保存，但stock_id为null
                    app_logger.debug(f"股票代码 {stock_code} 在库中不存在")

                # 检查是否已存在记录
                existing = db.query(SectorStockDaily).filter(
                    SectorStockDaily.sector_id == sector_id,
                    SectorStockDaily.stock_code == stock_code,
                    SectorStockDaily.trade_date == parsed_date
                ).first()

                # 收集额外数据
                extra_fields = {}
                for key, value in row.items():
                    if key not in ['stock_code', 'stock_name', 'close', 'change_pct', 'volume',
                                   'turnover_rate', 'open', 'high', 'low', 'amount']:
                        if value and value.strip():
                            extra_fields[key] = value.strip()

                if existing:
                    # 更新
                    existing.stock_id = stock_id
                    existing.stock_name = stock_name
                    existing.close = close
                    existing.change_pct = change_pct
                    existing.volume = volume
                    existing.turnover_rate = turnover_rate
                    existing.open = open_price
                    existing.high = high
                    existing.low = low
                    existing.amount = amount
                    if extra_fields:
                        existing.extra_data = json.dumps(extra_fields, ensure_ascii=False)
                else:
                    # 新增
                    record = SectorStockDaily(
                        sector_id=sector_id,
                        stock_id=stock_id,
                        trade_date=parsed_date,
                        stock_code=stock_code,
                        stock_name=stock_name,
                        close=close,
                        change_pct=change_pct,
                        volume=volume,
                        turnover_rate=turnover_rate,
                        open=open_price,
                        high=high,
                        low=low,
                        amount=amount,
                        extra_data=json.dumps(extra_fields, ensure_ascii=False) if extra_fields else None
                    )
                    db.add(record)

                imported_count += 1
                preview.append({
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'close': close,
                    'change_pct': change_pct,
                    'matched': stock_id is not None
                })

            except Exception as e:
                errors.append(f"第{i+2}行处理失败: {str(e)}")
                skipped_count += 1
                continue

        db.commit()

    return CSVImportResponse(
        success=True,
        total_rows=len(rows),
        imported=imported_count,
        skipped=skipped_count,
        errors=errors[:20],  # 最多返回20条错误
        preview=preview[:10],  # 最多返回10条预览
        unmatched_codes=list(unmatched_codes)
    )


@router.get("/list", response_model=SectorListResponse)
def get_sector_list(
    sector_type: Optional[str] = Query(None, description="板块类型: industry/concept/region"),
    limit: int = Query(50, description="返回数量"),
    offset: int = Query(0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """获取板块列表（带热度评分）"""
    query = db.query(Sector)
    if sector_type:
        query = query.filter(Sector.type == sector_type)

    total = query.count()
    sectors = query.offset(offset).limit(limit).all()

    items = []
    today = datetime.now().date()

    for sector in sectors:
        # 获取板块最新行情
        latest = db.query(SectorDaily).filter(
            SectorDaily.sector_id == sector.id
        ).order_by(SectorDaily.trade_date.desc()).first()

        # 获取板块内股票数量
        stock_count = db.query(Stock).filter(
            Stock.industry == sector.name
        ).count()

        # 获取板块内股票的详细数据
        stocks_data = db.query(Stock, StockDaily).join(
            StockDaily, StockDaily.stock_id == Stock.id
        ).filter(
            Stock.industry == sector.name,
            Stock.status == 'active'
        ).order_by(StockDaily.trade_date.desc()).limit(100).all()

        # 计算平均涨跌幅和成交量
        total_change = 0
        total_volume = 0
        count = 0
        lead_stocks = []

        stock_prices = {}
        for stock, daily in stocks_data:
            if stock.code not in stock_prices:
                stock_prices[stock.code] = {
                    'name': stock.name,
                    'code': stock.code,
                    'change_pct': float(daily.change_pct) if daily.change_pct else 0,
                    'volume': daily.volume or 0,
                    'turnover_rate': float(daily.turnover_rate) if daily.turnover_rate else 0,
                }

        stock_list = list(stock_prices.values())
        if stock_list:
            for s in stock_list:
                total_change += s['change_pct']
                total_volume += s['volume']
                count += 1

            # 获取龙头股（涨跌幅最大的3只）
            top_stocks = sorted(stock_list, key=lambda x: x['change_pct'], reverse=True)[:3]
            lead_stocks = [{
                'code': s['code'],
                'name': s['name'],
                'change_pct': s['change_pct']
            } for s in top_stocks]

        avg_change = total_change / count if count > 0 else 0
        avg_volume = total_volume / count if count > 0 else 0

        # 计算热度评分
        sector_data = {
            'change_pct': avg_change,
            'stock_count': stock_count,
            'volume_ratio': 1.0,  # 简化处理
            'lead_performance': top_stocks[0]['change_pct'] if top_stocks else 0,
        }

        heat_score = calculate_heat_score(sector_data)
        heat_reason = get_heat_reason(sector_data)

        items.append(SectorItem(
            code=sector.code,
            name=sector.name,
            type=sector.type or 'concept',
            change_pct=round(avg_change, 2),
            stock_count=stock_count,
            lead_stocks=lead_stocks,
            heat_score=heat_score,
            reason=heat_reason,
        ))

    # 按热度评分排序
    items.sort(key=lambda x: x.heat_score, reverse=True)

    return SectorListResponse(total=total, items=items)


@router.get("/hot")
def get_hot_sectors(
    limit: int = Query(20, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取热门板块（热度排名）"""
    # 获取所有板块
    sectors = db.query(Sector).all()

    items = []
    for sector in sectors:
        # 获取板块内股票数据
        stocks_data = db.query(Stock, StockDaily).join(
            StockDaily, StockDaily.stock_id == Stock.id
        ).filter(
            Stock.industry == sector.name,
            Stock.status == 'active'
        ).order_by(StockDaily.trade_date.desc()).limit(200).all()

        # 计算统计数据
        stock_prices = {}
        for stock, daily in stocks_data:
            if stock.code not in stock_prices:
                stock_prices[stock.code] = {
                    'name': stock.name,
                    'code': stock.code,
                    'change_pct': float(daily.change_pct) if daily.change_pct else 0,
                    'volume': daily.volume or 0,
                    'turnover_rate': float(daily.turnover_rate) if daily.turnover_rate else 0,
                }

        stock_list = list(stock_prices.values())
        if not stock_list:
            continue

        total_change = sum(s['change_pct'] for s in stock_list)
        avg_change = total_change / len(stock_list)

        # 龙头股
        top_stocks = sorted(stock_list, key=lambda x: x['change_pct'], reverse=True)[:3]

        sector_data = {
            'change_pct': avg_change,
            'stock_count': len(stock_list),
            'volume_ratio': 1.0,
            'lead_performance': top_stocks[0]['change_pct'] if top_stocks else 0,
        }

        heat_score = calculate_heat_score(sector_data)
        heat_reason = get_heat_reason(sector_data)

        items.append({
            'rank': 0,  # 稍后计算
            'code': sector.code,
            'name': sector.name,
            'type': sector.type or 'concept',
            'change_pct': round(avg_change, 2),
            'stock_count': len(stock_list),
            'lead_stocks': [{'code': s['code'], 'name': s['name'], 'change_pct': s['change_pct']} for s in top_stocks],
            'heat_score': heat_score,
            'heat_reason': heat_reason,
        })

    # 按热度评分排序并设置排名
    items.sort(key=lambda x: x['heat_score'], reverse=True)
    for i, item in enumerate(items):
        item['rank'] = i + 1

    return {
        'total': len(items),
        'items': items[:limit],
    }


@router.get("/{sector_code}")
def get_sector_detail(
    sector_code: str,
    db: Session = Depends(get_db)
):
    """获取板块详情"""
    sector = db.query(Sector).filter(Sector.code == sector_code).first()
    if not sector:
        return {"error": "板块不存在"}

    # 获取板块内股票
    stocks_data = db.query(Stock, StockDaily).join(
        StockDaily, StockDaily.stock_id == Stock.id
    ).filter(
        Stock.industry == sector.name,
        Stock.status == 'active'
    ).order_by(StockDaily.trade_date.desc()).limit(500).all()

    # 去重并获取最新数据
    stock_prices = {}
    for stock, daily in stocks_data:
        if stock.code not in stock_prices:
            stock_prices[stock.code] = {
                'name': stock.name,
                'code': stock.code,
                'change_pct': float(daily.change_pct) if daily.change_pct else 0,
                'volume': daily.volume or 0,
                'turnover_rate': float(daily.turnover_rate) if daily.turnover_rate else 0,
            }

    stock_list = list(stock_prices.values())

    # 计算统计数据
    if stock_list:
        total_change = sum(s['change_pct'] for s in stock_list)
        avg_change = total_change / len(stock_list)
    else:
        avg_change = 0

    # 龙头股
    top_stocks = sorted(stock_list, key=lambda x: x['change_pct'], reverse=True)[:5]

    # 获取历史数据
    history = db.query(SectorDaily).filter(
        SectorDaily.sector_id == sector.id
    ).order_by(SectorDaily.trade_date.desc()).limit(10).all()

    history_data = [{
        'date': h.trade_date.isoformat() if h.trade_date else '',
        'change_pct': float(h.change_pct) if h.change_pct else 0,
        'turnover_rate': float(h.turnover_rate) if h.turnover_rate else 0,
    } for h in history]

    sector_data = {
        'change_pct': avg_change,
        'stock_count': len(stock_list),
        'volume_ratio': 1.0,
        'lead_performance': top_stocks[0]['change_pct'] if top_stocks else 0,
    }

    heat_score = calculate_heat_score(sector_data)
    heat_reason = get_heat_reason(sector_data)

    return {
        'code': sector.code,
        'name': sector.name,
        'type': sector.type or 'concept',
        'change_pct': round(avg_change, 2),
        'stock_count': len(stock_list),
        'lead_stocks': [{'code': s['code'], 'name': s['name'], 'change_pct': s['change_pct']} for s in top_stocks],
        'heat_score': heat_score,
        'heat_reason': heat_reason,
        'history': history_data,
    }


@router.get("/{sector_code}/stocks")
def get_sector_stocks(
    sector_code: str,
    sort_by: str = Query('change_pct', description="排序字段: change_pct/volume/turnover_rate"),
    order: str = Query('desc', description="排序方向: asc/desc"),
    limit: int = Query(50, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取板块内股票列表"""
    sector = db.query(Sector).filter(Sector.code == sector_code).first()
    if not sector:
        return {"error": "板块不存在"}

    # 获取板块内股票最新数据
    stocks_data = db.query(Stock, StockDaily).join(
        StockDaily, StockDaily.stock_id == Stock.id
    ).filter(
        Stock.industry == sector.name,
        Stock.status == 'active'
    ).order_by(StockDaily.trade_date.desc()).all()

    # 去重
    stock_map = {}
    for stock, daily in stocks_data:
        if stock.code not in stock_map:
            stock_map[stock.code] = {
                'code': stock.code,
                'name': stock.name,
                'change_pct': float(daily.change_pct) if daily.change_pct else 0,
                'volume': daily.volume or 0,
                'turnover_rate': float(daily.turnover_rate) if daily.turnover_rate else 0,
                'current_price': float(daily.close) if daily.close else 0,
            }

    items = list(stock_map.values())

    # 排序
    reverse = order == 'desc'
    if sort_by == 'volume':
        items.sort(key=lambda x: x['volume'], reverse=reverse)
    elif sort_by == 'turnover_rate':
        items.sort(key=lambda x: x['turnover_rate'], reverse=reverse)
    else:  # change_pct
        items.sort(key=lambda x: x['change_pct'], reverse=reverse)

    return {
        'sector_name': sector.name,
        'total': len(items),
        'items': items[:limit],
    }
