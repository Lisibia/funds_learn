import pandas as pd

from .models import Portfolio, PortfolioResult


class BacktestEngine:
    def run(self, strategy, nav_df, initial_amounts, fees):
        portfolio = Portfolio(
            initial_cash=sum(initial_amounts.values()),
            purchase_rate=fees['purchase_rate'],
            redeem_rate=fees['redeem_rate'],
        )
        dates = nav_df.index
        for index, date in enumerate(dates):
            prices = {
                code: float(nav_df.loc[date, code])
                for code in nav_df.columns
                if not pd.isna(nav_df.loc[date, code])
            }
            if index == 0:
                strategy.on_init(date, prices, portfolio, initial_amounts)
            else:
                strategy.on_day(date, prices, portfolio)
            portfolio.record_daily(date, prices)
        return PortfolioResult(strategy_name=strategy.name, portfolio=portfolio)
