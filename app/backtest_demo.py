"""回测结果展示页（路线 A Demo）：读取本地回测数据包，渲染 K 线/买卖点/统计。"""
import json
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.utils import get_current_user

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
DATA_DIR = BASE_DIR / "data" / "backtest_runs"


def _load_run(run_id: str) -> dict:
    path = DATA_DIR / f"{run_id}.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _build_trades(run: dict) -> list:
    """把 trade_events 按 trade_id 聚合：一次买入 + 一次清仓 = 一笔交易。"""
    trades: list[dict] = []
    for ev in run.get("trade_events", []):
        if ev.get("event_kind") == "entry":
            trades.append({
                "trade_id": ev.get("trade_id"),
                "buy_date": ev.get("date"),
                "buy_price": ev.get("price"),
                "shares": ev.get("shares"),
                "sell_date": None,
                "sell_price": None,
                "reason": None,
            })
        else:  # exit_all
            for t in reversed(trades):
                if t["trade_id"] == ev.get("trade_id"):
                    t["sell_date"] = ev.get("date")
                    t["sell_price"] = ev.get("price")
                    t["reason"] = ev.get("reason_text") or t.get("reason")
                    break
    for t in trades:
        if t.get("buy_price") and t.get("sell_price"):
            t["pnl_pct"] = round((t["sell_price"] - t["buy_price"]) / t["buy_price"] * 100, 2)
            t["pnl_amount"] = round((t["sell_price"] - t["buy_price"]) * t.get("shares", 0), 0)
    return trades


@router.get("/backtest", response_class=HTMLResponse)
async def backtest_page(request: Request) -> HTMLResponse:
    username = get_current_user(request)
    if username is None:
        return RedirectResponse(url="/login")
    run = _load_run("600519-web-demo")
    trades = _build_trades(run)
    return templates.TemplateResponse(
        request,
        "backtest.html",
        {
            "username": username,
            "run": run,
            "trades": trades,
        },
    )
