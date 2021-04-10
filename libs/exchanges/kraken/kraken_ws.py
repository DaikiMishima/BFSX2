# coding: utf-8
#!/usr/bin/python3

#-------------参考
#https://docs.kraken.com/websockets/

import json
from libs.exchanges.base_module.base_exchange import WebsocketExchange

class KrakenWebsocket(WebsocketExchange):

    def __init__(self, logger, subscribe={}, symbol='XBT/USD'):
        self._endpoint = "wss://ws.kraken.com/"
        self._channel_str = "event"
        self._side_str = {'b':"BUY", 's':"SELL"}
        self._param = subscribe
        self._symbol = symbol
        WebsocketExchange.__init__(self,logger)
        if self._param.get('ticker', False) :
            self.ticker.best_ask = 0
            self.ticker.best_bid = 0
        self._handler["heartbeat"]=self._ignore

    def _ignore(self,msg):
        pass

    def _message_dump(self, message):
        msg = json.loads(message)
        if type(msg)==list :
            msg = {self._channel_str:msg[-2], "data":msg}
        return msg

    def _on_connect(self):
        if self._param.get('execution', True) : self._subscribe({"event": "subscribe", "pair": [self._symbol], "subscription": {"name": "trade"}},"trade", self._on_executions)
        if self._param.get('board', False) :    self._subscribe({"event": "subscribe", "pair": [self._symbol], "subscription": {"depth":100, "name": "book"}},"book-100", self._on_board)
        if self._param.get('ticker', False) :   self._subscribe({"event": "subscribe", "pair": [self._symbol], "subscription": {"name": "ticker"}},"ticker", self._on_ticker)

    def _on_executions(self,msg):
        recept_data = msg.get('data')[1]
        self.execution.time = self._epoc_to_dt(float(recept_data[-1][2]))
        self._append_latency((self._jst_now_dt().timestamp() - self.execution.time.timestamp())*1000)
        for i in recept_data:
            self._append_execution(float(i[0]),float(i[1]),self._side_str[i[3]],self._epoc_to_dt(float(i[2])))
        self.execution.call_handlers.set()

    def _on_board(self,msg):
        recept_data = msg.get('data')
        asks_book = bids_book = []
        for d in recept_data:
            if type(d)!=dict :
                continue
            asks=d.get('a',[])
            bids=d.get('b',[])
            if len(asks)!=0 :
                self.board.time = self._epoc_to_dt(float(asks[-1][2]))                                             
                asks_book.extend(self.board._update_asks(asks))
            elif len(bids)!=0 :
                self.board.time = self._epoc_to_dt(float(bids[-1][2]))                                             
                bids_book.extend(self.board._update_bids(bids))
        if asks_book:
            for i in asks_book:
                self._append_board(self.board.time, i['price'],i['size'],i['side'])
        if bids_book:
            for i in bids_book:
                self._append_board(self.board.time, i['price'], i['size'], i['side'])
        self.board.call_handlers.set()

    def _on_ticker(self,msg):
        recept_data = msg.get('data')[1]
        self.ticker.time = self._jst_now_dt()
        self.ticker.last = float(recept_data.get('c',[self.ticker.last,0])[0])
        self.ticker.best_ask = float(recept_data.get('a',[self.ticker.best_ask,0])[0])
        self.ticker.best_bid = float(recept_data.get('b',[self.ticker.best_bid,0])[0])
