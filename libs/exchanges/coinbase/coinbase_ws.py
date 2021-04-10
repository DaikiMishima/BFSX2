# coding: utf-8
#!/usr/bin/python3

#-------------参考
#https://docs.pro.coinbase.com/#websocket-feed

from libs.exchanges.base_module.base_exchange import WebsocketExchange

class CoinbaseWebsocket(WebsocketExchange):

    def __init__(self, logger, subscribe={}, symbol='BTC-USD'):
        self._endpoint = "wss://ws-feed.pro.coinbase.com"
        self._channel_str = "type"
        self._param = subscribe
        self._symbol = symbol
        WebsocketExchange.__init__(self,logger)
        if self._param.get('execution', True) or self._param.get('ticker', False) :
            self.ticker.best_ask = 0
            self.ticker.best_bid = 0

    def _on_connect(self):
        if self._param.get('board', False) :
            self._subscribe({"type": "subscribe", "channels": [{ "name": "level2"}],"product_ids": [self._symbol]},"snapshot", self._on_board)
            self._subscribe({"type": "subscribe", "channels": [{ "name": "level2"}],"product_ids": [self._symbol]},"l2update", self._on_board)
        if self._param.get('execution', True) or self._param.get('ticker', False) :
            self._subscribe({"type": "subscribe", "channels": [{ "name": "ticker"}],"product_ids": [self._symbol]},"ticker", self._on_ticker)

    def _on_board(self,msg):
        msg_type=msg.get('type')    
        if msg_type=='snapshot' :
            self.board._initialize_dict()
            asks = self.board._update_asks(msg.get('asks',[]))
            bids = self.board._update_bids(msg.get('bids',[]))
        elif msg_type=='l2update' :
            self.board.time = self._utcstr_to_dt(msg['time'])
            changes=msg.get('changes')
            asks = self.board._update_asks([[a[1],a[2]] for a in changes if a[0]=='sell'])
            bids = self.board._update_bids([[b[1],b[2]] for b in changes if b[0]=='buy'])
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
        self.ticker.time = self._utcstr_to_dt(msg['time'])
        self.ticker.last = float(msg.get('price',self.ticker.last))
        self.ticker.best_ask = float(msg.get('best_ask',self.ticker.best_ask))
        self.ticker.best_bid = float(msg.get('best_bid',self.ticker.best_bid))

        self.execution.time = self.ticker.time
        self._append_latency((self._jst_now_dt().timestamp() - self.execution.time.timestamp())*1000)
        self._append_execution(float(msg['price']),float(msg['last_size']),msg['side'].upper(),self.ticker.time,msg['trade_id'])
        self.execution.call_handlers.set()
