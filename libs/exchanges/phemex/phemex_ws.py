# coding: utf-8
#!/usr/bin/python3

import time
import json
from threading import Thread

#-------------参考
# https://github.com/phemex/phemex-api-docs/

from libs.exchanges.base_module.base_exchange import WebsocketExchange
from libs.exchanges.base_module.position.myposition import MyPosition
from libs.exchanges.base_module.position.position_ave import OpenPositionKeepAve

class PhemexWebsocket(WebsocketExchange):

    _currency = {"BTCUSD": ".BTC",
                 "XRPUSD": ".XRP",
                 "ETHUSD": ".ETH",
                 "LINKUSD": ".LINK",
                 "XTZUSD": ".XTZ",
                 "LTCUSD": ".LTC",
                 "GOLDUSD": ".GOLD",
                 "ADAUSD": ".ADA",
                 "BCHUSD": ".BCH",
                 "COMPUSD": ".COMP",
                 "ALGOUSD": ".ALGO",
                 "YFIUSD": ".YFI",
                 "DOTUSD": ".DOT",
                 "UNIUSD": ".UNI"
                }
    def __init__(self, logger, subscribe={}, symbol='BTCUSD', testnet=False, auth=None):
        if testnet :
            self._endpoint = "wss://testnet.phemex.com/ws"
        else:
            self._endpoint = "wss://phemex.com/ws"
        self._channel_str = "event"
        self._param = subscribe
        self._symbol = symbol
        self._auth = auth
        self.connected_channel={}
        WebsocketExchange.__init__(self,logger)
        self.my = MyPosition(logger, OpenPositionKeepAve, order_unit='USD')

        self._heart_beat_th = Thread(target=self._heart_beat)
        self._heart_beat_th.daemon = True
        self._heart_beat_th.start()

    def units(self,value=0):
        return {'unitrate' :self.execution.last,        # 損益額をプロフィットグラフに表示する単位に変換する係数
                'title':"USD {:+,.2f}".format(value)}   # 表示フォーマット

    def _heart_beat(self):
        while not self._stop:
            if self._connected :
                self.ws.send(json.dumps({"id": 1, "method": "server.ping", "params": []}))
            time.sleep(20)

    def is_connected(self):
        return (self._auth.auth_completed and
                self.connected_channel.get(100,False)) if self._auth!=None else self._connected

    def _message_dump(self, message):
        msg = json.loads(message)
