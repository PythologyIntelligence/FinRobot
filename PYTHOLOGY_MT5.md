# Pythology FinRobot MT5 Experiment

This branch turns the upstream FinRobot fork into a controlled Pythology trading-research experiment.

## Safety model

The first version has only two execution modes:

- `shadow`: decisions are recorded, but no order is sent.
- `demo`: orders may be sent only when MetaTrader 5 reports that the connected account is a demo account.

There is intentionally **no real-money execution mode**. Adding one later should be a separate reviewed change after the experiment has accumulated enough evidence.

## Components

- Existing FinRobot web application: primary UI.
- `pythology_mt5`: local MT5 bridge and decision ledger.
- SQLite ledger: `C:\Pythology\FinRobot\runtime\finrobot_mt5.sqlite3` by default.
- MT5 sidecar API: `http://127.0.0.1:8011` by default.

Useful endpoints:

- `GET /health`
- `GET /account`
- `GET /positions`
- `GET /tick/{symbol}`
- `POST /decisions`
- `POST /decisions/{decision_id}/execute`
- `POST /decisions/{decision_id}/resolve`

Every FinRobot trade hypothesis should be written to the ledger before execution, including confidence, thesis, market snapshot, sources, requested entry, stop, target and volume.

## VPS target

Recommended layout:

    C:\Pythology\FinRobot
      .venv\
      runtime\
        finrobot_mt5.sqlite3
        logs\

The public hostname can reverse-proxy the existing FinRobot web interface:

    finrobot.pythology.co.nz -> 127.0.0.1:8001

Keep the MT5 sidecar bound to localhost unless a later integration requires otherwise.

## Installation

1. Clone the Pythology fork onto the Windows VPS.
2. Check out `feature/pythology-mt5-experiment`.
3. Put MT5 connection values into the VPS environment/secret store; do not commit credentials.
4. Run the Windows installer script.
5. Start the `Pythology FinRobot` scheduled task.
6. Verify `http://127.0.0.1:8011/health`.

## Promotion path

Shadow -> Demo -> evidence review -> explicit future real-money implementation.

Promotion should be based on the ledger: P&L, drawdown, slippage, profit factor, expectancy, confidence calibration, instrument/timeframe performance, market-regime performance, and the outcomes of rejected/skipped decisions.
