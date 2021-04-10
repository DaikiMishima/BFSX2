# coding: utf-8
#!/usr/bin/python3

#-------------参考
# https://api.coin.z.com/docs/#ws-ticker

from threading import Thread, Event
import time
from libs.exchanges.base_module.base_exchange import WebsocketExchange
from libs.exchanges.base_module.position.myposition import MyPosition
from libs.exchanges.base_module.position.position_gross import OpenPositionGross
from libs.exchanges.gmo.gmo_private_ws import GmoWebsocketPrivate

class GmoWebsocket(WebsocketExchange):

    def __init__(self, logger, subscribe={}, symbol='BTC_JPY', testnet=False, auth=None):
        self._endpoint = "wss://api.coin.z.com/ws/public/v1"
        self._channel_str = "channel"
        self._logger = logger
        self._param = subscribe
        self._symbol = symbol
        self._auth = auth
        if self._auth!=None :
            self.reconnect_event = Event()
            self._private_ws = GmoWebsocketPrivate(logger, auth, self.reconnect_event)

            self.check_th = Thread(target=self._check_private_ws)
            self.check_th.daemon = True
            self.check_th.start()
        else:
            self._my = MyPosition(logger, OpenPositionGross)
        WebsocketExchange.__init__(self, logger)
        if self._param.get('ticker', False) :
            self.ticker.best_ask = 0
            self.ticker.best_bid = 0

    def units(self,value=0):
        return {'unitrate' :1,                        # 損益額をプロフィットグラフに表示する単位に変換する係数
                'title':"JPY {:+,.0f}".format(value)}  # 表示フォーマット

    def is_connected(self):
        return self._private_ws.is_connected() if self._auth!=None else self._connected

    @property
    def my(self):
        return self._private_ws.my if self._auth!=None else self._my

    def _on_connect(self):
        if self._param.get('execution', True) : 
            self._subscribe({"command": "subscribe", "channel": "trades", "symbol": self._symbol, "option": "TAKER_ONLY"},"trades", self._on_executions)
            time.sleep(2)
        if self._param.get('board', False) : 
            self._subscribe({"command": "subscribe", "channel": "orderbooks", "symbol": self._symbol},"orderbooks", self._on_board_snapshot)
            time.sleep(2)
        if self._param.get('ticker', False) : 
            self._subscribe({"command": "subscribe", "channel": "ticker", "symbol": self._symbol},"ticker", self._on_ticker)
            self.ticker.best_ask = 0
            self.ticker.best_bid = 0
            time.sleep(2)

    def _on_executions(self,msg):
        self.execution.time = self._utcstr_to_dt(msg['timestamp'])
        self._append_latency((self._jst_now_dt().timestamp() - self.execution.time.timestamp())*1000)
        self._append_execution(int(msg['price']),float(msg['size']),msg['side'],self.execution.time)
        self.execution.call_handlers.set()
        self.my.position.ref_ltp = self.execution.last

    def _on_board_snapshot(self,msg):
        self.board._initialize_dict()
        self.board.time = self._utcstr_to_dt(msg['timestamp'])
        asks = self.board._update_asks(msg.get('asks',[]))
        bids = self.board._update_bids(msg.get('bids',[]))
        if asks:
            for i in asks:
                self._append_board(self.board.time, i['price'],i['size'],i['side'])
        if bids:
            for i in bids:
                self._append_board(self.board.time, i['price'], i['size'], i['side'])
        self.board.call_handlers.set()

    def _on_ticker(self,msg):
        self.ticker.time = self._utcstr_to_dt(msg['timestamp'])
        self.ticker.last = int(msg.get('last',self.ticker.last))
        self.ticker.best_ask = int(msg.get('ask',self.ticker.best_ask))
        self.ticker.best_bid = int(msg.get('bid',self.ticker.best_bid))

    def _check_private_ws(self):
        while True:
            self.reconnect_event.clear()
            self._logger.debug( "wait until re-connect event" )
            self.reconnect_event.wait()
            self._logger.debug( "re-connect event occured" )
            self._private_ws.stop() # 念のため
            time.sleep(2)
            self._private_ws.re_connect()
            self._logger.info( "Start new Private ws : {}".format(self._private_ws) )
