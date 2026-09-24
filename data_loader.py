'''
universe + prices
'''
import os
import pandas as pd
import yfinance as yf

START = '2017-01-01'
END = '2026-01-01'
BATCH_SIZE = 50
OUT_DIR = 'data/processed'
prices_file = os.path.join(OUT_DIR, 'prices.parquet')
failed_file = os.path.join(OUT_DIR, 'failed_tickers.csv')

os.makedirs(OUT_DIR, exist_ok=True)

def clean_ticker(t):
    # S&P list uses ABC.D, yahoo uses ABC-D
    return t.replace('.', '-')

def download_prices(tickers):
    '''dowanload daily prices in batches. returns (prices, failed).'''

    tickers = sorted(set(clean_ticker(t) for t in tickers))
    print('Total tickers:', len(tickers))

    all_data = []
    failed = []

    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i:i + BATCH_SIZE]
        print('Batch', i // BATCH_SIZE + 1, '-', len(batch), 'tickers')

        try:
            raw = yf.download(batch, start=START, end=END, auto_adjust=True, group_by='ticker', progress='FALSE',)

        except Exception as e:
            print('whole batch failed:', e)
            failed.extend(batch)
            continue

        for t in batch:
            #ticker not in result at all
            if t not in raw.columns.get_level_values(0):
                failed.append(t)
                continue 

            one = raw[t].dropna(how='all')

            #case 2: ticker is there but has no data
            if len(one) == 0:
                failed.append(t)
                continue 

            one = one.reset_index()
            one['ticker'] = t 
            all_data.append(one)

    prices = pd.concat(all_data, ignore_index=True)
    prices.columns = [str(c).lower() for c in prices.columns] 

    prices.to_parquet(prices_file)
    pd.Series(failed, name='ticker').to_csv(failed_file, index=False)
    print('Saved', len(prices), 'rows for', prices['ticker'].nunique(), 'tickers')
    print('Failed:', len(failed))

    return prices, failed 

def load_prices():
    '''load the saved file'''
    prices = pd.read_parquet(prices_file)
    failed = pd.read_csv(failed_file)['ticker'].tolist()
    return prices, failed 

def sanity_check(prices, failed, n_requested):
    print('1) Tickers requested:', n_requested)
    print('   Tickers failed:', len(failed), f'({len(failed) / n_requested:.1%})')
    print('2) Date Range:', prices['date'].min().date(), 'to', prices['date'].max().date())

    #zero vol days

    zero_vol = prices[prices['volume'] == 0]
    print('3) zero-volume rows:', len(zero_vol))

    #missing prices
    print('4) missing close prices:', prices['close'].isna().sum())

    # rows per ticker (short history = joined index late, or left early)
    counts = prices.groupby('ticker').size()
    print('5) rows per ticker:')
    print(counts.describe())
    print('  tickers with < 500 rows:', (counts<500).sum())

    #biggest gaps b/w two trades for each ticker
    def max_gap(d):
        return d['date'].sort_values().diff().dt.days.max()

    gaps = prices.groupby('ticker').apply(max_gap)
    print('6) Tickers with a gap > 10 days:', (gaps > 10).sum())
    print(gaps.sort_values(ascending=False).head(10))

if __name__ == '__main__':
    from constituents_loader import get_universe

    universe = list(get_universe('2018-01-01', '2026-01-01'))
    prices, failed = download_prices(universe)
    sanity_check(prices, failed, len(universe))

