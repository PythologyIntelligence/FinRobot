from __future__ import annotations

from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .bridge import MT5Bridge
from .config import settings
from .ledger import DecisionLedger


ledger = DecisionLedger(settings.database_path)
bridge = MT5Bridge(settings)
app = FastAPI(title="Pythology FinRobot MT5 Experiment", version="0.1.0", docs_url="/docs")


class DecisionCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float = Field(ge=0.0, le=1.0)
    thesis: str = Field(min_length=1)
    volume: float = Field(gt=0)
    requested_entry: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    market_snapshot: dict[str, Any] = Field(default_factory=dict)
    sources: list[dict[str, Any] | str] = Field(default_factory=list)


class ResolutionCreate(BaseModel):
    realised_pnl: float | None = None
    maximum_favourable_excursion: float | None = None
    maximum_adverse_excursion: float | None = None
    fees: float | None = None
    swap: float | None = None
    exit_reason: str | None = None
    notes: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "execution_mode": settings.execution_mode, "database": str(settings.database_path), "mt5": bridge.health()}

@app.get("/account")
def account() -> dict[str, Any]:
    try:
        bridge.connect()
        return bridge.account()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

@app.get("/positions")
def positions() -> list[dict[str, Any]]:
    try:
        bridge.connect()
        return bridge.positions()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

@app.get("/tick/{symbol}")
def tick(symbol: str) -> dict[str, Any]:
    try:
        bridge.connect()
        return bridge.tick(symbol.upper())
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

@app.get("/decisions")
def decisions(limit: int = 100) -> list[dict[str, Any]]:
    return ledger.list_decisions(limit)

@app.get("/decisions/{decision_id}")
def decision(decision_id: str) -> dict[str, Any]:
    item = ledger.get_decision(decision_id)
    if not item:
        raise HTTPException(status_code=404, detail="Decision not found")
    return item

@app.post("/decisions")
def create_decision(payload: DecisionCreate) -> dict[str, Any]:
    return ledger.create_decision(payload.model_dump())

@app.post("/decisions/{decision_id}/execute")
def execute_decision(decision_id: str) -> dict[str, Any]:
    item = ledger.get_decision(decision_id)
    if not item:
        raise HTTPException(status_code=404, detail="Decision not found")
    if item["action"] == "HOLD" or settings.execution_mode == "shadow":
        return ledger.mark_shadow(decision_id)
    try:
        bridge.connect()
        result = bridge.place_market_order(
            symbol=item["symbol"], action=item["action"], volume=item["volume"],
            stop_loss=item["stop_loss"], take_profit=item["take_profit"], comment=decision_id
        )
        ticket = result.get("order") or result.get("deal")
        if not ticket:
            raise RuntimeError("MT5 returned success without an order/deal ticket.")
        return ledger.mark_execution(decision_id, ticket=int(ticket), fill_price=result.get("price"))
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

@app.post("/decisions/{decision_id}/resolve")
def resolve_decision(decision_id: str, payload: ResolutionCreate) -> dict[str, Any]:
    if not ledger.get_decision(decision_id):
        raise HTTPException(status_code=404, detail="Decision not found")
    return ledger.resolve(decision_id, payload.model_dump())
