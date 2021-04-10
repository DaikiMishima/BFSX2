# coding: utf-8
#!/usr/bin/python3

#-------------参考
# https://www.okex.com/docs/en/#spot_ws-general

import zlib
import json
from libs.exchanges.base_module.base_exchange import WebsocketExchange

class OkexWebsocket(WebsocketExchange):
    
    def __init__(self, logger, subscribe={}, symbol='BTC-USDT'):
        self._endpoint = "wss://real.okex.com:8443/ws/v3"
        self._channel_str = "table"
        self._param = subscribe
        self._symbol = symbol
        WebsocketExchange.__init__(self,logger)
        if self._param.get('ticker', False) :
            self.ticker.best_ask = 0
            self.ticker.best_bid = 0

    def inflate(self,data):
        decompress = zlib.decompressobj(-zlib.MAX_WBITS)  # see above
        inflated = decompress.decompress(data)
        inflated += decompress.flush()
        return inflated

    def _message_dump(self, message):
        return json.loads(self.inflate(message))

    def _on_connect(self):
        if self._param.get('execution', True) : self._subscribe({"op": "subscribe", "args": [f"spot/trade:{self._symbol}"]},"spot/trade", self._on_executions)
        if self._param.get('board', False) :    self._subscribe({"op": "subscribe", "args": [f"spot/depth:{self._symbol}"]}, "spot/depth", self._on_board)
        if self._param.get('ticker', False) :   self._subscribe({"op": "subscribe", "args": [f"spot/ticker:{self._symbol}"]}, "spot/ticker", self._on_ticker)

    def _on_executions(self,msg):
        recept_data = msg.get('data')
        self.execution.time = self._utcstr_to_dt(recept_data[-1]['timestamp'])
        self._append_latency((self._jst_now_dt().timestamp() - self.execution.time.timestamp())*1000)
        for i in recept_data:
            self._append_execution(float(i['price']),float(i['size']),i['side'].upper(),self._utcstr_to_dt(i['timestamp']),i['trade_id'])
        self.execution.call_handlers.set()

    def _on_board(self,msg):
        self.board.time = self._jst_now_dt()
        recept_data = msg.get('data')
        msg_type=msg.get('action')
        asks = bids = []
        for i in recept_data :
            if i['instrument_id']!=self._symbol:
                continue
            if msg_type=='partial':
                self.board._initialize_dict()
            asks.extend(self.board._update_asks(i.get('asks',[])))
            bids.extend(self.board._update_bids(i.get('bids',[])))
        if asks:
            for i in asks:
                self._append_board(self.board.time, i['price'],i['size'],i['side'])
        if bids:
            for i in bids:
                self._append_board(self.board.time, i['price'], i['size'], i['side'])
        self.board.call_handlers.set()

    def _on_ticker(self,msg):
        data = msg.get('data')
        self.ticker.time = self._utcstr_to_dt(data[-1]['timestamp'])
        for d in data:
            self.ticker.last = float(d.get('last',self.ticker.last))
            self.ticker.best_ask = float(d.get('best_ask',self.ticker.best_ask))
            self.ticker.best_bid = float(d.get('best_bid',self.ticker.best_bid))
