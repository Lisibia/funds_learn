STRATEGY = 'buy_hold'

DATE_RANGE = {
    'start': '20200101',
    'end': '20260424',
}

FUNDS = {
        '019000.OF': 200,
        '021277.OF': 1100,
        '019305.OF': 650,
        '016702.OF': 3500,
        '016452.OF': 1750,
        '110008.OF': 10000,
        '003280.OF': 300000,
        '020740.OF': 5000,
        '017730.OF': 1200,
        '000070.OF': 20000,
        '001422.OF': 10000,
        '006331.OF': 60000,
        '009308.OF': 10000,
        '019524.OF': 3300,
        '022488.OF': 5000,
        '016858.OF': 10000,
        '018561.OF': 2000,
        '013360.OF': 20000,
        '016600.OF': 20000,
}

REBALANCE_CONFIG = {
    'target_weights': {
        '019000.OF': 0.3,
        '002833.OF': 0.7,
    },
    'threshold': 0.05,
    'frequency': 'monthly',
}

FEES = {
    'purchase_rate': 0.0015,
    'redeem_rate': 0.005,
}

OUTPUT = {
    'show_plot': True,
    'export_csv': False,
    'csv_path': 'fund_nav_history.csv',
    'print_trades': True,
    'max_trades_shown': 20,
}

TUSHARE_TOKEN = '6c5ace2424e4a7602c7195abf962a3cc1e110f4aadd2a1b03112c99'
