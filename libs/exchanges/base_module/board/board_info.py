# coding: utf-8
#!/usr/bin/python3

from threading import Thread, Event, Lock
from sortedcontainers import SortedDict
import traceback

from libs.exchanges.base_module.board.board_info_type_a import BoardInfoTypeA
from libs.exchanges.base_module.board.board_info_type_b import BoardInfoTypeB


# 板情報を管理するクラス
class BoardInfo(BoardInfoTypeA, BoardInfoTypeB):
    def __init__(self, logger):
        self._logger = logger
        self._board_que_list = []
        self._lock = Lock()
        self._clear()
        self._event_list = []
        self.call_handlers = Event()
        self.thread = Thread(target=self._wait_call_handlers)
        self.thread.daemon = True
        self.thread.start()


    def _initialize_dict(self):
        with self._lock:
            self._clear()

    def _clear(self):
        self._asks = SortedDict()
        self._bids = SortedDict()

    def _wait_call_handlers(self):
        while True:
            flag = self.call_handlers.wait(1)
            if flag:
                self.call_handlers.clear()
            for que, trig in self._board_que_list:
                if len(que) != 0:
                    trig.set()

    def add_handler(self, board_que, handler):
        trig = Event()
        self._board_que_list.append([board_que, trig])
        thread = Thread(target=self._call_handler, args=(handler, board_que, trig))
        thread.daemon = True
        thread.start()

    def _call_handler(self, handler, board_que, event):
        while True:
            if len(board_que) == 0:
                flag = event.wait(1)
                if flag:
                    event.clear()
            if len(board_que) != 0:
                if not flag:
                    self._logger.error("miss board event")
                try:
                    handler()
                except Exception as e:
                    self._logger.error(e)
                    self._logger.info(traceback.format_exc())

    @property
    def bids(self): return self._bids.values() # bidsは買い板
    @property
    def asks(self): return self._asks.values() # askは売り板
    @property
    def best_bid(self):
        with self._lock:
            return float(self.bids[0][0]) if len(self._bids)!=0 else float(0)
    @property
    def best_ask(self):
        with self._lock:
            return float(self.asks[0][0]) if len(self._asks)!=0 else float(0)
    @property
    def mid(self): return (self.best_bid + self.best_ask)/2

