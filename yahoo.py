import logging
import random
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import requests

from tickers import tickers

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
# log_config.configure('yahoo_graph')

TZ = timezone(timedelta(hours=-4))  # EDT


class Candle:
    def __init__(self, timestamp, open, high, low, close):
        self.datetime = datetime.fromtimestamp(timestamp, tz=TZ)
        self.open = open
        self.high = high
        self.low = low
        self.close = close

    def __str__(self):
        return 'Candle({0.when} {0.open:.2f} {0.high:.2f} {0.low:.2f} {0.close:.2f})'.format(self)

    __repr__ = __str__

    @property
    def when(self):
        return self.datetime.strftime('%m%d-%H%M')


class Period(list):
    periods = [1, 7, 30, 90, 180]

    def __init__(self, ticker, data):
        super(Period, self).__init__(data)
        self.ticker = ticker
        self.days = self[-1].datetime - self[0].datetime
        self.highest = max(self, key=lambda val: val.high)
        self.percent = (self[-1].close / self.highest.high - 1) * 100
        # self.dump()

    def __hash__(self):
        return id(self)

    def dump(self):
        for candle in self:
            log.info(candle)

    @lru_cache()
    def period(self, days_back):
        datetime_back = self[-1].datetime - timedelta(days_back)
        return Period(ticker=self.ticker, data=list(filter(lambda item: item.datetime > datetime_back, self)))

    def compare(self, other):
        my_results = self.results
        other_results = other.results
        diff = [(period, my_result, other_result, my_result - other_result) for period, my_result, other_result in zip(self.periods, my_results, other_results)]
        # log.info(diff)
        return diff

    @property
    def results(self):
        return [self.period(days).percent for days in self.periods]
        # return [random.randint(-3, 0) for days in self.periods]

    def debug_info(self):
        periods_strs = ['{per.percent:2.2f}%:{per.highest.high:.2f}({per.highest.when})-{days}d'.format(per=self.period(days), days=days) for days in self.periods]
        return '{self.ticker:6.6s}\topen:{open.open:.2f}({open.when})\tclose:{close.close:.2f}({close.when})\t{periods}'.format(self=self,
                                                                                                                                open=self[0],
                                                                                                                                close=self[-1],
                                                                                                                                periods='\t'.join(periods_strs))


def process(tickers):
    results = []
    for ticker in tickers:
        # with IgnoreExceptions():
        log.info('Processing %s' % ticker)
        end = datetime.now(TZ)
        start = end - timedelta(180)
        start_ts = int(start.astimezone(timezone.utc).timestamp())
        end_ts = int(end.astimezone(timezone.utc).timestamp())
        # log.info('%s %s %s %s %s' % (ticker, start, end, start_ts, end_ts))
        resp = requests.get(r'https://query1.finance.yahoo.com/v8/finance/chart/%s' % ticker,
                            timeout=(10, 10),
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
        data = [Candle(*values) for values in zip(result['timestamp'], quotes['open'], quotes['high'], quotes['low'], quotes['close'])]
        results.append(Period(ticker=ticker, data=data))
    return results


def output(results):
    for item in sorted(results, key=lambda result: result.period(30).percent, reverse=True):
        log.info(item.debug_info())


def prepare(tickers):
    return filter(None, tickers.splitlines())


if __name__ == '__main__':
    output(process(prepare(tickers)))

    # output(process(prepare('lrcx')))

    # lrcx = process(prepare('lrcx'))[0]
    # adbe = process(prepare('adbe'))[0]
    # print(lrcx.info())
    # print(adbe.info())
    # print(lrcx.compare(adbe))



# response example
# {
#   "chart": {
#     "result": [
#       {
#         "meta": {
#           "currency": "USD",
#           "symbol": "LRCX",
#           "exchangeName": "NMS",
#           "instrumentType": "EQUITY",
#           "firstTradeDate": 452505600,
#           "gmtoffset": -14400,
#           "timezone": "EDT",
#           "exchangeTimezoneName": "America/New_York",
#           "chartPreviousClose": 195.49,
#           "currentTradingPeriod": {
#             "pre": {
#               "timezone": "EDT",
#               "start": 1529049600,
#               "end": 1529069400,
#               "gmtoffset": -14400
#             },
#             "regular": {
#               "timezone": "EDT",
#               "start": 1529069400,
#               "end": 1529092800,
#               "gmtoffset": -14400
#             },
#             "post": {
#               "timezone": "EDT",
#               "start": 1529092800,
#               "end": 1529107200,
#               "gmtoffset": -14400
#             }
#           },
#           "dataGranularity": "1d",
#           "validRanges": [
#             "1d",
#             "5d",
#             "1mo",
#             "3mo",
#             "6mo",
#             "1y",
#             "2y",
#             "5y",
#             "10y",
#             "ytd",
#             "max"
#           ]
#         },
#         "timestamp": [
#           1526650200,
#           ...
#         ],
#         "events": {
#           "dividends": {
#             "1528205400": {
#               "amount": 1.1,
#               "date": 1528205400
#             }
#           }
#         },
#         "indicators": {
#           "quote": [
#             {
#               "volume": [
#                 5250100,
#                 ...
#               ],
#               "open": [
#                 195.25,
#                 ...
#               ],
#               "low": [
#                 192.17999267578125,
#                 ...
#               ],
#               "close": [
#                 195.49000549316406,
#                 ...
#               ],
#               "high": [
#                 197.8800048828125,
#                 ...
#               ]
#             }
#           ],
#           "adjclose": [
#             {
#               "adjclose": [
#                 194.43893432617188,
#                 ...
#               ]
#             }
#           ]
#         }
#       }
#     ],
#     "error": null
#   }
# }
