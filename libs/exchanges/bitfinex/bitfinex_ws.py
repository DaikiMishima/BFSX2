# coding: utf-8
# !/usr/bin/python3

# -------------参考
# https://docs.bitfinex.com/docs/ws-general

from libs.exchanges.base_module.base_exchange import WebsocketExchange


class BitfinexWebsocket(WebsocketExchange):

    def __init__(self, logger, subscribe={}, symbol='tBTCUSD'):
        self._endpoint = "wss://api-pub.bitfinex.com/ws/2"
        self._channel_str = "chanel"
        self._param = subscribe
        self._symbol = symbol
        WebsocketExchange.__init__(self, logger)
        if self._param.get('ticker', False):
            self.ticker.best_ask = 0
            self.ticker.best_bid = 0
            self.ticker.open_interest = 0

    def _on_connect(self):
        if self._param.get('execution', True) :
            self._subscribe({"event": "subscribe", "channel": 'trades', 'symbol': self._symbol}, 'trades', self._on_executions)
        if self._param.get('board', False):    self._subscribe(
            {"event": "subscribe", "channel": 'book', "prec": "R0", 'symbol': self._symbol}, 'book', self._on_board)
        if self._param.get('ticker', False):   self._subscribe(
            {"event": "subscribe", "channel": 'ticker', 'symbol': self._symbol},'ticker', self._on_ticker)

    def _on_executions(self, msg):
        recept_data = msg['trade']
        self.execution.time = self._epoc_to_dt(int(recept_data[1])/1000)
        self._append_latency((self._jst_now_dt().timestamp() - self.execution.time.timestamp()) * 1000)
        side = 'BUY' if recept_data[2] > 0 else 'SELL'
        self._append_execution(recept_data[3], abs(recept_data[2]), side, self.execution.time, recept_data[0])
        self.execution.call_handlers.set()

    def _on_board(self, msg):
        self.board.time = self._jst_now_dt()
        msg_data=msg.get('data')
        board_list = []
        action = self._message_action(msg_data)
        if action == 'partial':
            self.board._initialize_dict()
            board_list.extend(self.board._insert_usd(msg_data))
        elif action == 'insert':
            board_list.extend(self.board._insert_usd(msg_data))
        elif action == 'delete':
            board_list.extend(self.board._delete(msg_data))
        elif action == 'change':
            board_list.extend(self.board._change_usd(msg_data))
        else:
            return
        for i in board_list:
            self._append_board(self.board.time, i['price'],i['size'],i['side'])
        self.board.call_handlers.set()

    def _on_ticker(self, msg):
        data = msg.get('data')
        self.ticker.time = self._utcstr_to_dt(data[-1]['timestamp'])
        for d in data:
            self.ticker.last = float(d.get('lastPrice', self.ticker.last))
            self.ticker.best_ask = float(d.get('askPrice', self.ticker.best_ask))
            self.ticker.best_bid = float(d.get('bidPrice', self.ticker.best_bid))
            self.ticker.open_interest = float(d.get('openInterest', self.ticker.open_interest))

    def _message_action(self, msg):
        if len(msg) > 1:
            return 'partial'
        key = msg[0]['id'] in self.board._asks or msg[0]['id'] in self.board._bids
        if key and not msg[0]['id']:
            return 'change'
        elif not msg[0]['price']:
            return 'delete'
        else:
            return 'insert'

