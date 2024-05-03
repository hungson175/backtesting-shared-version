import numpy as np
import pandas as pd
import utils
from strategies import trade_strategy
from strategies.trade_strategy import TradeStrategy


class SMA_Dual_LS(TradeStrategy):
    def __init__(self, data: pd.DataFrame, ls: int,
                 slow_ma_period: int, fast_ma_period: int,
                 entry_pct: float, tolerance_pct: float,
                 start_balance: int = trade_strategy.START_BALANCE):
        TradeStrategy.__init__(self, data=data, start_balance=start_balance)
        self.ls = ls
        self.slow_ma_period = slow_ma_period
        self.fast_ma_period = fast_ma_period
        self.entry_pct = entry_pct
        self.tolerance_pct = tolerance_pct

        self.slow_ma = self.df["close"].rolling(self.slow_ma_period).mean()
        self.fast_ma = self.df["close"].rolling(self.fast_ma_period).mean()

    def backtest(self):
        n = len(self.close_price)
        for i in range(0, n):
            price_cut_slow_sma = self._price_cut_sma(i, self.slow_ma)
            price_cut_fast_sma = self._price_cut_sma(i, self.fast_ma)

            if (price_cut_fast_sma and
                    ((self.ls == 1 and self.trade_side == 1 and self.close_price[i] < self.fast_ma[i] * (
                            1 - self.tolerance_pct)) or
                     (self.ls == -1 and self.trade_side == -1 and self.close_price[i] > self.fast_ma[i] * (
                             1 + self.tolerance_pct))
                    )
            ):
                self._close_trade(i)

            if self.trade_side == 0 and price_cut_slow_sma:
                if self.ls == 1 and self.close_price[i] > self.slow_ma[i] * (1 + self.entry_pct):
                    self.trade_side = 1
                if self.ls == -1 and self.close_price[i] < self.slow_ma[i] * (1 - self.entry_pct):
                    self.trade_side = -1
                self.entry_price = self.close_price[i]
                self.entry_time = self.timestamp[i]

            self.max_pnl = max(self.max_pnl, self.pnl)
            self.max_dd = max(self.max_dd, self.max_pnl - self.pnl)
        if self.trade_side != 0:
            self._close_trade(n - 1)
        return self.pnl, self.max_dd, self.trades
