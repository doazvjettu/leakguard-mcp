def to_bars(ticks):
    bars = ticks.resample("5min").last()   # bar stamped at left edge
    ohlc = ticks.resample("1h").ohlc()
    return bars, ohlc
