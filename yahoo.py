import logging
from datetime import datetime, timedelta, timezone
from operator import itemgetter

import requests

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
# log_config.configure('yahoo_graph')

TZ = timezone(timedelta(hours=-4))  # EDT
EDT = timezone(timedelta(hours=-4))
ET = timezone(timedelta(hours=-4))
MSK = timezone(timedelta(hours=3))

end = datetime.now(EDT)
start = end - timedelta(7)


def process(tickers):
    results = []
    for ticker in tickers:
        # with IgnoreExceptions():
        log.info('Processing %s' % ticker)
        start_ts = int(start.astimezone(timezone.utc).timestamp())
        end_ts = int(end.astimezone(timezone.utc).timestamp())
        # log.info('%s %s %s %s %s' % (ticker, start, end, start_ts, end_ts))
        resp = requests.get(r'https://query1.finance.yahoo.com/v8/finance/chart/%s' % ticker,
                            params=dict(symbol=ticker,
                                        period1=start_ts,  # in utc
                                        period2=end_ts,  # in utc
                                        interval='1d',  # 1m 2m 5m 15m 30m 1h 4h 1d 1w 1m
                                        includePrePost=False,
                                        events='div|split|earn',
                                        corsDomain='finance.yahoo.com'))

        resp.raise_for_status()
        data = resp.json()
        error = data['chart']['error']
        assert not error, error
        result = data['chart']['result'][0]
        quotes = result['indicators']['quote'][0]
        q = [dict(timestamp=datetime.fromtimestamp(values[0], tz=TZ), open=values[1] or 0, high=values[2] or 0, low=values[3] or 0, close=values[4] or 0)
             for values in zip(result['timestamp'], quotes['open'], quotes['high'], quotes['low'], quotes['close'])]
        # for vals in q:
        #     log.info('%s %s %s' % (ticker, datetime.fromtimestamp(vals['timestamp'], tz=TZ), ' '.join(map(lambda i: '%s:%s' % (i[0], i[1]), vals.items()))))
        max_item = max(q, key=lambda val: val['high'])
        max_value = max_item['high']
        close_value = q[-1]['close']

        results.append(dict(ticker=ticker,
                            max_ts=max_item['timestamp'],
                            max_value=max_value,
                            open_ts=q[0]['timestamp'],
                            open_value=q[0]['open'],
                            close_ts=q[-1]['timestamp'],
                            close_value=close_value,
                            percent=1 - close_value / max_value))

    return results


def output(results):
    for item in sorted(results, key=itemgetter('percent')):
        log.info('{ticker} open:{open_value:.2f}({open_ts}) max:{max_value:.2f}({max_ts}) close:{close_value:.2f}({close_ts}) {percent:.2%}'.format(**item))


def prepare(tickers):
    return filter(None, tickers.splitlines())


tickers = """
ADBE
ALGN
AMZN
CME
EA
ETFC
FB
GOOG
IDXX
INTC
INTU
LRCX
MA
NDAQ
NFLX
NOC
NVDA
PGR
RTN
SPGI
TXN
UNH
V
VLO

AAPL
ALL
AMAT
ATVI
BA
BABA
BBY
CNC
CTAS
EL
FLIR
ISRG
KLAC
MAS
MPC
MU
NTAP
SYY
TWTR
WM
XYL
"""

if __name__ == '__main__':
    output(process(prepare(tickers)))
    # output(process(prepare('cme')))

