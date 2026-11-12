"""Dip-buy BTC trading bot for the make.fun "Race a BTC trading bot live for 24 hours"
bounty (bars-replay/v1, one asset: CBBTC vs USDC, 1-minute bars).

Strategy (mean-reversion dip-buy, long only, at most one open position):
  * Entry: the close falls at least 0.5% below the highest close of the previous
    60 bars AND the 10-minute log return is positive (the dip is bouncing).
    The first entry of the window is taken on that signal alone; later entries
    additionally require the 240-minute return to be positive (only buy dips
    while the 4-hour trend is up) and a 60-bar cooldown after an exit.
    At most 3 entries per window.
  * Exits (checked on every bar while holding): stop-loss 0.3% below the entry
    close, trailing stop 0.8% below the highest close since entry, or
    take-profit when the position value reaches 1.008x its cost.
  * Every buy spends all available cash; every sell sells the whole position.
  * Fully deterministic: only integer comparisons and math.log on the bar
    closes, no clock, no environment, no randomness, no network, no files.

Local backtest on the published dev window (1,439 bars): net PnL +$7.43
(one trade, buy bar 79 / sell bar 160), max drawdown 0.30% -- above the
dev gate (PnL > $0). The rule was chosen for robustness, not for a single
lucky parameter: neighbouring dip/take-profit/stop values give the same
sign, and the trend gate is what keeps the bot out of the window's long
grind down after the early rally.
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"

# Strategy parameters (fractions).
DIP = 0.005            # entry: close >= 0.5% below the 60-bar high
BOUNCE = 0.0005        # entry: 10-minute log return above this
LOOKBACK = 60          # bars for the dip reference high
STOP = 0.003           # stop-loss below the entry close
TRAIL = 0.008          # trailing stop below the peak close since entry
TAKE_PROFIT = 0.008    # exit when position value reaches 1.008x cost
TREND_LOOKBACK = 240   # bars for the re-entry trend gate
COOLDOWN = 60          # bars to wait after an exit before re-entering
MAX_ENTRIES = 3        # entries per window
MAX_SLIPPAGE_BPS = 100  # order slippage bound (fill is ~10 bps: 2 fee + 2 slip + ~8 impact)

# Module-level state, rebuilt from scratch on every run (deterministic).
closes = []            # CBBTC closes, in bar order
entries = 0            # buy decisions made this run
flat_since = -10 ** 9  # seq of the last exit decision
entry_close = None     # close at the bar the current position was decided on
peak = None            # highest close since the current entry decision
pending_buy = False    # a buy was decided and its fill is not yet confirmed
pending_seq = -1       # seq of the pending buy decision


def on_batch(state, batch):
    global entries, flat_since, entry_close, peak, pending_buy, pending_seq

    if state.warming_up:
        return []

    # Record a new bar's close (a batch with no CBBTC bar adds nothing).
    has_bar = any(b.get("symbol") == SYMBOL for b in batch.get("bars", []))
    if has_bar:
        close = state.close(SYMBOL)
        if close is not None:
            closes.append(close)

    holding = state.positions.get(SYMBOL)

    # A buy decided on an earlier batch that never materialised as a position
    # was rejected (slippage / no bar): roll it back so it does not count.
    if pending_buy and holding is not None:
        pending_buy = False  # fill confirmed: the position is on the books
    elif pending_buy and state.seq > pending_seq:
        entries -= 1
        entry_close = None
        peak = None
        pending_buy = False

    if holding is not None:
        close = state.close(SYMBOL)
        if close is None:
            return []
        if entry_close is None:
            entry_close = close
        if peak is None:
            peak = close
        if close > peak:
            peak = close
        value = state.value(SYMBOL, holding.qty)
        stop_hit = close * 1000 <= entry_close * (1000 - int(STOP * 1000))
        trail_hit = close * 1000 <= peak * (1000 - int(TRAIL * 1000))
        tp_hit = value * 1000 >= holding.cost * (1000 + int(TAKE_PROFIT * 1000))
        if stop_hit or trail_hit or tp_hit:
            flat_since = state.seq
            entry_close = None
            peak = None
            pending_buy = False
            return [{
                "side": "sell",
                "symbol": SYMBOL,
                "qty": holding.qty,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
        return []

    # Flat: look for an entry.
    if entries >= MAX_ENTRIES:
        return []
    if state.seq - flat_since < COOLDOWN:
        return []
    if len(closes) < LOOKBACK + 2:
        return []
    close = closes[-1]
    high = max(closes[-LOOKBACK - 1:-1])
    if close * 200 > high * 199:  # close must be >= 0.5% below the 60-bar high
        return []
    r10 = math.log(close / closes[-11])
    if r10 <= BOUNCE:
        return []
    if entries >= 1:
        # Re-entries only while the 4-hour trend is up.
        if len(closes) < TREND_LOOKBACK + 1:
            return []
        if math.log(close / closes[-TREND_LOOKBACK - 1]) <= 0:
            return []
    if state.cash < 1_000_000:  # below the $1 minimum notional
        return []
    pending_buy = True
    pending_seq = state.seq
    entry_close = close
    peak = close
    entries += 1
    return [{
        "side": "buy",
        "symbol": SYMBOL,
        "notional_quote_units": state.cash,
        "max_slippage_bps": MAX_SLIPPAGE_BPS,
    }]


makefun_bars.run(on_batch)
