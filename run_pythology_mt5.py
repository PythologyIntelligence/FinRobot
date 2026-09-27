from __future__ import annotations

import uvicorn

from pythology_mt5.config import settings


if __name__ == "__main__":
    uvicorn.run("pythology_mt5.api:app", host=settings.host, port=settings.port, reload=False, access_log=True)
