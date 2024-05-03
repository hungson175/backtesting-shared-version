from typing import Tuple, List, Any

import numpy as np
import pandas as pd

import utils
from strategies import trade_strategy
from strategies.trade_strategy import TradeStrategy


class SingleMALong(TradeStrategy):
    def __init__(self,
                 data: pd.DataFrame,
                 ma_period: int,
                 entry_pct: float, tolerance_pct: float,
                 start_balance: int = trade_strategy.START_BALANCE):
        TradeStrategy.__init__(self, data=data, start_balance=start_balance)
        self.ma_period = ma_period
        self.entry_pct = entry_pct
        self.tolerance_pct = tolerance_pct

    def backtest(self) -> Tuple[float, float, List[Any]]:

        n = len(self.df)
        ma = self.df["close"].rolling(self.ma_period).mean()
        for i in range(0, n):
            current_price = self.close_price[i]
            price_cut_ma = self._price_cut_sma(i, ma)
            if self.trade_side == 0 and price_cut_ma and current_price > ma[i] * (1 + self.entry_pct):
                self.trade_side = 1
                self.entry_price = current_price
                self.entry_time = self.timestamp[i]
            elif self.trade_side == 1 and price_cut_ma and current_price < ma[i] * (1 - self.tolerance_pct):
                self._close_trade(i)
                self.max_pnl = max(self.max_pnl, self.pnl)
                self.max_dd = max(self.max_dd, self.max_pnl - self.pnl)

        if self.trade_side != 0:
            self._close_trade(n - 1)
            self.max_pnl = max(self.max_pnl, self.pnl)
            self.max_dd = max(self.max_dd, self.max_pnl - self.pnl)

        return self.pnl, self.max_dd, self.trades


