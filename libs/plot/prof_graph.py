# coding: utf-8
#!/usr/bin/python3

from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas
import random
from threading import Thread
import time

# 日次損益グラフをプロットするクラス
class ProfitGraph(object):
    def __init__(self, logger, stats, strategy, lock):
        self._logger = logger
        self._stats = stats
        self._strategy = strategy
        self._lock = lock

    def plot(self, image_file, ws, fmt='%H:%M', rotate=0 ):
        if self._logger.discord.webhook!='' :
            Thread(target=self._plot, args=(image_file,ws,fmt,rotate,)).start()

    def _plot(self, image_file, ws, fmt, rotate):
        org_stats = self._stats.get_stats()
        if len(org_stats)==0 :
            return

        t=0
        stats=[]
        for s in org_stats:
            if s['timestamp']-t>20 and time.time()-s['timestamp']<86400 :
                stats.append(s)
                t=s['timestamp']
        stats.append(org_stats[-1])

        history_timestamp = [s['timestamp'] for s in stats]
        price_history_raw = [ws.units()['unitrate']*(s['profit']-stats[0]['profit']) for s in stats]
        price_history = list(pandas.Series(price_history_raw).rolling(window=20, min_periods=1).mean())
        price_history[-1] = price_history_raw[-1]


        self._logger.info("[plot] Start plotting profit graph" )
        with self._lock :
            fig = plt.figure()
            fig.autofmt_xdate()
            fig.tight_layout()

            time.sleep(random.uniform(1.0, 3.0))
            start = time.time()

            ax = fig.add_subplot(111, facecolor='#fafafa')
            ax.spines['top'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(which='major', linestyle='-', color='#101010', alpha=0.1, axis='y')
            if rotate == 0:
                ax.tick_params(width=0, length=0)
            else:
                ax.tick_params(width=1, length=5)
            ax.tick_params(axis='x', colors='#c0c0c0')
            ax.tick_params(axis='y', colors='#c0c0c0')
            if fmt != '':
                ax.xaxis.set_major_formatter(mdates.DateFormatter(fmt))
            ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
            ax.yaxis.get_major_formatter().set_scientific(False)
            ax.yaxis.get_major_formatter().set_useOffset(False)

            green1 = '#10b285'
            green2 = '#9cdcd0'
            red1 = '#e25447'
            red2 = '#f0b8b8'

            if price_history[-1] >= 0:
                ax.set_title(ws.units(round(price_history[-1],4))['title'], color=green1, fontsize=28)
            else:
                ax.set_title(ws.units(round(price_history[-1],4))['title'], color=red1, fontsize=28)

            time.sleep(random.uniform(1.0, 3.0))
            last = 0
            plus_times = []
            plus_price = []
            minus_times = []
            minus_price = []
            for i in range(0, len(history_timestamp)):
                if last * price_history[i] >= 0:
                    if price_history[i] >= 0:
                        plus_times.append(datetime.fromtimestamp(history_timestamp[i]))
                        plus_price.append(price_history[i])
                    if price_history[i] <= 0:
                        minus_times.append(datetime.fromtimestamp(history_timestamp[i]))
                        minus_price.append(price_history[i])
                else:
                    cross_point = price_history[i-1]/(price_history[i-1]-price_history[i])*(history_timestamp[i]-history_timestamp[i-1])+history_timestamp[i-1]
                    if price_history[i] < 0:
                        plus_times.append(datetime.fromtimestamp(cross_point))
                        plus_price.append(0)
                        ax.plot(plus_times, plus_price, color=green1, linewidth=0.8)
                        ax.fill_between(plus_times, plus_price, 0, color=green2, alpha=0.25)
                        plus_times = []
                        plus_price = []
                        minus_times = []
                        minus_price = []
                        minus_times.append(datetime.fromtimestamp(cross_point))
                        minus_price.append(0)
                        minus_times.append(datetime.fromtimestamp(history_timestamp[i]))
                        minus_price.append(price_history[i])
                    else:
                        minus_times.append(datetime.fromtimestamp(cross_point))
                        minus_price.append(0)
                        ax.plot(minus_times, minus_price, color=red1, linewidth=0.8)
                        ax.fill_between(minus_times, minus_price, 0, color=red2, alpha=0.25)
                        plus_times = []
                        plus_price = []
                        minus_times = []
                        minus_price = []
                        plus_times.append(datetime.fromtimestamp(cross_point))
                        plus_price.append(0)
                        plus_times.append(datetime.fromtimestamp(history_timestamp[i]))
                        plus_price.append(price_history[i])
                last = price_history[i]

            time.sleep(random.uniform(1.0, 3.0))

            if len(plus_times) > 0:
                ax.plot(plus_times, plus_price, color=green1, linewidth=0.8)
                ax.fill_between(plus_times, plus_price, 0, color=green2, alpha=0.25)

            if len(minus_times) > 0:
                ax.plot(minus_times, minus_price, color=red1, linewidth=0.8)
                ax.fill_between(minus_times, minus_price, 0, color=red2, alpha=0.25)

            labels = ax.get_xticklabels()
            plt.setp(labels, rotation=rotate)

            time.sleep(random.uniform(1.0, 3.0))
            plt.savefig(image_file, facecolor='#fafafa')
            plt.close()

            self._logger.info("[plot] Finish plotting profit graph in {:.2f}sec".format(time.time()-start) )

        message = '{} 損益通知 Profit:{:+.0f}'.format((datetime.utcnow()+timedelta(hours=9)).strftime('%H:%M:%S'), price_history[-1])

        self._logger.discord.send( message, image_file )
