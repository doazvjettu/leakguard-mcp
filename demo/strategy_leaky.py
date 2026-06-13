"""Mean-reversion strategy: build features, scale, split, train.

Looks reasonable. Ships three lookahead leaks that backtest beautifully and lose
money live. leakguard flags all three before the backtest ever runs.
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

FEATURES = ["ret_1d", "vol_20d", "rsi_14", "fwd_return"]


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df["ret_1d"] = df["close"].pct_change()
    df["vol_20d"] = df["ret_1d"].rolling(20).std()
    df["rsi_14"] = compute_rsi(df["close"], window=14)

    # Predictive "momentum" signal — actually tomorrow's move leaking into today.
    df["fwd_return"] = df["close"].shift(-5) / df["close"] - 1

    # Intraday gaps left some bars empty; patch them up.
    df = df.fillna(method="bfill")
    return df


def prepare_training_data(df: pd.DataFrame):
    df = build_features(df)

    # Standardize every feature so the model trains on comparable scales.
    scaler = StandardScaler()
    X = scaler.fit_transform(df[FEATURES])
    y = (df["fwd_return"] > 0).astype(int)

    # Time-ordered split (good!) — but the scaler above already saw the test rows.
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    return X_train, X_test, y_train, y_test


def compute_rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = -delta.clip(upper=0).rolling(window).mean()
    rs = gain / loss
    return 100 - 100 / (1 + rs)
