# coding: utf-8
#!/usr/bin/python3

#-------------参考
#https://docs.ftx.com/#websocket-api

import time
import json
from threading import Thread
from libs.exchanges.base_module.base_exchange import WebsocketExchange

class FtxWebsocket(WebsocketExchange):

    def __init__(self, logger, subscribe={}, symbol='BTC-PERP'):
        self._endpoint = "wss://ftx.com/ws/"
        self._channel_str = "channel"
        self._param = subscribe
        self._symbol = symbol
        WebsocketExchange.__init__(self,logger)
        if self._param.get('ticker', False) :
            self.ticker.best_ask = 0
            self.ticker.best_bid = 0
        self._heart_beat_th = Thread(target=self._heart_beat)
        self._heart_beat_th.daemon = True
        self._heart_beat_th.start()

    def _heart_beat(self):
        while not self._stop:
            if self._connected :
                self.ws.send(json.dumps({'op': 'ping'}))
            time.sleep(15)

    def _on_connect(self):
        if self._param.get('execution', True) : self._subscribe({"op": "subscribe", 'channel': 'trades', 'market': self._symbol},"trades", self._on_executions)
        if self._param.get('board', False) :    self._subscribe({"op": "subscribe", 'channel': 'orderbook', 'market': self._symbol},"orderbook", self._on_board)
        if self._param.get('ticker', False) :   self._subscribe({"op": "subscribe", 'channel': 'ticker', 'market': self._symbol},"ticker", self._on_ticker)
        return

    def _on_executions(self,msg):
        recept_data = msg.get('data')
        if recept_data==None : return
        self.execution.time = self._utcstr_to_dt(recept_data[-1]['time'])
        self._append_latency((self._jst_now_dt().timestamp() - self.execution.time.timestamp())*1000)
        for i in recept_data:
            self._append_execution(i['price'],i['size'],i['side'].upper(),self._utcstr_to_dt(i['time']),i['id'])
        self.execution.call_handlers.set()

    def _on_board(self,msg):
        recept_data = msg.get('data')
        if recept_data==None : return
        self.board.time = self._epoc_to_dt(recept_data['time'])
        msg_type=msg.get('type')    
        if msg_type=='partial' :
            self.board._initialize_dict()
            asks = self.board._update_asks(recept_data.get('asks',[]))
            bids = self.board._update_bids(recept_data.get('bids',[]))
        elif msg_type=='update' :
            asks = self.board._update_asks(recept_data.get('asks',[]))
            bids = self.board._update_bids(recept_data.get('bids',[]))
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
        recept_data = msg.get('data')
        if recept_data==None : return
        self.ticker.time = self._epoc_to_dt(recept_data['time'])
        self.ticker.last = recept_data.get('last',self.ticker.last)
        self.ticker.best_ask = recept_data.get('ask',self.ticker.best_ask)
        self.ticker.best_bid = recept_data.get('bid',self.ticker.best_bid)