#        print(json.dumps(msg, indent=2))
        id = msg.get('id')
        if not id:
            if 'trades' in msg :
                msg[self._channel_str] = 'trades'
            elif 'book' in msg :
                msg[self._channel_str] = 'book'
            elif 'tick' in msg :
                msg[self._channel_str] = 'tick'
            elif 'accounts' in msg :
                msg[self._channel_str] = 'accounts'
            elif 'position_info' in msg :
                return ''
            else:
                self._logger.error( self.__class__.__name__ + " : Unknown response \n" + str(msg)+"\n" )
            return msg

        result = msg.get("result",{})
        if type(result)==dict and result.get("status")=="success" :

            if id == 10:
                self._auth.auth_complete()
                self._subscribe({"id": 100, "method": "aop.subscribe","params": []}, "accounts", self._on_my_order)

            self.connected_channel[id]=True
            return ''
        elif id !=1 :
            self._logger.error( self.__class__.__name__ + " : Unknown response \n" + str(msg)+"\n" )

        return msg

    def _on_connect(self):
        if self._param.get('execution', True) : self._subscribe({"id": 2, "method": "trade.subscribe", "params": [self._symbol]}, "trades", self._on_executions)
        if self._param.get('board', False) :    self._subscribe({"id": 3, "method": "orderbook.subscribe", "params": [self._symbol]}, "book", self._on_board)
        if self._param.get('ticker', False) :   self._subscribe({"id": 4, "method": "tick.subscribe", "params": [self._currency[self._symbol]]}, "tick", self._on_ticker)

        if self._auth!=None :
            self._auth.start_auth(self._auth_start)

    def _auth_start(self):
        timestamp = int(time.time())+60
        sign = self._auth.generate_sign(self._auth.secret, self._auth.apikey + str(timestamp))
        params = {"method": "user.auth", "params": ["API", self._auth.apikey, sign, timestamp], "id": 10}
        self.ws.send(json.dumps(params))

    def _on_executions(self,msg):
        if msg['type']=='snapshot' :
            trades = msg['trades'][-1:] # 初回のsnapshot時には多いので最後だけを読み込み
        else:
            trades = msg['trades']
        self.execution.time = self._epoc_to_dt(int(trades[0][0])/1000000000)
        for t in trades:
            self._append_execution(float(t[2])/10000,float(t[3]),"BUY" if t[1]=="Buy" else "SELL", self._epoc_to_dt(int(t[0])/1000000000))
        self._append_latency(self._jst_now_dt().timestamp()*1000 - int(trades[0][0])/1000000)
        self.my.position.ref_ltp = self.execution.last
        self.execution.call_handlers.set()

    def _on_board(self,msg):
        book = msg['book']
        self.board.time = self._epoc_to_dt(int(msg['timestamp'])/1000000000)
        msg_type=msg.get('type')    
        if msg_type=='snapshot' :
            self.board._initialize_dict()
        asks = self.board._update_asks([(p/10000,s) for p,s in book.get('asks',[])])
        bids = self.board._update_bids([(p/10000,s) for p,s in book.get('bids',[])])
        if asks:
            for i in asks:
                self._append_board(self.board.time, i['price'],i['size'],i['side'])
        if bids:
            for i in bids:
                self._append_board(self.board.time, i['price'], i['size'], i['side'])
        self.board.call_handlers.set()

    def _on_ticker(self,msg):
        tick = msg['tick']
        self.ticker.time = self._epoc_to_dt(int(tick['timestamp'])/1000000000)
        self.ticker.last = float(tick.get('last',0))

    def _on_my_order(self,message):
        '''
        {'accountID': 1111111111, 'action': 'New', 'actionBy': 'ByUser', 'actionTimeNs': 1615290931272863133, 'addedSeq': 5863708589, 'bonusChangedAmountEv': 0, 'clOrdID': 'BFSX2-1615290930', 'closedPnlEv': 0, 'closedSize': 0, 'code': 0, 'cumQty': 0, 'cumValueEv': 0, 'curAccBalanceEv': 88345, 'curAssignedPosBalanceEv': 0, 'curBonusBalanceEv': 75330, 'curLeverageEr': 0, 'curPosSide': 'None', 'curPosSize': 0, 'curPosTerm': 8, 'curPosValueEv': 0, 'curRiskLimitEv': 10000000000, 'currency': 'BTC', 'cxlRejReason': 0, 'displayQty': 0, 'execFeeEv': 0, 'execID': '00000000-0000-0000-0000-000000000000', 'execPriceEp': 0, 'execQty': 0, 'execSeq': 5863708589, 'execStatus': 'New', 'execValueEv': 0, 'feeRateEr': 0, 'leavesQty': 1, 'leavesValueEv': 1923, 'message': 'No error', 'nthItem': 1, 'ordStatus': 'New', 'ordType': 'Limit', 'orderID': '2ceb1d43-4ca5-4083-9c5e-ccb17a84226e', 'orderQty': 1, 'pegOffsetValueEp': 0, 'platform': 'API', 'priceEp': 520000000, 'relatedPosTerm': 8, 'relatedReqNum': 81, 'side': 'Buy', 'slTrigger': 'ByMarkPrice', 'stopLossEp': 0, 'stopPxEp': 0, 'symbol': 'BTCUSD', 'takeProfitEp': 0, 'timeInForce': 'GoodTillCancel', 'totalItems': 1, 'tpTrigger': 'ByLastPrice', 'transactTimeNs': 1615290931275994937, 'userID': 778748, 'vsAccountID': 0, 'vsUserID': 0}
        {'accountID': 1111111111, 'action': 'New', 'actionBy': 'ByUser', 'actionTimeNs': 1615378305577855512, 'addedSeq': 5890866606, 'bonusChangedAmountEv': 0, 'clOrdID': 'BFSX2-1615378305', 'closedPnlEv': 11, 'closedSize': 3, 'code': 0, 'cumQty': 3, 'cumValueEv': 5431, 'curAccBalanceEv': 88099, 'curAssignedPosBalanceEv': 781, 'curBonusBalanceEv': 73805, 'curLeverageEr': 0, 'curPosSide': 'Buy', 'curPosSize': 37, 'curPosTerm': 108, 'curPosValueEv': 67129, 'curRiskLimitEv': 10000000000, 'currency': 'BTC', 'cxlRejReason': 0, 'displayQty': 0, 'execFeeEv': -1, 'execID': 'adcf6d13-9c73-54a7-a51c-af8278b75db0', 'execPriceEp': 552310000, 'execQty': 3, 'execSeq': 5891046209, 'execStatus': 'MakerFill', 'execValueEv': 5431, 'feeRateEr': -25000, 'lastLiquidityInd': 'AddedLiquidity', 'leavesQty': 67, 'leavesValueEv': 121308, 'message': 'No error', 'nthItem': 2, 'ordStatus': 'PartiallyFilled', 'ordType': 'Limit', 'orderID': '35b6bbca-2fa9-4757-a1cc-c9a33e5d10a2', 'orderQty': 70, 'pegOffsetValueEp': 0, 'platform': 'API', 'priceEp': 552310000, 'relatedPosTerm': 108, 'relatedReqNum': 1402, 'side': 'Sell', 'slTrigger': 'ByMarkPrice', 'stopLossEp': 0, 'stopPxEp': 0, 'symbol': 'BTCUSD', 'takeProfitEp': 0, 'timeInForce': 'GoodTillCancel', 'totalItems': 3, 'tpTrigger': 'ByLastPrice', 'tradeType': 'Trade', 'transactTimeNs': 1615378830054782485, 'userID': 778748, 'vsAccountID': 8293920001, 'vsUserID': 829392}
        {'accountID': 1111111111, 'action': 'Cancel', 'actionBy': 'ByUser', 'actionTimeNs': 1615290941440697507, 'addedSeq': 5863708589, 'bonusChangedAmountEv': 0, 'clOrdID': 'BFSX2-1615290930', 'closedPnlEv': 0, 'closedSize': 0, 'code': 0, 'cumQty': 0, 'cumValueEv': 0, 'curAccBalanceEv': 88345, 'curAssignedPosBalanceEv': 0, 'curBonusBalanceEv': 75330, 'curLeverageEr': 0, 'curPosSide': 'None', 'curPosSize': 0, 'curPosTerm': 8, 'curPosValueEv': 0, 'curRiskLimitEv': 10000000000, 'currency': 'BTC', 'cxlRejReason': 0, 'displayQty': 0, 'execFeeEv': 0, 'execID': '00000000-0000-0000-0000-000000000000', 'execPriceEp': 0, 'execQty': 1, 'execSeq': 5863711780, 'execStatus': 'Canceled', 'execValueEv': 0, 'feeRateEr': 0, 'leavesQty': 0, 'leavesValueEv': 0, 'message': 'No error', 'nthItem': 1, 'ordStatus': 'Canceled', 'ordType': 'Limit', 'orderID': '2ceb1d43-4ca5-4083-9c5e-ccb17a84226e', 'orderQty': 1, 'pegOffsetValueEp': 0, 'platform': 'API', 'priceEp': 520000000, 'relatedPosTerm': 8, 'relatedReqNum': 82, 'side': 'Buy', 'slTrigger': 'ByMarkPrice', 'stopLossEp': 0, 'stopPxEp': 0, 'symbol': 'BTCUSD', 'takeProfitEp': 0, 'timeInForce': 'GoodTillCancel', 'totalItems': 1, 'tpTrigger': 'ByLastPrice', 'transactTimeNs': 1615290941445892128, 'userID': 778748, 'vsAccountID': 0, 'vsUserID': 0}
        '''
        if message.get('type')=='snapshot' : return
        with self.my.lock :
            for d in message.get('orders',[]) :
                id = d.get('orderID')
                if d['ordStatus']=='New' :
                    if self.my.order.update_order(id, side=d['side'].upper(), price=float(d['priceEp'])/10000, size=d['orderQty']) :
                        self._logger.debug( self.__class__.__name__ + " : [order] New Order : " + str(d) )
                        continue
                    else:
                        self._logger.debug( self.__class__.__name__ + " : Not My order : " + str(id) )

                elif d['ordStatus']=='Canceled' :
                    if self.my.order.remove_order( id ) :
                        self._logger.debug( self.__class__.__name__ + " : [order] Canceled : " + str(d) )
                        continue
                    else:
                        self._logger.debug( self.__class__.__name__ + " : Not My order : " + str(id) )

                elif d['ordStatus']=='Filled' :
                    if self.my.order.execution( id=id, side=d['side'].upper(), price=d['execPriceEp']/10000, size=d['execQty'] ) :
