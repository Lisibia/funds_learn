import tushare as ts
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Songti SC', 'SimHei']  # 使用MacOS系统可用的中文字体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题

# Set Tushare token (replace with your actual token)
ts.set_token('6c5ace2424e4a7602c7195abf962a3cc1e110f4aadd2a1b03112c99')
pro = ts.pro_api()


class Transaction:
    """交易记录类"""
    def __init__(self, date, etf, action, shares, price, value, commission):
        self.date = date
        self.etf = etf
        self.action = action  # 'BUY' or 'SELL'
        self.shares = shares
        self.price = price
        self.value = value
        self.commission = commission

    def __str__(self):
        return f"{self.date.strftime('%Y-%m-%d')} {self.action} {self.etf} {self.shares} shares @ {self.price:.2f}"


class Portfolio:
    """投资组合类"""
    def __init__(self, initial_cash):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.holdings = {}  # {etf_code: shares}
        self.transactions = []
        self.values = []  # 历史组合价值
        self.dates = []   # 对应的日期
        self.holdings_history = {}  # {date: {etf_code: shares}}
        self.price_history = {}  # {date: {etf_code: price}}
        self.target_weights = {}  # 目标权重 {etf_code: weight}

    def add_transaction(self, transaction):
        """添加交易记录"""
        self.transactions.append(transaction)
        
        # 更新持仓
        if transaction.action == 'BUY':
            if transaction.etf not in self.holdings:
                self.holdings[transaction.etf] = 0
            self.holdings[transaction.etf] += transaction.shares
            self.cash -= (transaction.value + transaction.commission)
        elif transaction.action == 'SELL':
            if transaction.etf in self.holdings and self.holdings[transaction.etf] >= transaction.shares:
                self.holdings[transaction.etf] -= transaction.shares
                self.cash += (transaction.value - transaction.commission)

    def calculate_total_value(self, current_prices):
        """计算当前组合总价值"""
        holdings_value = sum(shares * current_prices.get(etf, 0) 
                           for etf, shares in self.holdings.items())
        return self.cash + holdings_value

    def get_current_weights(self, current_prices):
        """获取当前持仓权重"""
        total_value = self.calculate_total_value(current_prices)
        if total_value <= 0:
            return {etf: 0 for etf in self.holdings.keys()}
        
        return {etf: (shares * current_prices.get(etf, 0)) / total_value 
                for etf, shares in self.holdings.items()}

    def record_value(self, date, value):
        """记录组合价值"""
        self.dates.append(date)
        self.values.append(value)
    
    def record_daily_history(self, date, current_prices):
        """记录每日持仓和价格历史"""
        # 记录持仓历史
        self.holdings_history[date] = self.holdings.copy()
        
        # 记录价格历史
        self.price_history[date] = current_prices.copy()


class DataManager:
    """数据管理类"""
    def __init__(self):
        self.pro = ts.pro_api()

    def get_etf_data(self, etf_codes, start_date, end_date):
        """获取多个ETF的历史数据"""
        print("Fetching ETF data...")
        all_data = {}

        for etf_code in etf_codes:
            try:
                # Get adjusted data
                df = self.pro.fund_daily(ts_code=etf_code, start_date=start_date,
                                        end_date=end_date, fields='ts_code,trade_date,open,close,vol')

                if df is None or len(df) == 0:
                    print(f"Warning: Unable to get data for {etf_code}")
                    continue

                # Data cleaning and formatting
                df = df.sort_values('trade_date')
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df.set_index('trade_date', inplace=True)
                df = df[['open', 'close']]
                df.rename(columns={'open': f'{etf_code}_open', 'close': f'{etf_code}_close'}, inplace=True)

                all_data[etf_code] = df
                print(f"Successfully fetched {etf_code} data, total {len(df)} records")

            except Exception as e:
                print(f"Failed to get {etf_code} data: {e}")

        # Merge all ETF data
        if not all_data:
            raise ValueError("No ETF data obtained, please check network connection and Tushare Token")

        # Merge dataframes
        merged_df = pd.DataFrame()
        for etf_code, df in all_data.items():
            if merged_df.empty:
                merged_df = df
            else:
                merged_df = merged_df.join(df, how='outer')

        # Forward fill missing values
        merged_df.fillna(method='ffill', inplace=True)
        merged_df.dropna(inplace=True)

        return merged_df


