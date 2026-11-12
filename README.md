# BTC Dip-Buy Bot

Entry for the make.fun bounty **"Race a BTC trading bot live for 24 hours"**
(`btc-race-24h-20261112-1439`, bars-replay/v1).

A mean-reversion dip-buy bot for CBBTC/USDC on 1-minute bars. It buys a
0.5% dip below the 60-bar high once the 10-minute return turns positive,
and exits on a 0.3% stop-loss, a 0.8% trailing stop, or a 0.8% take-profit.
Later entries additionally require the 4-hour trend to be up. Long only,
at most one open position, fully deterministic (Python 3.13 stdlib only).

See [STRATEGY.md](STRATEGY.md) for the full rules and the dev-window result.

## Run

```sh
python3 -P -s main.py
```

The bot speaks `agent-fun/bars-replay/v1` (newline-delimited JSON on stdin /
stdout) through the vendored kit shim in `vendor/makefun_bars.py` (a
byte-for-byte copy of the kit's Python SDK shim).

## Files

- `main.py` — the bot (repo root, as the bounty requires)
- `vendor/makefun_bars.py` — the kit's Python SDK shim, copied unchanged
- `STRATEGY.md` — strategy rules and dev-window backtest result
- `LICENSE` — MIT

## Dev-window result (local, kit `grade-local`)

Net PnL **+$7.43** on the published 24-hour dev window (one trade), max
drawdown 0.30% — above the dev gate (PnL > $0), so the entry qualifies to
race.
