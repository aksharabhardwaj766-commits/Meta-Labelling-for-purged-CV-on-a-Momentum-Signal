'''
- Load the CSV
- Parse the tickers column into a python list
- given a target date, find the closest available date <= that date, 
    and returns its ticker list (point-in-time-lookup)
- Given the date range (eg: 2018-2026), collect the union of all tickers that
appeared at any point -- this becomes your download universe.
'''

import pandas as pd

df = pd.read_csv('data/raw/S&P 500 Historical Components & Changes (Updated).csv')
df.columns = [c.lower() for c in df.columns]
df['date'] = pd.to_datetime(df['date'])

df['tickers'] = df['tickers'].apply(lambda s: s.split(','))

df = df.sort_values('date')

def get_const_on_date(trgt_date):
    trgt_date = pd.to_datetime(trgt_date)
    rows = df[df['date'] <= trgt_date]
    last_row = rows.iloc[-1]
    return last_row['tickers']

def get_universe(start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    rows = df[mask]

    all_tickers = set()
    for t_list in rows['tickers']:
        all_tickers.update(t_list)

    return sorted(all_tickers)

if __name__ == '__main__':
    print(get_const_on_date('2020-06-01')[:10])
    universe = get_universe('2018-01-01', '2026-01-01')
    print(len(universe), 'tickers total')
