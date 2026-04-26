import pandas as pd
import tushare as ts

from .config import TUSHARE_TOKEN


ts.set_token(TUSHARE_TOKEN)


class FundDataManager:
    def __init__(self):
        self.pro = ts.pro_api()

    def get_nav_data(self, fund_codes, start_date, end_date):
        print('Fetching fund nav data...')
        all_data = {}
        for fund_code in fund_codes:
            try:
                df = self.pro.fund_nav(
                    ts_code=fund_code,
                    market='O',
                    start_date=start_date,
                    end_date=end_date,
                    fields='ts_code,nav_date,adj_nav,accum_nav,unit_nav'
                )
                if df is None or df.empty:
                    print(f'Warning: Unable to get nav data for {fund_code}')
                    continue
                df = df.sort_values('nav_date')
                df['nav_date'] = pd.to_datetime(df['nav_date'])
                df['nav'] = df['adj_nav'].fillna(df['accum_nav']).fillna(df['unit_nav'])
                df = df[['nav_date', 'nav']].dropna()
                if df.empty:
                    print(f'Warning: No valid nav data for {fund_code}')
                    continue
                df = df.groupby('nav_date', as_index=False)['nav'].last()
                df.set_index('nav_date', inplace=True)
                df.rename(columns={'nav': fund_code}, inplace=True)
                all_data[fund_code] = df
                print(f'Successfully fetched {fund_code} data, total {len(df)} records')
            except Exception as e:
                print(f'Failed to get {fund_code} data: {e}')
        if not all_data:
            raise ValueError('No fund nav data obtained')
        merged_df = pd.DataFrame()
        for fund_code, df in all_data.items():
            merged_df = df if merged_df.empty else merged_df.join(df, how='outer')
        merged_df = merged_df.sort_index().ffill().dropna(how='all')
        return merged_df

    def get_fund_names(self, fund_codes):
        names = {}
        for fund_code in fund_codes:
            try:
                df = self.pro.fund_basic(market='O', ts_code=fund_code, fields='ts_code,name')
                if df is not None and not df.empty:
                    names[fund_code] = str(df.iloc[0]['name'])
                else:
                    names[fund_code] = fund_code
            except Exception:
                names[fund_code] = fund_code
        return names
