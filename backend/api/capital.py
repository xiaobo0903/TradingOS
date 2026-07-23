from fastapi import APIRouter
from models.schemas import CapitalData
from typing import List

router = APIRouter()


@router.get("/{code}", response_model=CapitalData)
async def get_capital(code: str):
    return CapitalData(
        main_inflow=125000000,
        main_outflow=98000000,
        super_large_in=85000000,
        super_large_out=62000000,
        large_in=68000000,
        large_out=55000000,
        medium_in=32000000,
        medium_out=45000000,
        small_in=18000000,
        small_out=35000000
    )


@router.get("/market/main")
async def get_main_capital():
    return {
        "total_inflow": 1250000000,
        "total_outflow": 980000000,
        "net_inflow": 270000000,
        "north_money": 28500000,
        "super_large": {
            "inflow": 850000000,
            "outflow": 620000000,
            "net": 230000000
        }
    }


@router.get("/dragon")
async def get_dragon_list():
    return [
        {
            "date": "07-22",
            "stock_name": "贵州茅台",
            "stock_code": "600519",
            "reason": "连续3日涨幅偏离值达20%",
            "buy_amount": 5800000000,
            "sell_amount": 4200000000,
            "net_amount": 1600000000
        },
        {
            "date": "07-22",
            "stock_name": "比亚迪",
            "stock_code": "002594",
            "reason": "日涨幅偏离值达7%",
            "buy_amount": 3200000000,
            "sell_amount": 2800000000,
            "net_amount": 400000000
        },
        {
            "date": "07-21",
            "stock_name": "宁德时代",
            "stock_code": "300750",
            "reason": "融资融券信息",
            "buy_amount": 4500000000,
            "sell_amount": 5100000000,
            "net_amount": -600000000
        }
    ]


@router.get("/north")
async def get_north_money():
    return {
        "date": "2026-07-22",
        "sh_connect": 15200000000,
        "sz_connect": 13300000000,
        "total": 28500000000,
        "change": 2850000000
    }
