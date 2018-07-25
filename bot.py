#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""Simple Bot to send timed Telegram messages.

# This program is dedicated to the public domain under the CC0 license.

This Bot uses the Updater class to handle the bot and the JobQueue to send
timed messages.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Alarm Bot example, sends a message after a set time.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from yahoo import process, prepare, tickers

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

subscribers = set()

new_results = []
notified_results = {}


def start(bot, update):
    subscribers.add(update.message.chat_id)
    update.message.reply_text('Subscribing')
    results_str = []
    global new_results
    for item in sorted(new_results, key=lambda result: result.period(180).percent, reverse=True):
        periods_strs = ['{per.percent:2.1f}'.format(per=item.period(days), days=days) for days in item.periods]
        results_str.append('{self.ticker:5.5s}\t{periods}'.format(self=item, open=item[0], close=item[-1], periods='\t'.join(periods_strs)))
    update.message.reply_text('\n'.join(results_str))


def stop(bot, update):
    subscribers.remove(update.message.chat_id)
    update.message.reply_text('Unsubscribing')


def update(bot, job):
    global new_results, notified_results
    new_results = process(prepare(tickers))
    for item in sorted(new_results, key=lambda result: result.period(180).percent, reverse=True):
        log.info(item.debug_info())

    results_str = []
    for new in new_results:
        notified = notified_results.setdefault(new.ticker, new)
        for period, new_percent, old_percent, diff in new.compare(notified):
            if diff < -2:
                results_str.append('{:5.5s}\t{}d\told:{:2.1f}\tnew:{:2.1f}'.format(notified.ticker, period, old_percent, new_percent))
                notified_results[new.ticker] = new

    if results_str:
        for subscriber in subscribers:
            bot.send_message(chat_id=subscriber, text='\n'.join(results_str))


def error(bot, update, error):
    """Log Errors caused by Updates."""
    log.warning('Update "%s" caused error "%s"', update, error)


def main():
    """Run bot."""
    updater = Updater('590223940:AAEcsJfRqDYmyP5lDOvuhYXReXYb221-ozU', request_kwargs=dict(proxy_url='https://137.74.254.242:3128'))

    updater.job_queue.run_repeating(update, interval=60*5, first=0)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("stop", stop))
    dispatcher.add_handler(CommandHandler("help", start))
    dispatcher.add_handler(MessageHandler(Filters.text, start))
    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