class PerformanceAnalyzer:
    """绩效分析类"""
    def __init__(self, strategy_portfolio, buy_hold_portfolio):
        self.strategy_portfolio = strategy_portfolio
        self.buy_hold_portfolio = buy_hold_portfolio
        self.risk_free_rate = 0.03  # 假设无风险利率为3%

    def calculate_metrics(self):
        """计算绩效指标"""
        if not self.strategy_portfolio.values or not self.buy_hold_portfolio.values:
            return None

        # 策略指标
        strategy_metrics = self._calculate_single_metrics(self.strategy_portfolio)
        # 买入持有策略指标
        bh_metrics = self._calculate_single_metrics(self.buy_hold_portfolio)

        return strategy_metrics, bh_metrics

    def _calculate_single_metrics(self, portfolio):
        """计算单个投资组合的绩效指标"""
        values = np.array(portfolio.values)
        dates = np.array(portfolio.dates)

        initial_value = portfolio.initial_cash
        final_value = values[-1]
        total_return = (final_value - initial_value) / initial_value

        total_days = len(values)
        years = total_days / 252  # 假设252个交易日

        # 年化收益率
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else total_return

        # 日收益率
        daily_returns = []
        for i in range(1, len(values)):
            if values[i - 1] > 0:
                ret = (values[i] - values[i - 1]) / values[i - 1]
                daily_returns.append(ret)
            else:
                daily_returns.append(0)
        daily_returns = np.array(daily_returns)

        # Sharpe比率
        risk_free_daily = self.risk_free_rate / 252
        sharpe_ratio = 0
        if len(daily_returns) > 0 and np.std(daily_returns) > 0:
            sharpe_ratio = (np.mean(daily_returns) - risk_free_daily) / np.std(daily_returns) * np.sqrt(252)

        # 最大回撤
        peak = values[0]
        max_drawdown = 0
        for val in values:
            if val > peak:
                peak = val
            else:
                drawdown = (peak - val) / peak
                max_drawdown = max(max_drawdown, drawdown)

        return {
            'initial_value': initial_value,
            'final_value': final_value,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_days': total_days,
            'daily_returns': daily_returns
        }

    def print_results(self):
        """打印绩效结果"""
        strategy_metrics, bh_metrics = self.calculate_metrics()
        if not strategy_metrics or not bh_metrics:
            print("没有足够的有效数据进行绩效分析")
            return

        # 输出策略结果
        print("\n" + "=" * 70)
        print("回测结果汇总")
        print("=" * 70)
        print(f"回测期间: {self.strategy_portfolio.dates[0].strftime('%Y-%m-%d')} 至 {self.strategy_portfolio.dates[-1].strftime('%Y-%m-%d')}")
        print(f"初始资金: {strategy_metrics['initial_value']:,.2f}")
        print(f"最终资金: {strategy_metrics['final_value']:,.2f}")
        print(f"总收益率: {strategy_metrics['total_return']:.2%}")
        print(f"年化收益率: {strategy_metrics['annual_return']:.2%}")
        print(f"夏普比率: {strategy_metrics['sharpe_ratio']:.2f}")
        print(f"最大回撤: {strategy_metrics['max_drawdown']:.2%}")
        
        # 交易统计
        total_trades = len(self.strategy_portfolio.transactions)
        buy_trades = len([t for t in self.strategy_portfolio.transactions if t.action == 'BUY'])
        sell_trades = len([t for t in self.strategy_portfolio.transactions if t.action == 'SELL'])
        total_commission = sum(t.commission for t in self.strategy_portfolio.transactions)
        print(f"总交易次数: {total_trades} (买入: {buy_trades}, 卖出: {sell_trades})")
        print(f"总交易成本: {total_commission:.2f}")

        # 输出买入持有策略结果
        print("\n" + "买入持有策略结果")
        print("-" * 70)
        print(f"最终资金: {bh_metrics['final_value']:,.2f}")
        print(f"总收益率: {bh_metrics['total_return']:.2%}")
        print(f"年化收益率: {bh_metrics['annual_return']:.2%}")
        print(f"夏普比率: {bh_metrics['sharpe_ratio']:.2f}")
        print(f"最大回撤: {bh_metrics['max_drawdown']:.2%}")
        print("=" * 70)

    def plot_performance(self):
        """绘制绩效图表"""
        if not self.strategy_portfolio.values or not self.buy_hold_portfolio.values:
            print("没有有效数据可绘制")
            return

        # 创建图表
        plt.figure(figsize=(14, 10))

        # 1. 组合价值对比图
        plt.subplot(2, 1, 1)

        # 绘制策略价值曲线
        plt.plot(self.strategy_portfolio.dates, self.strategy_portfolio.values, 
                 linewidth=2, label='再平衡策略', color='blue')

        # 绘制买入持有策略价值曲线
        plt.plot(self.buy_hold_portfolio.dates, self.buy_hold_portfolio.values, 
                 linewidth=2, label='买入持有策略', color='green',
                 linestyle='--')

        # 标记交易点
        buy_dates = [t.date for t in self.strategy_portfolio.transactions if t.action == 'BUY']
        sell_dates = [t.date for t in self.strategy_portfolio.transactions if t.action == 'SELL']

        # 查找交易点对应的组合价值
        buy_values = []
        sell_values = []

        for date in buy_dates:
            for i, d in enumerate(self.strategy_portfolio.dates):
                if d >= date:
                    buy_values.append(self.strategy_portfolio.values[i])
                    break

        for date in sell_dates:
            for i, d in enumerate(self.strategy_portfolio.dates):
                if d >= date:
                    sell_values.append(self.strategy_portfolio.values[i])
                    break

        # 标记买入点
        if buy_dates and buy_values:
            plt.scatter(buy_dates, buy_values, color='red', marker='^', s=100, zorder=5, label='买入点')

        # 标记卖出点
        if sell_dates and sell_values:
            plt.scatter(sell_dates, sell_values, color='orange', marker='v', s=100, zorder=5, label='卖出点')

        plt.axhline(y=self.strategy_portfolio.initial_cash, color='gray', linestyle='--', alpha=0.7, label='初始资金')
        plt.title('组合价值对比')
        plt.ylabel('组合价值')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # 2. ETF对组合价值的贡献
        plt.subplot(2, 1, 2)

        # 获取ETF对组合价值的贡献
        etf_values = {}
        for etf_code in self.strategy_portfolio.target_weights.keys():
            etf_values[etf_code] = []
            
        for i, date in enumerate(self.strategy_portfolio.dates):
            # 获取当日的组合持仓
            holdings = self.strategy_portfolio.holdings_history.get(date, {})
            prices = self.strategy_portfolio.price_history.get(date, {})
            
            total_etf_value = 0
            for etf_code in self.strategy_portfolio.target_weights.keys():
                shares = holdings.get(etf_code, 0)
                price = prices.get(etf_code, 0)
                etf_value = shares * price
                etf_values[etf_code].append(etf_value)
                total_etf_value += etf_value
            
            # 如果没有持仓数据，设为零
            if total_etf_value == 0:
                for etf_code in self.strategy_portfolio.target_weights.keys():
                    etf_values[etf_code][-1] = 0

        # 绘制ETF价值贡献
        colors = ['red', 'purple', 'orange', 'brown', 'pink', 'gray', 'olive', 'cyan']
        for i, (etf_code, values) in enumerate(etf_values.items()):
            # 使用中文名称，如果没有映射则使用代码
            etf_name = ETF_CHINESE_NAMES.get(etf_code, etf_code)
            plt.plot(self.strategy_portfolio.dates, values, 
                     linewidth=1.5, label=f'{etf_name}', 
                     color=colors[i % len(colors)], alpha=0.8)

        plt.title('ETF对组合价值的贡献')
        plt.ylabel('价值 (CNY)')
        plt.xlabel('日期')
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()


