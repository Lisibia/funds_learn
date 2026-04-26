from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    name = 'base'

    def __init__(self):
        self._initialized_codes = set()

    @abstractmethod
    def on_init(self, date, prices, portfolio, initial_amounts):
        raise NotImplementedError

    def on_day(self, date, prices, portfolio):
        return

    def _buy_pending_funds(self, date, prices, portfolio, initial_amounts):
        for fund_code, amount in initial_amounts.items():
            if fund_code in self._initialized_codes:
                continue
            price = prices.get(fund_code)
            if price is None or amount <= 0:
                continue
            portfolio.buy(date, fund_code, amount, price)
            if portfolio.holdings.get(fund_code, 0.0) > 0:
                self._initialized_codes.add(fund_code)


class BuyHoldStrategy(BaseStrategy):
    name = 'buy_hold'

    def __init__(self):
        super().__init__()
        self._initial_amounts = {}

    def on_init(self, date, prices, portfolio, initial_amounts):
        self._initial_amounts = initial_amounts
        self._buy_pending_funds(date, prices, portfolio, initial_amounts)

    def on_day(self, date, prices, portfolio):
        self._buy_pending_funds(date, prices, portfolio, self._initial_amounts)


class RebalanceStrategy(BaseStrategy):
    name = 'rebalance'

    def __init__(self, target_weights, threshold, frequency):
        super().__init__()
        self.target_weights = target_weights
        self.threshold = threshold
        self.frequency = frequency
        self._last_rebalance_period = None
        self._initial_amounts = {}

    def on_init(self, date, prices, portfolio, initial_amounts):
        self._initial_amounts = initial_amounts
        self._buy_pending_funds(date, prices, portfolio, initial_amounts)
        self._last_rebalance_period = self._get_period_key(date)

    def on_day(self, date, prices, portfolio):
        self._buy_pending_funds(date, prices, portfolio, self._initial_amounts)
        if not self._should_check(date):
            return
        current_weights = portfolio.get_current_weights(prices)
        if not current_weights:
            return
        if not any(abs(current_weights.get(code, 0.0) - target) > self.threshold for code, target in self.target_weights.items()):
            return
        total_value = portfolio.calculate_total_value(prices)
        target_values = {code: total_value * weight for code, weight in self.target_weights.items()}
        for code, units in list(portfolio.holdings.items()):
            if code not in prices:
                continue
            current_value = units * prices.get(code, 0.0)
            target_value = target_values.get(code, 0.0)
            if current_value > target_value:
                sell_units = (current_value - target_value) / prices[code]
                portfolio.sell(date, code, sell_units, prices[code])
        for code, target_value in target_values.items():
            if code not in prices:
                continue
            current_value = portfolio.holdings.get(code, 0.0) * prices.get(code, 0.0)
            if target_value > current_value and portfolio.cash > 1:
                buy_amount = min(target_value - current_value, portfolio.cash)
                portfolio.buy(date, code, buy_amount, prices[code])
        self._last_rebalance_period = self._get_period_key(date)

    def _should_check(self, date):
        period_key = self._get_period_key(date)
        if self.frequency == 'daily':
            return True
        if period_key != self._last_rebalance_period:
            return True
        return False

    def _get_period_key(self, date):
        if self.frequency == 'quarterly':
            return (date.year, (date.month - 1) // 3 + 1)
        if self.frequency == 'monthly':
            return (date.year, date.month)
        return date


class StrategyFactory:
    @staticmethod
    def create(strategy_name, rebalance_config):
        if strategy_name == 'buy_hold':
            return BuyHoldStrategy()
        if strategy_name == 'rebalance':
            return RebalanceStrategy(
                target_weights=rebalance_config['target_weights'],
                threshold=rebalance_config['threshold'],
                frequency=rebalance_config['frequency'],
            )
        raise ValueError(f'Unknown strategy: {strategy_name}')
