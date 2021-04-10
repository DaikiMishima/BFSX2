# coding: utf-8
#!/usr/bin/python3

import time
from threading import Event, Lock
from collections import deque
from .orderlist import OrderList
from libs.utils.scheduler import Scheduler
from libs.utils.jsonfile import JsonFile

# 現在のポジション・注文リスト管理クラス
class MyPosition(object):

    def __init__(self, logger, position_control_type, order_unit='BTC'):
        self._logger = logger
        self.order = OrderList(logger)
        self.position = position_control_type(logger, self.update_profitfile)
        self.daily_exec_size = 0
        self._ltp = 0

        self.lock = Lock()

        self._display_unit = order_unit

        self.file = JsonFile(self._logger)
        self._filename = ''
        self.update = Event()

        # 5秒ごとに損益を保存
        Scheduler(self._logger, interval=5, callback=self.update_profitfile)

        # 1時間ごとにカウンターを表示
        Scheduler(self._logger, interval=3600, basetime=0, callback=self._disp_stats)

    def reload_profitfile(self, filename=None):
        self._filename = filename or self._filename
        tmp_prof = self.file.reload_file(self._filename)

        # 本日の0:00:05
        jst_zero = (time.time()+32400) // 86400 * 86400 - 32395
        prof_list = [p for p in tmp_prof if p['timestamp']>=jst_zero]

        for data in prof_list:
            self.position.realized = data.get('realized',self.position.realized)
            self.position.commission = data.get('commission',self.position.commission)

        self._logger.info( '-'*100 )
        self._logger.info( " realized = {} / commission = {}".format(self.position.realized, self.position.commission)) 
        self._logger.info( '-'*100 )

        # 過去のデータは削除して上書き
        self.file.renew_file( prof_list )

    def update_profitfile(self):
        self.file.add_data({'timestamp':time.time(), 'realized':self.position.realized, 'commission':self.position.commission, 'unreal':self.position.unreal} )
        self.update.set()

    def _disp_stats(self):
        self.daily_exec_size += self.order.executed_size
        self._disp_str( "---------------------Order counts" )
        self._disp_str( "    ordered        : {}".format(self.order.ordered_count) )
        self._disp_str( "    order filled   : {}".format(self.order.filled_count) )
        self._disp_str( "    partial filled : {}".format(self.order.partially_filled_count) )
        self._disp_str( "    order cancelled: {}\n".format(self.order.canceled_count) )
        self._disp_str( "    executed volume /h  : {:.2f}{}".format(self.order.executed_size, self._display_unit) )
        self._disp_str( "    exec volume today   : {:.2f}{}".format(self.daily_exec_size, self._display_unit) )
        self._disp_str( "" )
        self.order.reset_counter()
        self._logger.discord.flush_message()

    def _disp_str(self, str):
        self._logger.info( str, send_to_discord=True)

