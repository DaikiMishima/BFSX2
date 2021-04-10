# coding: utf-8
#!/usr/bin/python3

from collections import deque
from threading import Thread, Event
from libs.exchanges.base_module.utils.time_conv import TimeConv
import traceback
from libs.exchanges.base_module.board.board_info_group import BoardInfoGroup


# 板情報を管理するクラス
class WebsocketBoard(TimeConv):

    def __init__(self, logger):
        self._board = deque()
        self.board = BoardInformation(logger)
        self.board.time = self._jst_now_dt()   #　直近のboard受信時刻 (datetime形式)

    def _append_board(self, exec_date, price, size, side):
        self.board.last = price
        self._board.append( price )
        # 登録されているすべてのキューに約定履歴を突っ込む
        for board_list, trig in self.board._board_que_list :
            board_list.append({'price':price, 'size':size, 'side':side, 'exec_date':exec_date})


class BoardInformation(BoardInfoGroup):
    def __init__(self, logger):
        super().__init__(logger)

# テストコード
if __name__ == "__main__":
    from logging import getLogger, StreamHandler, INFO
    import time
    try:
        from .base_websocket import WebsocketConnection
    except ImportError:
        from base_websocket import WebsocketConnection

    logger = getLogger(__name__)
    handler = StreamHandler()
    handler.setLevel(INFO)
    logger.setLevel(INFO)
    logger.addHandler(handler)

    class orderbook_ws(WebsocketBoard,WebsocketConnection):
        _endpoint = "wss://stream.binance.com/ws/btcusdt@depth@100ms"
        def __init__(self,logger):
            WebsocketBoard.__init__(self,logger)
            WebsocketConnection.__init__(self,logger)
        def _message(self, msg):
            self.board._update_bids(msg['b'])
            self.board._update_asks(msg['a'])

    ws = orderbook_ws(logger)

    while True:
        try:
            logger.info( "{:.2f}".format(ws.board.mid) )
            time.sleep(1)

        except KeyboardInterrupt:
            ws.stop()
            break
