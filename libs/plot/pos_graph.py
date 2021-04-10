# coding: utf-8
#!/usr/bin/python3

from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import random
from threading import Thread
import time

# ポジショングラフをプロットするグラフ
class PositionGraph(object):
    def __init__(self, logger, stats, strategy, lock, setting={}):
        self._logger = logger
        self._stats = stats
        self._strategy = strategy
        self._lock = lock
        self.setting = setting

    def plot(self, image_file, ws ):
        if self._logger.discord.webhook!='' :
            Thread(target=self._plot, args=(image_file,ws,)).start()

    def _plot(self, image_file, ws):
        org_stats = self._stats.get_stats()
        if len(org_stats)==0 :
            return

        t=0
        stats=[]
        l=0
        p=0
        for s in org_stats:
            p=s['ltp'] if s['ltp']!=0 else p
            if p == 0 :
                continue
            s['ltp']=p
            if s['timestamp']-t>20 and time.time()-s['timestamp']<self.setting.get('period',60)*60 :
                s['lantency']=max(l,s['lantency'])
                stats.append(s)
                t=s['timestamp']
                l=0
            else:
                l=max(l,s['lantency'])
        stats.append(org_stats[-1])

        timestamp = [datetime.fromtimestamp(s['timestamp']) for s in stats]
        ltp = [round(s['ltp'],1) for s in stats]
        current_pos = [s['current_pos'] for s in stats]
        leverage = [abs(s['current_pos']) for s in stats]
        average = [(round(s['average'],1) if s['average']!=0 else s['ltp']) for s in stats]
        if self.setting.get('plot_fixed_pnl',False) :
            profit = [ws.units()['unitrate']*s['fixed_profit'] for s in stats]
        else:
            profit = [ws.units()['unitrate']*s['profit'] for s in stats]
        commission = [ws.units()['unitrate']*s['commission'] for s in stats]
        lantency_np = np.array([s['lantency'] for s in org_stats])
        lantency_std = lantency_np.std()
        lantency_mean = lantency_np.mean()
        lantency_np = np.array([s['lantency'] for s in stats])
        normal = [100000000 if s['lantency'] < lantency_mean-lantency_std*0.3 else 0 for s in stats]
        very_busy = [100000000 if s['lantency'] > lantency_mean+lantency_std*3 else 0 for s in stats]
        super_busy = [100000000 if s['lantency'] > lantency_mean+lantency_std*10 else 0 for s in stats]
        api1 = [s['api1'] for s in stats]
        api2 = [s.get('api2',0) for s in stats]
        api3 = [s.get('api3',0) for s in stats]

        self._logger.info("[plot] Start plotting position graph" )
        with self._lock :
            fig = plt.figure()
            fig.autofmt_xdate()
            fig.tight_layout()

            time.sleep(random.uniform(1.0, 3.0))
            start = time.time()

            # サブエリアの大きさの比率を変える
            gs = matplotlib.gridspec.GridSpec(nrows=2, ncols=1, height_ratios=[7, 3])
            ax1 = plt.subplot(gs[0])  # 0行0列目にプロット
            ax2 = ax1.twinx()
            ax2.tick_params(labelright=False)
            bx1 = plt.subplot(gs[1])  # 1行0列目にプロット
            bx1.tick_params(labelbottom=False)
            bx2 = bx1.twinx()

            # 上側のグラフ
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))
            ax1.set_ylim([min(ltp + average)*0.999 - (max(ltp + average) - min(ltp + average))/5, max(ltp + average)*1.001])

            ax1.plot(timestamp, ltp, label="market price")
            ax1.plot(timestamp, average, label="position average")

            ax1.bar(timestamp, normal, color='green', width=0.001, alpha=0.01)
            ax1.bar(timestamp, very_busy, color='red', width=0.001, alpha=0.1)
            ax1.bar(timestamp, super_busy, color='red', width=0.001, alpha=0.5)

            if max(api1)!=min(api1) :
                ax2.plot(timestamp, api1, label="API1", color='red')
            if max(api2)!=min(api2) :
                ax2.plot(timestamp, api2, label="API2", color='orange')
            if max(api3)!=min(api3) :
                ax2.plot(timestamp, api3, label="API3", color='brown')
            ax2.axhline(y=0, color='k', linestyle='dashed')

            ax2.set_ylim([-100, 2800])
            ax2.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(500))

            # 損益の推移
            bx1.yaxis.set_major_formatter(ticker.ScalarFormatter())
            bx1.yaxis.get_major_formatter().set_scientific(False)
            bx1.yaxis.get_major_formatter().set_useOffset(False)

            if self.setting.get('plot_fixed_pnl',False) :
                bx1.plot(timestamp, profit, label="fixed profit", color='red')
            else:
                bx1.plot(timestamp, profit, label="profit", color='red')
            if max(commission)!=min(commission) and self.setting.get('plot_commission',False) :
                bx1.plot(timestamp, commission, label="commission", color='blue')
                bx1.set_ylim([min(profit+commission)*0.99, max(profit+commission)*1.01])
            else:
                bx1.set_ylim([min(profit)*0.99, max(profit)*1.01])

            bx1.yaxis.get_major_formatter().set_useOffset(False)
            bx1.yaxis.set_major_locator(ticker.MaxNLocator(nbins=5, integer=True))

            # ポジション推移
            bx2.set_ylim([-max(leverage) * 1.2, max(leverage) * 1.2])
            bx2.bar(timestamp, current_pos, width=0.001, label="position")
            bx2.axhline(y=0, color='k', linestyle='dashed')

#            bx2.yaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(0.1))
            bx2.yaxis.set_minor_locator(ticker.MaxNLocator(nbins=5))

            bx1.patch.set_alpha(0)
            bx1.set_zorder(2)
            bx2.set_zorder(1)

            # 凡例
            h1, l1 = ax1.get_legend_handles_labels()
            h2, l2 = ax2.get_legend_handles_labels()
            h3, l3 = bx1.get_legend_handles_labels()
            h4, l4 = bx2.get_legend_handles_labels()
            ax1.legend(h1, l1, loc='upper left', prop={'size': 8})
            ax2.legend(h2, l2, loc='lower left', prop={'size': 8})
            bx1.legend(h3+h4, l3+l4, loc='upper left', prop={'size': 8})

            ax1.grid(linestyle=':')
            bx1.grid(linestyle=':')

            bx1.tick_params(axis = 'y', colors ='red')
            bx2.tick_params(axis = 'y', colors ='blue')

            plt.savefig(image_file)
            plt.close()

            self._logger.info("[plot] Finish plotting position graph in {:.2f}sec".format(time.time()-start) )

        time.sleep(random.uniform(1.0, 3.0))

        message = '{} ポジション通知 {}'.format((datetime.utcnow()+timedelta(hours=9)).strftime('%H:%M:%S'), self._strategy)
        self._logger.discord.send( message, image_file )
