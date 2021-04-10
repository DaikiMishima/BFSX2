# coding: utf-8
#!/usr/bin/python3

#-------------参考
# https://www.bitmex.com/app/wsAPI

from libs.exchanges.base_module.base_exchange import WebsocketExchange

class BitmexWebsocket(WebsocketExchange):
    
    def __init__(self, logger, subscribe={}, symbol='XBTUSD'):
        self._endpoint = "wss://www.bitmex.com/realtime"
        self._channel_str = "table"
        self._param = subscribe
        self._symbol = symbol
        WebsocketExchange.__init__(self,logger)
        if self._param.get('ticker', False) :
            self.ticker.best_ask = 0
            self.ticker.best_bid = 0
            self.ticker.open_interest = 0

    def _on_connect(self):
        if self._param.get('execution', True) : self._subscribe({"op": "subscribe", "args": [f"trade:{self._symbol}"]},"trade", self._on_executions)
        if self._param.get('board', False) :    self._subscribe({"op": "subscribe", "args": [f"orderBookL2:{self._symbol}"]}, "orderBookL2", self._on_board)
        if self._param.get('ticker', False) :   self._subscribe({"op": "subscribe", "args": [f"instrument:{self._symbol}"]}, "instrument", self._on_ticker)

    def _on_executions(self,msg):
        recept_data = msg.get('data')
        self.execution.time = self._utcstr_to_dt(recept_data[-1]['timestamp'])
        self._append_latency((self._jst_now_dt().timestamp() - self.execution.time.timestamp())*1000)
        for i in recept_data:
            self._append_execution(i['price'],i['size'],i['side'].upper(),self._utcstr_to_dt(i['timestamp']),i['trdMatchID'])
            # print('{}{}{}{}{}'.format(i['price'],i['size'],i['side'].upper(),self._utcstr_to_dt(i['timestamp']),i['trdMatchID']))

        self.execution.call_handlers.set()

    def _on_board(self,msg):
        self.board.time = self._jst_now_dt()
        recept_data = msg.get('data')
        msg_type = msg.get('action')
        if msg_type == 'partial':
            self.board._initialize_dict()
            board_list = self.board._insert(recept_data)
        elif msg_type=='insert' :
            board_list = self.board._insert(recept_data)
        elif msg_type=='delete' :
            board_list = self.board._delete(recept_data)
        elif msg_type=='update' :
            board_list = self.board._change(recept_data)
        else:
            return
        for i in board_list:
            self._append_board(self.board.time, i['price'],i['size'],i['side'])
        self.board.call_handlers.set()

    def _on_ticker(self,msg):
        data = msg.get('data')
        self.ticker.time = self._utcstr_to_dt(data[-1]['timestamp'])
        for d in data:
            self.ticker.last = float(d.get('lastPrice',self.ticker.last))
            self.ticker.best_ask = float(d.get('askPrice',self.ticker.best_ask))
            self.ticker.best_bid = float(d.get('bidPrice',self.ticker.best_bid))
            self.ticker.open_interest = float(d.get('openInterest',self.ticker.open_interest))
