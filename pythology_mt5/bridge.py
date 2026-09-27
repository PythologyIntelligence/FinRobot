from __future__ import annotations

from typing import Any

from .config import Settings


class MT5Bridge:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._mt5 = None

    def _module(self):
        if self._mt5 is None:
            try:
                import MetaTrader5 as mt5
            except ImportError as exc:
                raise RuntimeError("MetaTrader5 Python package is not installed on this host.") from exc
            self._mt5 = mt5
        return self._mt5

    def connect(self) -> None:
        mt5 = self._module()
        kwargs: dict[str, Any] = {}
        if self.settings.mt5_terminal_path:
            kwargs["path"] = self.settings.mt5_terminal_path
        if self.settings.mt5_login is not None:
            kwargs["login"] = self.settings.mt5_login
        if self.settings.mt5_password:
            kwargs["password"] = self.settings.mt5_password
        if self.settings.mt5_server:
            kwargs["server"] = self.settings.mt5_server
        if not mt5.initialize(**kwargs):
            raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")

    def shutdown(self) -> None:
        if self._mt5 is not None:
            self._mt5.shutdown()

    def health(self) -> dict[str, Any]:
        try:
            self.connect()
            account = self.account()
            return {
                "ok": True,
                "connected": True,
                "trade_mode": account.get("trade_mode"),
                "is_demo": account.get("is_demo"),
                "login": account.get("login"),
                "server": account.get("server"),
            }
        except Exception as exc:
            return {"ok": False, "connected": False, "error": str(exc)}

    def account(self) -> dict[str, Any]:
        mt5 = self._module()
        info = mt5.account_info()
        if info is None:
            raise RuntimeError(f"MT5 account_info failed: {mt5.last_error()}")
        data = info._asdict()
        demo_constant = getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", 0)
        return {
            "login": data.get("login"),
            "server": data.get("server"),
            "currency": data.get("currency"),
            "balance": data.get("balance"),
            "equity": data.get("equity"),
            "margin": data.get("margin"),
            "margin_free": data.get("margin_free"),
            "profit": data.get("profit"),
            "trade_mode": data.get("trade_mode"),
            "is_demo": data.get("trade_mode") == demo_constant,
        }

    def positions(self) -> list[dict[str, Any]]:
        mt5 = self._module()
        positions = mt5.positions_get()
        if positions is None:
            raise RuntimeError(f"MT5 positions_get failed: {mt5.last_error()}")
        return [p._asdict() for p in positions]

    def tick(self, symbol: str) -> dict[str, Any]:
        mt5 = self._module()
        if not mt5.symbol_select(symbol, True):
            raise RuntimeError(f"MT5 could not select symbol {symbol}")
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(f"MT5 tick unavailable for {symbol}: {mt5.last_error()}")
        return tick._asdict()

    def _assert_demo_account(self) -> None:
        account = self.account()
        if not account["is_demo"]:
            raise RuntimeError(
                "Order blocked: this FinRobot integration only permits MT5 demo accounts. "
                "Real-money execution is intentionally not implemented."
            )

    def place_market_order(self, *, symbol: str, action: str, volume: float,
                           stop_loss: float | None = None, take_profit: float | None = None,
                           comment: str = "FinRobot demo") -> dict[str, Any]:
        if self.settings.execution_mode != "demo":
            raise RuntimeError("Order blocked: execution mode is not demo.")
        self._assert_demo_account()
        mt5 = self._module()
        if not mt5.symbol_select(symbol, True):
            raise RuntimeError(f"MT5 could not select symbol {symbol}")
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise RuntimeError(f"MT5 tick unavailable for {symbol}")
        normalized_action = action.upper()
        if normalized_action == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        elif normalized_action == "SELL":
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            raise ValueError("Only BUY or SELL decisions can be executed.")
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type,
            "price": price,
            "sl": float(stop_loss or 0.0),
            "tp": float(take_profit or 0.0),
            "deviation": 20,
            "magic": 260927,
            "comment": comment[:31],
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result is None:
            raise RuntimeError(f"MT5 order_send returned no result: {mt5.last_error()}")
        data = result._asdict()
        success_codes = {
            getattr(mt5, "TRADE_RETCODE_DONE", -1),
            getattr(mt5, "TRADE_RETCODE_PLACED", -2),
            getattr(mt5, "TRADE_RETCODE_DONE_PARTIAL", -3),
        }
        if data.get("retcode") not in success_codes:
            raise RuntimeError(
                f"MT5 rejected order: retcode={data.get('retcode')} comment={data.get('comment')}"
            )
        return data
