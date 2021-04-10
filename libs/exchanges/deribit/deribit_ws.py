# coding: utf-8
#!/usr/bin/python3

#-------------参考
# https://docs.deribit.com/?python#json-rpc
#https://docs.deribit.com/v2.test/#subscriptions

import json
from libs.exchanges.base_module.base_exchange import WebsocketExchange

class DeribitWebsocket(WebsocketExchange):
    
    def __init__(self, logger, subscribe={}, symbol='BTC-PERPETUAL'):
        self._endpoint = "wss://www.deribit.com/ws/api/v2"
        self._channel_str = "channel"
        self._param = subscribe
        self._symbol = symbol
        WebsocketExchange.__init__(self,logger)
        if self._param.get('ticker', False) :
            self.ticker.best_ask = 0
            self.ticker.best_bid = 0
            self.ticker.open_interest = 0
        self._handler["ignore"]=self._ignore

    def _ignore(self,msg):
        pass

    def _message_dump(self, message):
        msg = json.loads(message)
        if msg.get("method") == 'subscription':
            msg = msg.get("params")
        elif msg.get("method") == 'heartbeat':
            msg = {self._channel_str:"heartbeat"}
        elif "method" not in msg:
            msg = {self._channel_str:"ignore"}
        return msg

    def _respoce(self,msg):
        self.ws.send(json.dumps({"jsonrpc": "2.0", "id": 5555, "method": "public/test"}))

    def _on_connect(self):
        self._subscribe({"jsonrpc": "2.0", "id": 1111, "method": "public/set_heartbeat", "params": {"interval" : 30}},"heartbeat", self._respoce)
        if self._param.get('execution', True) : self._subscribe({"jsonrpc": "2.0", "id": 2222, "method": "public/subscribe", "params": {"channels": [f"trades.{self._symbol}.raw"]}},f"trades.{self._symbol}.raw", self._on_executions)
        if self._param.get('board', False) :    self._subscribe({"jsonrpc": "2.0", "id": 3333, "method": "public/subscribe", "params": {"channels": [f"book.{self._symbol}.raw"]}}, f"book.{self._symbol}.raw", self._on_board)
        if self._param.get('ticker', False) :   self._subscribe({"jsonrpc": "2.0", "id": 4444, "method": "public/subscribe", "params": {"channels": [f"ticker.{self._symbol}.raw"]}}, f"ticker.{self._symbol}.raw", self._on_ticker)

    def _on_executions(self,msg):
        recept_data = msg.get('data')
        self.execution.time = self._epoc_to_dt(int(recept_data[-1]['timestamp'])/1000)
        self._append_latency((self._jst_now_dt().timestamp() - self.execution.time.timestamp())*1000)
        for i in recept_data:
            self._append_execution(i['price'],i['amount'],i['direction'].upper(),self._epoc_to_dt(int(i['timestamp'])/1000),i['trade_id'])
        self.execution.call_handlers.set()

    def _on_board(self,msg):
        recept_data = msg.get('data')
        msg_type=recept_data.get('type')
        self.board.time = self._epoc_to_dt(int(recept_data['timestamp'])/1000)
        if msg_type=='snapshot':
            self.board._initialize_dict()
            asks = self.board._update_asks([[a[1],a[2]/a[1]] for a in recept_data.get('asks',[])])
            bids = self.board._update_bids([[b[1],b[2]/b[1]] for b in recept_data.get('bids',[])])
        elif msg_type=='change' :
            asks = self.board._update_asks([[a[1],a[2]/a[1]] for a in recept_data.get('asks',[])])
            bids = self.board._update_bids([[b[1],b[2]/b[1]] for b in recept_data.get('bids',[])])
        else:
            self.board.call_handlers.set()
            return
        if asks:
            for i in asks:
                self._append_board(self.board.time, i['price'],i['size'],i['side'])
        if bids:
            for i in bids:
                self._append_board(self.board.time, i['price'], i['size'], i['side'])
        self.board.call_handlers.set()

    def _on_ticker(self,msg):
        data = msg.get('data')
        self.ticker.time = self._epoc_to_dt(int(data['timestamp'])/1000)
        self.ticker.last = float(data.get('last_price',self.ticker.last))
        self.ticker.best_ask = float(data.get('best_ask_price',self.ticker.best_ask))
        self.ticker.best_bid = float(data.get('best_bid_price',self.ticker.best_bid))
        self.ticker.open_interest = float(data.get('open_interest',self.ticker.open_interest))
