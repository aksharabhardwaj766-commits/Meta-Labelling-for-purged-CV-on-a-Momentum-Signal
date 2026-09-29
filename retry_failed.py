import pandas as pd
import yfinance as yf
import time

START = '2017-01-01'
END = '2026-01-01'
PRICES_FILE = "data/processed/prices.parquet"
FAILED_FILE = "data/processed/failed_tickers.csv"

def retry_failed_tickers():
    prices = pd.read_parquet(PRICES_FILE)
    failed = pd.read_csv(FAILED_FILE)['ticker'].tolist()
    print('retrying', len(failed), 'tickers')

    recovered = []
    still_failed = []

    for t in failed:
        try:
            d = yf.download(t, start=START, end=END, auto_adjust=True, progress=False)

        except Exception as e:
            print(t, 'error:', e)
            still_failed.append(t)
            time.sleep(2)
            continue

        time.sleep(1)

        if len(d) == 0:
            still_failed.append(t)
            continue

        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.get_level_values(0)

        d = d.reset_index()
        d['tickers'] = t
        d.columns = [str(c).lower() for c in d.columns]
        recovered.append(d)
        print(t, 'recovered:', len(d), 'rows')

    print(len(recovered), "recovered,", len(still_failed), "still_failed")

    if len(recovered) > 0:
        prices = pd.concat([prices] + recovered, ignore_index=True)
        prices.to_parquet(PRICES_FILE)

    pd.Series(still_failed, name='ticker').to_csv(FAILED_FILE, index=False)
    return prices, still_failed

if __name__ == '__main__':
    retry_failed_tickers() 