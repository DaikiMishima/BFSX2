# coding: utf-8
#!/usr/bin/python3

from collections import deque
from threading import Thread, Event
from libs.exchanges.base_module.utils.time_conv import TimeConv
import traceback

# 約定情報を管理するクラス
class WebsocketExecuions(TimeConv):

    def __init__(self, logger):
        self._executions = deque()
        self.execution = ExecutionInfo(logger)
        self.execution.time = self._jst_now_dt()   #　直近のexecutions受信時刻 (datetime形式)

    def _append_execution(self, price, size, side, exec_date, id='NONE'):
        self.execution.last = price
        self._executions.append( price )

        # 最終売買履歴からbest_ask/best_bidを算出
        if side=="BUY" : self.execution.best_ask = price
        else:            self.execution.best_bid = price

        # 登録されているすべてのキューに約定履歴を突っ込む
        for exec_list, trig in self.execution._exec_que_list :
            exec_list.append({'price':price, 'size':size, 'side':side, 'exec_date':exec_date, 'id':id})


class ExecutionInfo(object):
    def __init__(self,logger):
        self._logger = logger
        self.avg_price_1s = 0             #　直近1秒の約定平均価格
        self.avg_latency_1s = 0           #　直近1秒の平均配信遅延
        self.last = self.best_ask = self.best_bid = 0
        self._exec_que_list = []
        self.call_handlers = Event()
        self.thread = Thread(target=self._wait_call_handlers)
        self.thread.daemon = True
        self.thread.start()

    def _wait_call_handlers(self):
        while True:
            flag = self.call_handlers.wait(1)
            if flag :
                self.call_handlers.clear()
            for que,trig in self._exec_que_list:
                if len(que)!=0:
                    trig.set()

    def add_handler( self, exec_que, handler ):
        trig = Event()
        self._exec_que_list.append( [exec_que, trig] )
        thread = Thread(target=self._call_handler, args=(handler, exec_que, trig))
        thread.daemon = True
        thread.start()

    def _call_handler(self, handler, exec_que, event):
        while True:
            if len(exec_que)==0 :
                flag = event.wait(1)
                if flag:
                    event.clear()
            if len(exec_que)!=0 :
                if not flag :
                    self._logger.error( "miss exec event" )
#                self._logger.debug( "exec event : call {} {}".format(handler.__module__, handler.__name__) )
                try:
                    handler()
                except Exception as e:
                    self._logger.error( e )
                    self._logger.info(traceback.format_exc())
