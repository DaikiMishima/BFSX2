# coding: utf-8
#!/usr/bin/python3

#-------------参考
# https://api-doc.huobi.co.jp/#websocket
# https://huobiapi.github.io/docs/spot/v1/en/#websocket-market-data

import gzip
import json
from libs.exchanges.base_module.base_exchange import WebsocketExchange

class HuobiWebsocket(WebsocketExchange):
    
    def __init__(self, logger, subscribe={}, symbol='btcusdt'):
        self._endpoint = "wss://api-aws.huobi.pro/ws"
        self._channel_str = "ch"
        self._param = subscribe
        self._symbol = symbol
        WebsocketExchange.__init__(self,logger)

    def _message_dump(self, message):
        msg = json.loads(gzip.decompress(message).decode('utf-8'))
        if "ping" in msg:
            self.ws.send(json.dumps({"pong":msg["ping"]}) )
        return msg

    def _on_connect(self):
        if self._param.get('execution', True) : self._subscribe({"sub": f"market.{self._symbol}.trade.detail", "id":"1"},f"market.{self._symbol}.trade.detail", self._on_executions)
        if self._param.get('board', False) :    self._subscribe({"sub": f"market.{self._symbol}.depth.step0", "id":"1"}, f"market.{self._symbol}.depth.step0", self._on_board)
        if self._param.get('ticker', False) :   self._subscribe({"sub": f"market.{self._symbol}.detail", "id":"1"}, f"market.{self._symbol}.detail", self._on_ticker)

    def _on_executions(self,msg):
        self.execution.time = self._epoc_to_dt(msg['ts']/1000)
        recept_data = msg.get('tick',{}).get('data')
        self._append_latency((self._jst_now_dt().timestamp() - self.execution.time.timestamp())*1000)
        for i in recept_data:
            self._append_execution(float(i['price']),float(i['amount']),i['direction'].upper(),self.execution.time,i['tradeId'])
        self.execution.call_handlers.set()

    def _on_board(self,msg):
        self.board.time = self._epoc_to_dt(msg['ts']/1000)
        recept_data = msg.get('tick')
        self.board._initialize_dict()
        asks = self.board._update_asks(recept_data.get('asks',[]))
        bids = self.board._update_bids(recept_data.get('bids',[]))
        if asks:
            for i in asks:
                self._append_board(self.board.time, i['price'],i['size'],i['side'])
        if bids:
            for i in bids:
                self._append_board(self.board.time, i['price'], i['size'], i['side'])
        self.board.call_handlers.set()

    def _on_ticker(self,msg):
        self.ticker.time = self._epoc_to_dt(msg['ts']/1000)
        data = msg.get('tick')
        self.ticker.last = float(data.get('close',self.ticker.last))
