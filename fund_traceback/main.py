from .analyzer import PerformanceAnalyzer
from .config import DATE_RANGE, FEES, FUNDS, OUTPUT, REBALANCE_CONFIG, STRATEGY
from .data_manager import FundDataManager
from .engine import BacktestEngine
from .strategies import StrategyFactory


def validate_config():
    if STRATEGY not in {'buy_hold', 'rebalance'}:
        raise ValueError('STRATEGY 只支持 buy_hold 或 rebalance')
    if not FUNDS:
        raise ValueError('FUNDS 不能为空')
    for code, amount in FUNDS.items():
        if amount <= 0:
            raise ValueError(f'基金金额必须大于0: {code}')
    if STRATEGY == 'rebalance':
        target_weights = REBALANCE_CONFIG.get('target_weights', {})
        if set(target_weights.keys()) != set(FUNDS.keys()):
            raise ValueError('再平衡策略的 target_weights 必须与 FUNDS 基金列表一致')
        total_weight = sum(target_weights.values())
        if abs(total_weight - 1.0) > 1e-6:
            raise ValueError('再平衡策略的 target_weights 之和必须等于 1')
        if REBALANCE_CONFIG.get('frequency') not in {'daily', 'monthly', 'quarterly'}:
            raise ValueError('frequency 只支持 daily/monthly/quarterly')


def print_trades(result, fund_names):
    if not OUTPUT['print_trades']:
        return
    trades = result.portfolio.transactions
    if not trades:
        return
    max_count = OUTPUT['max_trades_shown']
    print(f"\nTransaction Records (Total {len(trades)}):")
    for index, item in enumerate(trades[:max_count]):
        fund_name = fund_names.get(item.fund_code, item.fund_code)
        print(f"  {index + 1}. {item.date.strftime('%Y-%m-%d')} {item.action} {fund_name}({item.fund_code}) {item.units:.2f} units @ {item.price:.4f}")
    if len(trades) > max_count:
        print(f"  ... Omitted {len(trades) - max_count} transactions")


def main():
    validate_config()
    manager = FundDataManager()
    fund_codes = list(FUNDS.keys())
    nav_df = manager.get_nav_data(fund_codes, DATE_RANGE['start'], DATE_RANGE['end'])
    fund_names = manager.get_fund_names(fund_codes)
    strategy = StrategyFactory.create(STRATEGY, REBALANCE_CONFIG)
    engine = BacktestEngine()
    result = engine.run(strategy, nav_df, FUNDS, FEES)
    analyzer = PerformanceAnalyzer(result, fund_names)
    analyzer.print_report()
    print_trades(result, fund_names)
    if OUTPUT['export_csv']:
        nav_df.to_csv(OUTPUT['csv_path'], encoding='utf-8-sig')
        print(f"已导出净值数据: {OUTPUT['csv_path']}")
    if OUTPUT['show_plot']:
        analyzer.plot()


if __name__ == '__main__':
    main()
