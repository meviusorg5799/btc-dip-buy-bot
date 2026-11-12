# Strategy

## Idea

One-minute BTC bars are noisy: a 1-minute move has a ~5 bps standard
deviation while a full-size round trip costs ~26 bps in fees, slippage and
price impact. Chasing every fast signal bleeds on whipsaws (fast EMA
crosses lost $65–$147 on the dev window; Donchian breakouts lost $25–$97).
The trade that works on this data is the patient one: buy a clear dip
after the market has already shown it can bounce, take a modest profit,
and stay out of a grinding downtrend.

## Rules

All decisions use the bar close only. All comparisons are integer
cross-multiplications except the two log returns, which are deterministic
functions of the closes.

**Entry (flat only):**
- The close is at least 0.5% below the highest close of the previous
  60 bars, AND the 10-minute log return is above +0.05% (bounce
  confirmation).
- The first entry of the window is taken on that signal alone. Later
  entries additionally require the 240-minute log return to be positive
  (only buy dips while the 4-hour trend is up) and a 60-bar cooldown
  after an exit.
- At most 3 entries per window. Every buy spends all available cash
  (up to 100% of equity, the cap).

**Exits (while holding):**
- Stop-loss: close 0.3% below the entry close.
- Trailing stop: close 0.8% below the highest close since entry.
- Take-profit: position value reaches 1.008x its cost.
- Every sell sells the whole position. `max_slippage_bps` is 100 on all
  orders (a fill is ~10 bps: 2 fee + 2 slippage + ~8 impact on ~$1.27M
  depth).

**Safety:** a buy that never appears as a position on the next batch
(rejected for slippage / no bar) is rolled back and does not count as an
entry. Warm-up batches are never traded. No clock, no environment, no
randomness, no network, no files — two runs on the same data produce the
same orders byte for byte.

## Why this shape

Tested on the published dev window (1,439 bars, price $73,739 → $72,044,
-2.33% with an early rally to $74,689):
- The bot buys the dip after the first rally peak (bar 79, fill $73,987)
  and sells at the take-profit (bar 160, fill $74,660): **+$7.43**.
- The trend gate then blocks every re-entry in the long grind down, so
  the bot keeps the profit instead of giving it back on falling knives
  (ungated re-entries lost $5–$12 on the same window).
- Neighbouring parameters give the same sign (dip 0.4–0.5%, take-profit
  0.7–0.8%, stop 0.2–0.4% all pass the gate), so the result is a plateau,
  not a single lucky point.

## Dev-window result

- Net PnL: **+$7.43** (above the dev gate of > $0)
- Trades: 1 round trip (2 fills)
- Max drawdown: 0.30%
- Sub-window PnL (6h blocks): +$7.43 / $0 / $0 / $0

The dev window decides only who races; the race window alone decides the
ranking. This bot's edge on an unseen window is the same discipline:
buy dips that bounce, take the profit, and refuse to buy dips in a
downtrend.
