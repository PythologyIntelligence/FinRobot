from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("FINROBOT_MT5_HOST", "127.0.0.1")
    port: int = int(os.getenv("FINROBOT_MT5_PORT", "8011"))
    database_path: Path = Path(
        os.getenv("FINROBOT_MT5_DATABASE", r"C:\\Pythology\\FinRobot\\runtime\\finrobot_mt5.sqlite3")
    )
    execution_mode: str = os.getenv("FINROBOT_MT5_EXECUTION_MODE", "shadow").strip().lower()
    mt5_terminal_path: str | None = os.getenv("FINROBOT_MT5_TERMINAL_PATH") or None
    mt5_login: int | None = int(os.environ["FINROBOT_MT5_LOGIN"]) if os.getenv("FINROBOT_MT5_LOGIN") else None
    mt5_password: str | None = os.getenv("FINROBOT_MT5_PASSWORD") or None
    mt5_server: str | None = os.getenv("FINROBOT_MT5_SERVER") or None

    def validate(self) -> None:
        if self.execution_mode not in {"shadow", "demo"}:
            raise ValueError(
                "FINROBOT_MT5_EXECUTION_MODE must be shadow or demo. "
                "Real-money execution is intentionally not implemented."
            )


settings = Settings()
settings.validate()
