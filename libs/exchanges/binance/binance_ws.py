# coding: utf-8
#!/usr/bin/python3

#-------------参考
# https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md

from libs.exchanges.base_module.base_exchange import WebsocketExchange

class BinanceWebsocket(WebsocketExchange):

    def __init__(self, logger, subscribe={}, symbol='btcusdt'):
        self._endpoint = "wss://fstream.binance.com/ws/btcusdt"          # BinanceFeatures
        self._channel_str = "e"
        self._param = subscribe
        WebsocketExchange.__init__(self,logger)

    def _on_connect(self):
        if self._param.get('execution', True) : self._subscribe({"method": "SUBSCRIBE", "params": ["btcusdt@trade"], "id": 1}, "trade", self._on_executions)
        if self._param.get('board', False) :    self._subscribe({"method": "SUBSCRIBE", "params": ["btcusdt@depth@100ms"], "id": 1}, "depthUpdate", self._on_board)
        if self._param.get('ticker', False) :   self._subscribe({"method": "SUBSCRIBE", "params": ["btcusdt@ticker"], "id": 1}, "24hrTicker", self._on_ticker)

    def _on_executions(self,msg):
        self.execution.time = self._epoc_to_dt(int(msg['T'])/1000)
        self._append_execution(float(msg['p']),float(msg['q']),"SELL" if msg['m'] else "BUY", self._epoc_to_dt(int(msg['T'])/1000), msg['t'])
        self._append_latency(self._jst_now_dt().timestamp()*1000 - msg['T'])
        self.execution.call_handlers.set()

    def _on_board(self,msg):
        self.board.time = self._epoc_to_dt(int(msg['E'])/1000)
        asks = self.board._update_asks(msg.get('a',[]))
        bids = self.board._update_bids(msg.get('b',[]))
        if asks:
            for i in asks:
                self._append_board(self.board.time, i['price'],i['size'],i['side'])
        if bids:
            for i in bids:
                self._append_board(self.board.time, i['price'], i['size'], i['side'])
        self.board.call_handlers.set()

    def _on_ticker(self,msg):
        self.ticker.time = self._epoc_to_dt(int(msg['E'])/1000)
        self.ticker.last = float(msg.get('c',0))
