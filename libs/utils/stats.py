# coding: utf-8
#!/usr/bin/python3

from copy import deepcopy
import time
from libs.utils.jsonfile import JsonFile
from libs.utils.scheduler import Scheduler

# 様々な統計データを集計するクラス
class Stats(object):
    def __init__(self, logger, exchange):
        self._logger = logger
        self._ws, self._api = (exchange)

        self._ws.add_stats = self.add_stats
        self._ws.daily_reset = self.daily_reset

        self.file = JsonFile(self._logger)
        self._filename = ''
        self._stats_list=[]

        Scheduler(self._logger, interval=60, basetime=0, callback=self._add_stats)
        Scheduler(self._logger, interval=86400, basetime=1, callback=self._daily_reset)

    def _add_stats(self):
        stat = self._ws.add_stats()
        self._stats_list.append(stat)
        self.file.add_data(stat)

    def _daily_reset(self):
        self._ws.add_stats(keep=True) # 日次の最後を保存
        self._ws.daily_reset() # wsに登録されているリセット関数を呼び出す（基本はこのクラスのself.daily_resetだが、pos_server稼働時にはオーバーライドされたdaily_resetになる)
        self._stats_list=[]

    def reload_statsfile(self, filename=None):
        self._filename = filename or self._filename
        tmp_stats = self.file.reload_file(self._filename)

        # 本日の0:00:05
        jst_zero = (time.time()+32400) // 86400 * 86400 - 32395

        # 昨日以前のデータは１時間に１個に間引く
        ts=0
        past_stats = []
        for s in tmp_stats:
            if (ts+3600 <= s['timestamp'] or s.get('keep',False)) and s['timestamp']<jst_zero :
                past_stats.append(s)
                ts = s['timestamp']
            
        # 本日分 (0:00:05以降)
        self._stats_list = [s for s in tmp_stats if s['timestamp']>=jst_zero]

        # 過去のデータを上書き
        self.file.renew_file( past_stats+self._stats_list )

        if len(self._stats_list)!=0 :
            self._ws.my.order.executed_size = self._stats_list[-1].get('exec_vol',0)
            self._ws.my.daily_exec_size = self._stats_list[-1].get('exec_vol_day',0)

    def get_stats(self):
        return deepcopy(self._stats_list)

    def get_all_stats(self):
        return self.file.reload_file(self._filename)

    # 以下の関数はpos_serverの時には置き換え
    def add_stats(self, keep=False):
        return {
               'timestamp': time.time(),

               'ltp': self._ws.execution.last,
               'current_pos': self._ws.my.position.size ,
               'average': self._ws.my.position.average_price,

               'realized': self._ws.my.position.realized,
               'commission': self._ws.my.position.commission,
               'unreal': self._ws.my.position.unreal,

               'profit': self._ws.my.position.profit,
               'fixed_profit': self._ws.my.position.fixed_profit,

               'lantency': self._ws.execution.avg_latency_1s,
               'api1': self._api.api_remain1 if hasattr(self._api,'api_remain1') else 300 ,
               'api2': self._api.api_remain2 if hasattr(self._api,'api_remain2') else 300 ,
               'api3': self._api.api_remain3 if hasattr(self._api,'api_remain3') else 300 ,

               'exec_vol': self._ws.my.order.executed_size,
               'exec_vol_day': self._ws.my.daily_exec_size,

               'keep':keep,
               }

    def daily_reset(self):
        # ファイルを再構成して過去のデータは１時間単位に間引く
        self.reload_statsfile()
        self._ws.my.reload_profitfile()

        self._ws.my.position.realized = -self._ws.my.position.unreal
        self._ws.my.position.commission = 0
        self._ws.my.daily_exec_size = 0
