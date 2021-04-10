# coding: utf-8
#!/usr/bin/python3

#-------------参考
#https://github.com/bybit-exchange/bybit-official-api-docs/blob/master/en/websocket.md

import time
import json
from threading import Thread
from libs.exchanges.base_module.base_exchange import WebsocketExchange
from libs.exchanges.base_module.position.myposition import MyPosition
from libs.exchanges.base_module.position.position_ave import OpenPositionKeepAve

class BybitWebsocket(WebsocketExchange):

    def __init__(self, logger, subscribe={}, symbol='BTCUSD', testnet=False, auth=None):
        if testnet :
            self._endpoint = "wss://stream-testnet.bybit.com/realtime"
        else:
            self._endpoint = "wss://stream.bybit.com/realtime"
        self._channel_str = "topic"
        self._param = subscribe
        self._symbol = symbol
        self._auth = auth
        self.connected_channel={}
        self.my = MyPosition(logger, OpenPositionKeepAve, order_unit='USD')
        WebsocketExchange.__init__(self,logger)
        if self._param.get('ticker', False) :
            self.ticker.open_interest = 0
        self._heart_beat_th = Thread(target=self._heart_beat)
        self._heart_beat_th.daemon = True
        self._heart_beat_th.start()

    def units(self,value=0):
        return {'unitrate' :self.execution.last,        # 損益額をプロフィットグラフに表示する単位に変換する係数
                'title':"USD {:+,.2f}".format(value)}   # 表示フォーマット

    def is_connected(self):
        return (self._auth.auth_completed and
                self.connected_channel.get("position",False) and
                self.connected_channel.get("execution",False) and
                self.connected_channel.get("order",False)) if self._auth!=None else self._connected

    def _message_dump(self, message):
        msg =json.loads(message)
        if 'success' in msg :
            if msg['success'] :
                if msg['request']['op']=='auth':
                    self._auth.auth_complete()
                    self._subscribe({"op": "subscribe", "args": ["position"]},"position", self._on_my_position)
                    self._subscribe({"op": "subscribe", "args": ["execution"]},"execution", self._on_my_execution)
                    self._subscribe({"op": "subscribe", "args": ["order"]},"order", self._on_my_order)
                if msg['request']['op']=='subscribe':
                    for channel in msg['request']['args']:
                        self.connected_channel[channel]=True
            else:
                if msg['request']['op']=='auth':
                    self._auth.retry_auth(msg["ret_msg"])
                else:
                    self._logger.error( self.__class__.__name__ + " : Unknown response \n" + str(msg)+"\n" )
            return ''
        return msg

    def _heart_beat(self):
        while not self._stop:
            if self._connected :
                self.ws.send(json.dumps({'op': 'ping'}))
            time.sleep(15)

    def _on_connect(self):
        self.connected_channel={}
        if self._param.get('execution', True) : self._subscribe({"op": "subscribe", "args": [f"trade.{self._symbol}"]},f"trade.{self._symbol}", self._on_executions)
        if self._param.get('board', False) :    self._subscribe({"op": "subscribe", "args": [f"orderBook_200.100ms.{self._symbol}"]},f"orderBook_200.100ms.{self._symbol}", self._on_board)
        if self._param.get('ticker', False) :   self._subscribe({"op": "subscribe", "args": [f"instrument_info.100ms.{self._symbol}"]},f"instrument_info.100ms.{self._symbol}", self._on_ticker)

        if self._auth!=None :
            self._auth.start_auth(self._auth_start)

    def _auth_start(self):
        timestamp = int((time.time() + 10.0) * 1000)
        sign = self._auth.generate_sign(self._auth.secret, 'GET/realtime' + str(timestamp))
        params = {"op": "auth", "args": [self._auth.apikey, timestamp, sign]}
        self.ws.send(json.dumps(params))

    def _on_executions(self,msg):
        recept_data = msg.get('data')
        self.execution.time = self._epoc_to_dt(recept_data[-1]['trade_time_ms']/1000)
        self._append_latency(self._jst_now_dt().timestamp()*1000 - recept_data[-1]['trade_time_ms'])
        for i in recept_data:
            self._append_execution(i['price'],i['size'],i['side'].upper(),self._epoc_to_dt(i['trade_time_ms']/1000),i['trade_id'])
        self.my.position.ref_ltp = self.execution.last
        self.execution.call_handlers.set()

    def _on_board(self,msg):
        self.board.time = self._epoc_to_dt(int(msg['timestamp_e6'])/1000000)
        recept_data = msg.get('data')
        msg_type=msg.get('type')
        board_list = []
        if msg_type=='snapshot' :
            self.board._initialize_dict()
            board_list = self.board._insert(recept_data,-1)
        elif msg_type=='delta' :
            board_list.extend(self.board._delete(recept_data.get('delete',[]),-1))
            board_list.extend(self.board._change(recept_data.get('update',[]),-1))
            board_list.extend(self.board._insert(recept_data.get('insert',[]),-1))
        for i in board_list:
            self._append_board(self.board.time, i['price'],i['size'],i['side'])
        self.board.call_handlers.set()

    def _on_ticker(self,msg):
        self.ticker.time = self._epoc_to_dt(int(msg['timestamp_e6'])/1000000)
        recept_data = msg.get('data',{'update':{}})
        data = recept_data.get('update',[])
        for d in data:
            self.ticker.last = float(d.get('last_price_e4',self.ticker.last*10000)/10000)
            self.ticker.open_interest = d.get('open_interest',self.ticker.open_interest)


    # https://bybit-exchange.github.io/docs/inverse/#t-introduction
    def _on_my_position(self,message):
        """
       {'topic': 'position', 'data': [{'user_id': 1473148, 'symbol': 'BTCUSD', 'size': 69652, 'side': 'Buy', 'position_value': '1.47289031', 'entry_price': '47289.33317987', 'liq_price': '37567', 'bust_price': '37418.5', 'leverage': '100', 'order_margin': '0.06713431', 'position_margin': '0.3885523', 'available_balance': '0.34747987', 'take_profit': '0', 'stop_loss': '0', 'realised_pnl': '0.00026876', 'trailing_stop': '0', 'trailing_active': '0', 'wallet_balance': '0.45708269', 'risk_id': 1, 'occ_closing_fee': '0.00139608', 'occ_funding_fee': '0', 'auto_add_margin': 1, 'cum_realised_pnl': '0.38129056', 'position_status': 'Normal', 'position_seq': 4357475864, 'Isolated': False, 'mode': 0, 'position_idx': 0}]}
        """
        with self.my.lock :
            for d in message.get('data',[]) :
                self._logger.debug( self.__class__.__name__ + " : Position : " + str(d) )

    def _on_my_execution(self,message):
        """
       {'topic': 'execution', 'data': [{'symbol': 'BTCUSD', 'side': 'Sell', 'order_id': 'd0048c25-303a-4454-8745-ac77d92a2c4d', 'exec_id': '75ca2a7c-7ca1-5aed-a3d3-d6538cb1b0f1', 'order_link_id': '', 'price': '46500', 'order_qty': 1, 'exec_type': 'Trade', 'exec_qty': 1, 'exec_fee': '0.00000002', 'leaves_qty': 0, 'is_maker': False, 'trade_time': '2021-02-26T06:51:54.030Z'}]}
        """
        with self.my.lock :
            for d in message.get('data',[]) :
                self._logger.debug( self.__class__.__name__ + " : EXECUTION : " + str(d) )
                if self.my.order.execution( id=d['order_id'], side=d['side'].upper(), price=float(d['price']), size=d['exec_qty'] ) :
                    self.my.position.execution( id=d['order_id'], side=d['side'].upper(), price=float(d['price']), size=d['exec_qty'] )

    def _on_my_order(self,message):
        """
        {'topic': 'order', 'data': [{'order_id': '7b9055dc-5cde-425f-8bf9-13b9021d0c24', 'order_link_id': '', 'symbol': 'BTCUSD', 'side': 'Sell', 'order_type': 'Limit', 'price': '54000', 'qty': 1, 'time_in_force': 'PostOnly', 'create_type': 'CreateByUser', 'cancel_type': '', 'order_status': 'New', 'leaves_qty': 1, 'cum_exec_qty': 0, 'cum_exec_value': '0', 'cum_exec_fee': '0', 'timestamp': '2021-02-26T06:31:50.785Z', 'take_profit': '0', 'stop_loss': '0', 'trailing_stop': '0', 'last_exec_price': '0', 'reduce_only': False, 'close_on_trigger': False}]}
        {'topic': 'order', 'data': [{'order_id': '7b9055dc-5cde-425f-8bf9-13b9021d0c24', 'order_link_id': '', 'symbol': 'BTCUSD', 'side': 'Sell', 'order_type': 'Limit', 'price': '46411.5', 'qty': 1, 'time_in_force': 'PostOnly', 'create_type': 'CreateByUser', 'cancel_type': '', 'order_status': 'New', 'leaves_qty': 1, 'cum_exec_qty': 0, 'cum_exec_value': '0', 'cum_exec_fee': '0', 'timestamp': '2021-02-26T06:32:30.368Z', 'take_profit': '0', 'stop_loss': '0', 'trailing_stop': '0', 'last_exec_price': '0', 'reduce_only': False, 'close_on_trigger': False}]} 
       """
        with self.my.lock :
            for d in message.get('data',[]) :
                id = d.get('order_id')
                if d['order_status']=='New' :
                    if self.my.order.update_order(id, side=d['side'].upper(), price=float(d['price']), size=d['qty']) :
                        self._logger.debug( self.__class__.__name__ + " : [order] New Order : " + str(d) )
                elif d['order_status']=='Cancelled' :
                    self._logger.debug( self.__class__.__name__ + " : [order] Canceled : " + str(d) )
                    if self.my.order.remove_order( id ) :
                        self.my.position.execution( id, commission=-float(d['cum_exec_fee']) )  # ここまでに得たコミッションを適用
                elif d['order_status']=='Filled' :
                    if self.my.order.is_myorder( id ) :
                        self._logger.debug( self.__class__.__name__ + " : [order] Filled : " + str(d) )
                        self.my.position.execution( id, commission=-float(d['cum_exec_fee']) )
                elif d['order_status']=='PartiallyFilled' :
                    if self.my.order.is_myorder( id ) :
                        self._logger.debug( self.__class__.__name__ + " : [order] PartiallyFilled : " + str(d) )
                else:
                    self._logger.debug( self.__class__.__name__ + " : [order] Unknown : " + str(d) )
