from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DecisionLedger:
    def __init__(self, database_path: Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.database_path)
        con.row_factory = sqlite3.Row
        return con

    def _init_schema(self) -> None:
        with self._connect() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    decision_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    thesis TEXT NOT NULL,
                    requested_entry REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    volume REAL NOT NULL,
                    market_snapshot_json TEXT NOT NULL,
                    sources_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    mt5_ticket INTEGER,
                    fill_price REAL,
                    executed_at TEXT,
                    resolution_json TEXT
                )
            """)
            con.execute("CREATE INDEX IF NOT EXISTS idx_decisions_created_at ON decisions(created_at DESC)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_decisions_symbol ON decisions(symbol, created_at DESC)")

    def create_decision(self, payload: dict[str, Any]) -> dict[str, Any]:
        decision_id = payload.get("decision_id") or f"FR-{uuid.uuid4().hex[:12].upper()}"
        row = {
            "decision_id": decision_id,
            "created_at": utc_now(),
            "symbol": payload["symbol"].upper(),
            "action": payload["action"].upper(),
            "confidence": float(payload["confidence"]),
            "thesis": payload["thesis"],
            "requested_entry": payload.get("requested_entry"),
            "stop_loss": payload.get("stop_loss"),
            "take_profit": payload.get("take_profit"),
            "volume": float(payload["volume"]),
            "market_snapshot_json": json.dumps(payload.get("market_snapshot", {}), sort_keys=True),
            "sources_json": json.dumps(payload.get("sources", []), sort_keys=True),
            "status": "PROPOSED",
        }
        with self._connect() as con:
            con.execute("""
                INSERT INTO decisions (decision_id, created_at, symbol, action, confidence, thesis,
                    requested_entry, stop_loss, take_profit, volume, market_snapshot_json, sources_json, status)
                VALUES (:decision_id, :created_at, :symbol, :action, :confidence, :thesis,
                    :requested_entry, :stop_loss, :take_profit, :volume, :market_snapshot_json, :sources_json, :status)
            """, row)
        return self.get_decision(decision_id)

    def get_decision(self, decision_id: str) -> dict[str, Any] | None:
        with self._connect() as con:
            row = con.execute("SELECT * FROM decisions WHERE decision_id = ?", (decision_id,)).fetchone()
        return self._decode(row) if row else None

    def list_decisions(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 1000))
        with self._connect() as con:
            rows = con.execute("SELECT * FROM decisions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._decode(row) for row in rows]

    def mark_shadow(self, decision_id: str) -> dict[str, Any]:
        with self._connect() as con:
            con.execute("UPDATE decisions SET status = ? WHERE decision_id = ?", ("SHADOW", decision_id))
        return self.get_decision(decision_id)

    def mark_execution(self, decision_id: str, ticket: int, fill_price: float | None) -> dict[str, Any]:
        with self._connect() as con:
            con.execute("UPDATE decisions SET status = ?, mt5_ticket = ?, fill_price = ?, executed_at = ? WHERE decision_id = ?",
                        ("EXECUTED_DEMO", int(ticket), fill_price, utc_now(), decision_id))
        return self.get_decision(decision_id)

    def resolve(self, decision_id: str, resolution: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as con:
            con.execute("UPDATE decisions SET status = ?, resolution_json = ? WHERE decision_id = ?",
                        ("RESOLVED", json.dumps(resolution, sort_keys=True), decision_id))
        return self.get_decision(decision_id)

    @staticmethod
    def _decode(row: sqlite3.Row) -> dict[str, Any]:
        out = dict(row)
        out["market_snapshot"] = json.loads(out.pop("market_snapshot_json") or "{}")
        out["sources"] = json.loads(out.pop("sources_json") or "[]")
        raw_resolution = out.pop("resolution_json")
        out["resolution"] = json.loads(raw_resolution) if raw_resolution else None
        return out
