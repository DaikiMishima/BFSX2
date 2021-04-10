# coding: utf-8
#!/usr/bin/python3

from copy import deepcopy
from threading import Thread
import time
import traceback

class RestAPIExchange(object):

    def __init__(self, logger, symbol, auth=None, position=None, timeout=None):
        self._logger = logger
        self.symbol = symbol
        self._auth = auth
        self._position = position
        self._timeout = timeout

        self.HttpAccessTime = time.time()

        # 取引制限
        self.PendingUntil = time.time()
        self._noTrade = False
        self.close_while_noTrade = False

        # 自動キャンセル実現のためのスレッド
        self._stop = False
        cancel = Thread(target=self._cancel_thread, args=())
        cancel.daemon = True
        cancel.start()

    def _cancel_thread(self):
        while not self._stop:
            time.sleep(0.3)
            if self._position and hasattr(self._position,'order') :
                # オーダーの自動キャンセル
                try:
                    order_dict = deepcopy(self._position.order.order_dict)
                    cancel = [o for o in order_dict.items() if o[1]['expire']<time.time()]
                    for id,value in cancel:
                        self.cancelorder(id)
                        self._logger.debug('        in orderlist : {}'.format(value))
                        self._logger.info('        Cancel automatically : [{}]'.format(id))
                except Exception as e:
                    self._logger.error("Error occured at _cancel_thread: {}".format(e))
                    self._logger.info(traceback.format_exc())

    def stop(self):
        self._logger.debug( "Stop thread {}".format(self) )
        self._stop = True
        retry = 3
        while len(self._position.order.order_dict)!=0 and retry>0:
            order_dict = deepcopy(self._position.order.order_dict)
            for id,value in order_dict.items():
                self._logger.info('        Cancel order [{}]'.format(id))
                self._logger.debug('{}'.format(value))
                self._logger.debug('       '.format(self.cancelorder(id)))
            retry -=1
            for i in range(10):
                if len(self._position.order.order_dict)==0 :
                    break
                time.sleep(0.5)

    @property
    def noTrade(self):
        return self._noTrade

    @noTrade.setter
    def noTrade(self, value):
        if value == False:
            self._noTrade = False
            return
        elif self._noTrade == False and self.close_while_noTrade :
            self.close_position()
        self._noTrade = True

    def close_position(self):
        current_pos = self._position.position.size
        if round(current_pos,8)==0:
            return {'stat': 0, 'msg': ""}
        if current_pos>0 :
            res = self.sendorder(order_type='MARKET', side='SELL', size=current_pos)
            self.PendingUntil = time.time()+30
            return res
        else :
            res = self.sendorder(order_type='MARKET', side='BUY', size=-current_pos)
            self.PendingUntil = time.time()+30
            return res