class Strategy:
    """策略基类"""
    def __init__(self, target_weights, initial_cash=100000, commission=0.0005):
        self.target_weights = target_weights
        self.initial_cash = initial_cash
        self.commission = commission
        self.data_manager = DataManager()

    def calculate_round_lots(self, target_value, price):
        """计算整数手数"""
        if price <= 0:
            return 0
        target_shares = target_value / price
        rounded_shares = int(target_shares // 100) * 100
        return max(rounded_shares, 0)

    def run_backtest(self, start_date, end_date):
        """运行回测，子类必须实现"""
        raise NotImplementedError("子类必须实现run_backtest方法")


class RebalancingStrategy(Strategy):
    """再平衡策略类"""
    def __init__(self, target_weights, initial_cash=100000, 
                 commission=0.0005, rebalance_threshold=0.02):
        super().__init__(target_weights, initial_cash, commission)
        self.rebalance_threshold = rebalance_threshold

    def run_backtest(self, start_date, end_date):
        """运行回测"""
        print("Starting backtest...")

        # 获取数据
        data_df = self.data_manager.get_etf_data(
            list(self.target_weights.keys()), start_date, end_date)
        dates = data_df.index

        # 初始化投资组合
        strategy_portfolio = Portfolio(self.initial_cash)
        buy_hold_portfolio = Portfolio(self.initial_cash)
        
        # 设置目标权重
        strategy_portfolio.target_weights = self.target_weights.copy()
        buy_hold_portfolio.target_weights = self.target_weights.copy()

        # 初始建仓
        self._initial_purchase(dates[0], data_df, strategy_portfolio, buy_hold_portfolio)

        # 记录初始价值
        first_date = dates[0]
        strategy_value = strategy_portfolio.calculate_total_value(
            {etf: data_df.loc[first_date, f'{etf}_close'] 
             for etf in self.target_weights.keys()})
        bh_value = buy_hold_portfolio.calculate_total_value(
            {etf: data_df.loc[first_date, f'{etf}_close'] 
             for etf in self.target_weights.keys()})
        
        strategy_portfolio.record_value(first_date, strategy_value)
        buy_hold_portfolio.record_value(first_date, bh_value)

        # 主回测循环
        for i in range(1, len(dates)):
            current_date = dates[i]
            
            # 获取当前价格
            current_prices = {etf: data_df.loc[current_date, f'{etf}_close'] 
                            for etf in self.target_weights.keys()}

            # 计算当前价值
            strategy_value = strategy_portfolio.calculate_total_value(current_prices)
            bh_value = buy_hold_portfolio.calculate_total_value(current_prices)

            # 检查是否需要再平衡
            if self._needs_rebalancing(strategy_portfolio, current_prices):
                self._execute_rebalancing(current_date, strategy_value, 
                                         current_prices, strategy_portfolio)

            # 记录每日持仓和价格历史
            strategy_portfolio.record_daily_history(current_date, current_prices)
            buy_hold_portfolio.record_daily_history(current_date, current_prices)

            # 记录价值
            strategy_portfolio.record_value(current_date, strategy_value)
            buy_hold_portfolio.record_value(current_date, bh_value)

        return strategy_portfolio, buy_hold_portfolio

    def _initial_purchase(self, date, data_df, strategy_portfolio, buy_hold_portfolio):
        """初始建仓"""
        print(f"\nInitial portfolio setup date: {date.strftime('%Y-%m-%d')}")

        for etf_code, target_weight in self.target_weights.items():
            target_value = self.initial_cash * target_weight
            price_col = f'{etf_code}_open'
            price = data_df.loc[date, price_col]

            if pd.isna(price) or price <= 0:
                print(f"Warning: {etf_code} has no valid opening price on {date}, skipping")
                continue

            # 策略初始购买
            shares = self.calculate_round_lots(target_value, price)
            cost = shares * price
            commission_cost = cost * self.commission

            if cost + commission_cost <= strategy_portfolio.cash:
                transaction = Transaction(date, etf_code, 'BUY', shares, price, cost, commission_cost)
                strategy_portfolio.add_transaction(transaction)
                etf_name = ETF_CHINESE_NAMES.get(etf_code, etf_code)
                print(f"  Buy {etf_name}: {shares} shares @ {price:.2f}, cost: {cost:.2f}")
            else:
                etf_name = ETF_CHINESE_NAMES.get(etf_code, etf_code)
                print(f"  Insufficient funds to buy {etf_name}, needed {cost:.2f}, available {strategy_portfolio.cash:.2f}")

            # 买入持有策略初始购买
            bh_shares = self.calculate_round_lots(target_value, price)
            bh_cost = bh_shares * price
            bh_commission = bh_cost * self.commission

            if bh_cost + bh_commission <= buy_hold_portfolio.cash:
                bh_transaction = Transaction(date, etf_code, 'BUY', bh_shares, price, bh_cost, bh_commission)
                buy_hold_portfolio.add_transaction(bh_transaction)
            else:
                # 如果资金不足，尽量多买
                max_shares = int(buy_hold_portfolio.cash / (price * (1 + self.commission)) // 100 * 100)
                if max_shares > 0:
                    max_cost = max_shares * price
                    max_commission = max_cost * self.commission
                    bh_transaction = Transaction(date, etf_code, 'BUY', max_shares, price, max_cost, max_commission)
                    buy_hold_portfolio.add_transaction(bh_transaction)

    def _needs_rebalancing(self, portfolio, current_prices):
        """检查是否需要再平衡"""
        current_weights = portfolio.get_current_weights(current_prices)
        for etf, target_weight in self.target_weights.items():
            current_weight = current_weights.get(etf, 0)
            if abs(current_weight - target_weight) > self.rebalance_threshold:
                return True
        return False

    def _execute_rebalancing(self, date, total_value, current_prices, portfolio):
        """执行再平衡"""
        current_weights = portfolio.get_current_weights(current_prices)
        deviations = {etf: abs(current_weights.get(etf, 0) - target_weight)
                     for etf, target_weight in self.target_weights.items()}
        
        print(f"\n{date.strftime('%Y-%m-%d')}: Rebalancing triggered, deviations: {deviations}")

        # 先卖后买
        # 计算目标持仓
        target_holdings = {etf: self.calculate_round_lots(total_value * target_weight, current_prices[etf])
                          for etf, target_weight in self.target_weights.items()}

        # 卖出超额持仓
        for etf, current_shares in portfolio.holdings.items():
            target_shares = target_holdings.get(etf, 0)
            if current_shares > target_shares:
                sell_shares = min(current_shares - target_shares, current_shares)
                if sell_shares > 0:
                    sell_value = sell_shares * current_prices[etf]
                    commission = sell_value * self.commission
                    transaction = Transaction(date, etf, 'SELL', sell_shares, 
                                            current_prices[etf], sell_value, commission)
                    portfolio.add_transaction(transaction)
                    etf_name = ETF_CHINESE_NAMES.get(etf, etf)
                    print(f"  Sell {etf_name}: {sell_shares} shares @ {current_prices[etf]:.2f}, income: {sell_value:.2f}")

        # 买入不足持仓
        for etf, target_shares in target_holdings.items():
            current_shares = portfolio.holdings.get(etf, 0)
            if target_shares > current_shares:
                buy_shares = target_shares - current_shares
                buy_value = buy_shares * current_prices[etf]
                commission = buy_value * self.commission
                total_cost = buy_value + commission
                
                if total_cost <= portfolio.cash:
                    transaction = Transaction(date, etf, 'BUY', buy_shares, 
                                            current_prices[etf], buy_value, commission)
                    portfolio.add_transaction(transaction)
                    etf_name = ETF_CHINESE_NAMES.get(etf, etf)
                    print(f"  Buy {etf_name}: {buy_shares} shares @ {current_prices[etf]:.2f}, cost: {buy_value:.2f}")
                else:
                    etf_name = ETF_CHINESE_NAMES.get(etf, etf)
                    print(f"  Insufficient funds to buy {etf_name}, needed {total_cost:.2f}, available {portfolio.cash:.2f}")


# ETF代码到中文名称的全局映射
ETF_CHINESE_NAMES = {
    '161125.SZ': '标普500ETF',  # 标普500
    '518850.SH': '黄金ETF',  # 黄金
    '161119.SZ': '债券ETF',  # 债券
    '159259.SZ': '成长ETF',  # 成长
    # '159338.SZ': '中证A500ETF',  # 中证A500
    '159232.SZ': '中证现金流ETF',  # 中证现金流
    '159201.SZ': '自由现金流ETF',  # 自由现金流
    '161130.SZ': '纳斯达克ETF',  # 纳斯达克
    '159100.SZ': '巴西ETF',  # 巴西
    '513000.SH': '日经ETF',  # 日经
    '159985.SZ': '豆粕期货ETF', # 豆粕期货
}

# Main function
def main():
    # 定义目标权重
    target_weights = {
        '161125.SZ': 0.05,  # 标普500
        '518850.SH': 0.05,  # 黄金
        '161119.SZ': 0.60,  # 债券
        '159259.SZ': 0.10,  # 成长
        # '159338.SZ': 0.10,  # 中证A500
        '159232.SZ': 0.05,  # 中证现金流
        '159201.SZ': 0.05,  #自由现金流
        '161130.SZ': 0.025,  #纳斯达克
        '159100.SZ': 0.025,  #巴西ETF
        '513000.SH': 0.025, #日经
        '159985.SZ': 0.025, #豆粕期货

    }

    # 初始化策略
    strategy = RebalancingStrategy(
        target_weights=target_weights,
        initial_cash=100000,
        commission=0.00005,
        rebalance_threshold=0.04
    )

    # 运行回测
    try:
        strategy_portfolio, buy_hold_portfolio = strategy.run_backtest(
            start_date='20200101',
            end_date='20251231'
        )

        # 分析绩效
        analyzer = PerformanceAnalyzer(strategy_portfolio, buy_hold_portfolio)
        analyzer.print_results()
        analyzer.plot_performance()

        # 显示交易记录
        if strategy_portfolio.transactions:
            print(f"\nTransaction Records (Total {len(strategy_portfolio.transactions)}):")
            for i, trans in enumerate(strategy_portfolio.transactions[:10]):  # 只显示前10条
                etf_name = ETF_CHINESE_NAMES.get(trans.etf, trans.etf)
                print(f"  {i + 1}. {trans.date.strftime('%Y-%m-%d')} {trans.action} {etf_name} {trans.shares} shares @ {trans.price:.2f}")

            if len(strategy_portfolio.transactions) > 10:
                print(f"  ... Omitted {len(strategy_portfolio.transactions) - 10} transactions")

    except Exception as e:
        print(f"Error during backtest: {e}")


if __name__ == "__main__":
    main()