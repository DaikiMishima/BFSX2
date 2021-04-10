# coding: utf-8
#!/usr/bin/python3

from collections import deque
from threading import Thread
import time
from libs.exchanges.base_module.execution.base_execution import WebsocketExecuions as WebsocketExecuionsBase

# 約定情報を管理する基本クラスに 1秒ごとの平均価格と平均配信遅延を集計する機能を追加したクラス
class WebsocketExecuions(WebsocketExecuionsBase):

    def __init__(self, logger):
        WebsocketExecuionsBase.__init__(self,logger)
        self._logger = logger
        self._latency = deque()
        self._stop = False
        self._update_th = Thread(target=self._update_ltp)
        self._update_th.daemon = True
        self._update_th.start()

    def _append_latency(self, latency):
        self._latency.append( latency )

    def _mean(self,q) : return sum(q) / (len(q) + 1e-7)

    # 1秒ごとに平均価格と平均配信遅延を集計するスレッド
    def _update_ltp(self):
        while not self._stop:
            time.sleep(1)
            if len(self._executions)!=0 :
                self.execution.avg_price_1s = self._mean(self._executions)
                self.execution.avg_latency_1s = self._mean(self._latency)
                self._executions.clear()
                self._latency.clear()
