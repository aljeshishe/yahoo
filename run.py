import time

from yahoo import output, process, prepare, tickers

if __name__ == '__main__':
    while True:
        output(process(prepare(tickers)))
        time.sleep(60 * 5)

# change 2 f2