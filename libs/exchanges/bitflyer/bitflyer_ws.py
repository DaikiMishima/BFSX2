# coding: utf-8
#!/usr/bin/python3

import time
from secrets import token_hex
import json
from libs.exchanges.base_module.base_exchange import WebsocketExchange
from libs.exchanges.base_module.position.myposition import MyPosition
from libs.exchanges.base_module.position.position_fifo import OpenPositionFIFO

class BitflyerWebsocket(WebsocketExchange):

    def __init__(self, logger, subscribe={}, symbol='FX_BTC_JPY', testnet=False, auth=None):
        self._endpoint = "wss://ws.lightstream.bitflyer.com/json-rpc"
        self._channel_str = "channel"
        self._logger = logger
        self._param = subscribe
        self._symbol = symbol
        self._auth = auth
        self.my = MyPosition(logger, OpenPositionFIFO)
        WebsocketExchange.__init__(self,logger)
        if self._param.get('ticker', False) :
            self.ticker.best_ask = 0
            self.ticker.best_bid = 0
        if self._param.get('execution', True) :
            self.execution.spot_last = 0
            while self.execution.last==0 : 
                time.sleep(0.1)

    def units(self,value=0):
        return {'unitrate' :1,                        # 損益額をプロフィットグラフに表示する単位に変換する係数
                'title':"JPY {:+,.0f}".format(value)}  # 表示フォーマット

    def is_connected(self):
        return self._auth.auth_completed if self._auth!=None else self._connected

    def _on_connect(self):
        if self._param.get('execution', True) :
            self._subscribe({"method": "subscribe", "params":{"channel": f"lightning_executions_{self._symbol}"}}, f"lightning_executions_{self._symbol}", self._on_executions)
            if self._symbol=='FX_BTC_JPY':  # SFD算出用に現物も購読する
                self._subscribe({"method": "subscribe", "params":{"channel": "lightning_executions_BTC_JPY"}}, "lightning_executions_BTC_JPY", self._on_spot_executions)
        if self._param.get('board', False) :
            self._subscribe({"method": "subscribe", "params":{"channel": f"lightning_board_snapshot_{self._symbol}"}}, f"lightning_board_snapshot_{self._symbol}", self._on_board_snapshot)
            self._subscribe({"method": "subscribe", "params":{"channel": f"lightning_board_{self._symbol}"}}, f"lightning_board_{self._symbol}", self._on_board)
        if self._param.get('ticker', False) :
            self._subscribe({"method": "subscribe", "params":{"channel": f"lightning_ticker_{self._symbol}"}}, f"lightning_ticker_{self._symbol}", self._on_ticker)

        if self._auth!=None :
            self._auth.start_auth(self._auth_start)

    def _auth_start(self):
        timestamp = int(time.time())
        nonce = token_hex(16)
        sign = self._auth.generate_sign(self._auth.secret, ''.join([str(timestamp), nonce]))
        params = {'method': 'auth', 'params': {'api_key': self._auth.apikey, 'timestamp': timestamp, 'nonce': nonce, 'signature': sign}, 'id': 1}
        self.ws.send(json.dumps(params))

    def _message_dump(self, message):
        msg = json.loads(message)

        # auth レスポンスの処理
        if 'id' in msg and msg['id'] == 1:
            if msg.get('result',False):
                self._auth.auth_complete()
                self._subscribe({"method": "subscribe", "params":{"channel": "child_order_events"}}, "child_order_events", self._on_child_order_events)
            elif 'error' in msg :
                self._auth.retry_auth(msg["error"])
            else:
                self._logger.error( self.__class__.__name__ + " : Unknown response \n" + str(msg)+"\n" )
            return ''

        if msg.get("method") == 'channelMessage':
            msg = msg.get("params")
        return msg

    def _on_executions(self,message):
        msg = message.get("message")
        self.execution.time = self._utcstr_to_dt(msg[-1]['exec_date'])
        self._append_latency((self._jst_now_dt().timestamp() - self.execution.time.timestamp())*1000)
        for i in msg:
            self._append_execution(i['price'],i['size'],i['side'],self._utcstr_to_dt(i['exec_date']),i["buy_child_order_acceptance_id"]+'='+i["sell_child_order_acceptance_id"])
        self.my.position.ref_ltp = self.execution.last
        self.execution.call_handlers.set()

    def _on_spot_executions(self,message):
        i = message.get("message",[{}])[-1]
        self.execution.spot_last = i.get('price',self.execution.spot_last)

    @property
    def sfd(self):
        if self.execution.last >= self.execution.spot_last:
            return round(self.execution.last/self.execution.spot_last*100-100, 3) if self.execution.spot_last != 0 else 0
        else:
            return -round(self.execution.spot_last/self.execution.last*100-100, 3) if self.execution.last != 0 else 0

    def _on_board_snapshot(self,message):
        self.board._initialize_dict()
        self._on_board(message)

    def _on_board(self,message):
        self.board.time = self._jst_now_dt()
        msg = message.get("message")
        asks = self.board._update_asks(msg.get('asks',[]))
        bids = self.board._update_bids(msg.get('bids',[]))
        if asks:
            for i in asks:
                self._append_board(self.board.time, i['price'],i['size'],i['side'])
        if bids:
            for i in bids:
                self._append_board(self.board.time, i['price'], i['size'], i['side'])
        self.board.call_handlers.set()

    def _on_ticker(self,message):
        msg = message.get("message")
        self.ticker.time = self._utcstr_to_dt(msg['timestamp'])
        self.ticker.last = msg.get('ltp',self.ticker.last)
        self.ticker.best_ask = msg.get('best_ask',self.ticker.best_ask)
        self.ticker.best_bid = msg.get('best_bid',self.ticker.best_bid)

    # https://bf-lightning-api.readme.io/docs/realtime-child-order-events
    def _on_child_order_events(self,message):
        """
        {'channel': 'child_order_events', 'message': [{'product_code': 'FX_BTC_JPY', 'child_order_id': 'JFX20210226-070310-350246F', 'child_order_acceptance_id': 'JRF20210226-070300-065874', 'event_date': '2021-02-26T07:04:19.0558047Z', 'event_type': 'EXECUTION', 'exec_id': 2184727760, 'side': 'SELL', 'price': 5119848, 'size': 0.00994883, 'commission': 0, 'sfd': 0, 'outstanding_size': 0.15324826}, {'product_code': 'FX_BTC_JPY', 'child_order_id': 'JFX20210226-070310-350246F', 'child_order_acceptance_id': 'JRF20210226-070300-065874', 'event_date': '2021-02-26T07:04:19.0870571Z', 'event_type': 'EXECUTION', 'exec_id': 2184727761, 'side': 'SELL', 'price': 5119848, 'size': 0.15324826, 'commission': 0, 'sfd': 0, 'outstanding_size': 0}]}
        {'channel': 'child_order_events', 'message': [{'product_code': 'FX_BTC_JPY', 'child_order_id': 'JFX20210226-070433-408889F', 'child_order_acceptance_id': 'JRF20210226-070431-025837', 'event_date': '2021-02-26T07:04:33.9484605Z', 'event_type': 'ORDER', 'child_order_type': 'LIMIT', 'side': 'BUY', 'price': 5108402, 'size': 0.2, 'expire_date': '2021-02-26T07:05:31'}]}
        """
        with self.my.lock :
            datas = message.get('message',[])
            for d in datas:
                id = d['child_order_acceptance_id']
                if d['event_type']=='ORDER' :
                    if self.my.order.update_order( id, side=d['side'], price=d['price'], size=d['size'] ) :
                        self._logger.debug( self.__class__.__name__ + " : ORDER : " + str(d) )
                elif d['event_type']=='EXECUTION' :
                    self._logger.debug( self.__class__.__name__ + " : EXECUTION : " + str(d) )
                    if self.my.order.execution( id, side=d['side'], price=d['price'], size=d['size'], remain=d['outstanding_size'] ) :
                        self.my.position.execution( id=id, side=d['side'], price=d['price'], size=d['size'], commission=d['sfd'] )
                elif d['event_type']=='EXPIRE' :
                    if self.my.order.remove_order( id ) :
                        self._logger.debug( self.__class__.__name__ + " : EXPIRE : " + str(d) )
                elif d['event_type']=='CANCEL' :
                    if self.my.order.remove_order( id ) :
                        self._logger.debug( self.__class__.__name__ + " : CANCEL : " + str(d) )
                elif d['event_type']=='CANCEL_FAILED' :
#                    if self.my.order.remove_order( id ) :
                    if self.my.order.is_myorder( id ) :
                        self._logger.debug( self.__class__.__name__ + " : CANCEL_FAILED : " + str(d) )
                elif d['event_type']=='ORDER_FAILED' :
                    if self.my.order.is_myorder( id ) :
                        self._logger.debug( self.__class__.__name__ + " : ORDER_FAILED : " + str(d) )
                else:
                    self._logger.debug( self.__class__.__name__ + " : UNKNOWN : " + str(d) )
