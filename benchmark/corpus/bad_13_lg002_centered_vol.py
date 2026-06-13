# "Smoother" annualized volatility — the centered window peeks 10 bars ahead.
import numpy as np
import pandas as pd

bars = pd.read_parquet("bars.parquet")
rets = bars["close"].pct_change()

bars["vol_21"] = rets.rolling(21, center=True).std() * np.sqrt(252)
bars["vol_regime"] = bars["vol_21"] > bars["vol_21"].rolling(252).mean()
