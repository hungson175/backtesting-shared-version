import numpy as np
import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", 1000)
pd.set_option("display.width", 1000)


def backtest(df: pd.DataFrame, ma_period: int):
    df["obv"] = (np.sign(df["close"].diff()) * df["volume"]).fillna(0).cumsum()
    df["obv_ma"] = round(df["obv"].rolling(window=ma_period).mean(), 2)
    # TODO: how built-in function like round implemented ? Read it, the performance of the code depends on this

    df["signal"] = np.where(df["obv"] > df["obv_ma"], 1, -1)

    df["close_change"] = df["close"].pct_change()
    df["signal_shift"] = df["signal"].shift(1)
    df["pnl"] = df["close"].pct_change() * df["signal"].shift(1)

    df["cum_pnl"] = df["pnl"].cumsum()
    df["max_cum_pnl"] = df["cum_pnl"].cummax()
    df["drawndown"] = df["max_cum_pnl"] - df["cum_pnl"]

    # print(df)

    return df["pnl"].sum(), df["drawndown"].max()