#                    if self.my.order.is_myorder( id ) :
                        self._logger.debug( self.__class__.__name__ + " : [order] Filled : " + str(d) )
                        self.my.position.execution( id, price=d['execPriceEp']/10000, side=d['side'].upper(), size=d['execQty'],
                                                    commission=round(-d['execQty']/d['execPriceEp']*d['feeRateEr']/10000-0.000000005,8) )
                        continue
                    else:
                        self._logger.debug( self.__class__.__name__ + " : Not My order : " + str(id) )

                elif d['ordStatus']=='PartiallyFilled' :
                    if self.my.order.execution( id=id, side=d['side'].upper(), price=d['execPriceEp']/10000, size=d['execQty'] ) :
#                    if self.my.order.is_myorder( id ) :
                        self._logger.debug( self.__class__.__name__ + " : [order] PartiallyFilled : " + str(d) )
                        self.my.position.execution( id, price=d['execPriceEp']/10000, side=d['side'].upper(), size=d['execQty']
                                                  , commission=round(-d['execQty']/d['execPriceEp']*d['feeRateEr']/10000-0.000000005,8) )
                        continue
                    else:
                        self._logger.info( self.__class__.__name__ + " : Not My order : " + str(id) )

                self._logger.debug( self.__class__.__name__ + " : [order] Unknown : " + str(d) )

