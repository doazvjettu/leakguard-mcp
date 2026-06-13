# Left-labeled minute bars used as features: each row is stamped BEFORE the
# data inside the bar existed.
import pandas as pd

ticks = pd.read_parquet("ticks.parquet").set_index("ts")

bars = ticks["price"].resample("1min").mean()
features = bars.to_frame("px_1m")
features["px_change"] = features["px_1m"].pct_change()
