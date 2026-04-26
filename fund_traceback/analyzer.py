import matplotlib.pyplot as plt
import numpy as np


plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Songti SC', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


class PerformanceAnalyzer:
    def __init__(self, result, fund_names):
        self.result = result
        self.fund_names = fund_names
        self.risk_free_rate = 0.03

    def calculate_metrics(self):
        portfolio = self.result.portfolio
        if not portfolio.values:
            return None
        values = np.array(portfolio.values)
        initial_value = portfolio.initial_cash
        final_value = values[-1]
        total_return = (final_value - initial_value) / initial_value
        total_days = len(values)
        years = total_days / 252
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else total_return
        daily_returns = np.diff(values) / values[:-1] if len(values) > 1 else np.array([])
        sharpe_ratio = 0
        if len(daily_returns) > 0 and np.std(daily_returns) > 0:
            risk_free_daily = self.risk_free_rate / 252
            sharpe_ratio = (np.mean(daily_returns) - risk_free_daily) / np.std(daily_returns) * np.sqrt(252)
        peak = values[0]
        max_drawdown = 0
        for value in values:
            peak = max(peak, value)
            max_drawdown = max(max_drawdown, (peak - value) / peak)
        return {
            'initial_value': initial_value,
            'final_value': final_value,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
        }

    def print_report(self):
        metrics = self.calculate_metrics()
        if not metrics:
            print('没有足够的有效数据进行绩效分析')
            return
        portfolio = self.result.portfolio
        print('\n' + '=' * 70)
        print('基金组合回测报告')
        print('=' * 70)
        print(f"策略: {self.result.strategy_name}")
        print(f"回测期间: {portfolio.dates[0].strftime('%Y-%m-%d')} 至 {portfolio.dates[-1].strftime('%Y-%m-%d')}")
        print(f"初始资金: {metrics['initial_value']:,.2f}")
        print(f"最终资金: {metrics['final_value']:,.2f}")
        print(f"总收益率: {metrics['total_return']:.2%}")
        print(f"年化收益率: {metrics['annual_return']:.2%}")
        print(f"夏普比率: {metrics['sharpe_ratio']:.2f}")
        print(f"最大回撤: {metrics['max_drawdown']:.2%}")
        total_commission = sum(item.commission for item in portfolio.transactions)
        print(f"总交易次数: {len(portfolio.transactions)}")
        print(f"总交易成本: {total_commission:.2f}")
        print('=' * 70)

    def plot(self):
        metrics = self.calculate_metrics()
        if not metrics:
            print('没有有效数据可绘制')
            return
        portfolio = self.result.portfolio
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        axes[0].plot(portfolio.dates, portfolio.values, linewidth=2, color='blue', label=self.result.strategy_name)
        axes[0].axhline(y=portfolio.initial_cash, color='gray', linestyle='--', alpha=0.7, label='初始资金')
        buy_dates = [t.date for t in portfolio.transactions if t.action == 'BUY']
        sell_dates = [t.date for t in portfolio.transactions if t.action == 'SELL']
        buy_values = [portfolio.values[min(portfolio.dates.index(d), len(portfolio.values) - 1)] for d in buy_dates if d in portfolio.dates]
        sell_values = [portfolio.values[min(portfolio.dates.index(d), len(portfolio.values) - 1)] for d in sell_dates if d in portfolio.dates]
        if buy_dates:
            axes[0].scatter(buy_dates, buy_values, color='red', marker='^', s=60, label='买入点')
        if sell_dates:
            axes[0].scatter(sell_dates, sell_values, color='orange', marker='v', s=60, label='卖出点')
        axes[0].set_title('组合净值曲线')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        axes[0].text(
            0.02,
            0.98,
            f"夏普率: {metrics['sharpe_ratio']:.2f}\n最大回撤: {metrics['max_drawdown']:.2%}",
            transform=axes[0].transAxes,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
        )
        fund_values = {code: [] for code in self.fund_names.keys()}
        for date in portfolio.dates:
            holdings = portfolio.holdings_history.get(date, {})
            prices = portfolio.price_history.get(date, {})
            for code in fund_values:
                fund_values[code].append(holdings.get(code, 0.0) * prices.get(code, 0.0))
        for code, values in fund_values.items():
            label = f"{self.fund_names.get(code, code)}({code})"
            axes[1].plot(portfolio.dates, values, linewidth=1.5, label=label)
        axes[1].set_title('基金持仓市值贡献')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
