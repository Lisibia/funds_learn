from dataclasses import dataclass, field


@dataclass
class Transaction:
    date: object
    fund_code: str
    action: str
    units: float
    price: float
    value: float
    commission: float


@dataclass
class PortfolioResult:
    strategy_name: str
    portfolio: 'Portfolio'


@dataclass
class Portfolio:
    initial_cash: float
    purchase_rate: float
    redeem_rate: float
    cash: float = field(init=False)
    holdings: dict = field(default_factory=dict)
    transactions: list = field(default_factory=list)
    values: list = field(default_factory=list)
    dates: list = field(default_factory=list)
    holdings_history: dict = field(default_factory=dict)
    price_history: dict = field(default_factory=dict)

    def __post_init__(self):
        self.cash = self.initial_cash

    def buy(self, date, fund_code, amount, price):
        if amount <= 0 or price <= 0:
            return
        net_amount = amount / (1 + self.purchase_rate)
        commission = amount - net_amount
        units = round(net_amount / price, 2)
        value = units * price
        total_cost = value + commission
        if units <= 0 or total_cost > self.cash + 1e-8:
            return
        self.holdings[fund_code] = self.holdings.get(fund_code, 0.0) + units
        self.cash -= total_cost
        self.transactions.append(Transaction(date, fund_code, 'BUY', units, price, value, commission))

    def sell(self, date, fund_code, units, price):
        current_units = round(self.holdings.get(fund_code, 0.0), 2)
        units = min(round(units, 2), current_units)
        if units <= 0 or price <= 0:
            return
        value = units * price
        commission = value * self.redeem_rate
        self.holdings[fund_code] = current_units - units
        if self.holdings[fund_code] <= 1e-8:
            self.holdings.pop(fund_code, None)
        self.cash += value - commission
        self.transactions.append(Transaction(date, fund_code, 'SELL', units, price, value, commission))

    def calculate_total_value(self, prices):
        holdings_value = sum(self.holdings.get(code, 0.0) * prices.get(code, 0.0) for code in set(self.holdings))
        return self.cash + holdings_value

    def get_current_weights(self, prices):
        total_value = self.calculate_total_value(prices)
        if total_value <= 0:
            return {}
        return {
            code: (units * prices.get(code, 0.0)) / total_value
            for code, units in self.holdings.items()
            if prices.get(code, 0.0) > 0
        }

    def record_daily(self, date, prices):
        self.dates.append(date)
        self.values.append(self.calculate_total_value(prices))
        self.holdings_history[date] = self.holdings.copy()
        self.price_history[date] = prices.copy()
