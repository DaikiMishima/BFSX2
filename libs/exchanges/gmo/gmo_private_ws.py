# coding: utf-8
#!/usr/bin/python3

#-------------参考
# https://api.coin.z.com/docs/#private-ws-api

from datetime import datetime
import json
import requests
import time
from libs.utils.scheduler import Scheduler
from libs.exchanges.base_module.base_exchange import WebsocketExchange
from libs.exchanges.base_module.position.myposition import MyPosition
from libs.exchanges.base_module.position.position_gross import OpenPositionGross

class GmoWebsocketPrivate(WebsocketExchange):

    def __init__(self, logger, auth, disconnect_event):
        self._logger = logger
        self._auth = auth
        self._disconnect_event = disconnect_event
        self.my = MyPosition(logger, OpenPositionGross)
        self._endpoint_rest = 'https://api.coin.z.com/private/v1'
        while True:
            self._token = self._get_access_token()
            if self._token :
                break
            time.sleep(1)
        Scheduler(self._logger, interval=3000, callback=self._extend_access_token)
        self._endpoint = "wss://api.coin.z.com/ws/private/v1/" + self._token
        self._channel_str = "channel"
        WebsocketExchange.__init__(self,logger)

    def re_connect(self):
        while True:
            self._token = self._get_access_token()
            if self._token :
                break
            time.sleep(1)
        self._endpoint = "wss://api.coin.z.com/ws/private/v1/" + self._token
        self._connected = False
        self._stop = False
        self.running = False
        self._start()

    def _on_connect(self):
        self._subscribe({"command": "subscribe", "channel": "executionEvents"},"executionEvents", self._on_my_execution)
        time.sleep(2)
        self._subscribe({"command": "subscribe", "channel": "orderEvents"},"orderEvents", self._on_my_order)
        time.sleep(2)
        self._subscribe({"command": "subscribe", "channel": "positionEvents"},"positionEvents", self._on_my_position)
        time.sleep(2)
        self._auth.auth_complete()

    def is_connected(self):
        return self._auth.auth_completed

    def _on_disconnect(self):
        self.stop()
        self._disconnect_event.set()

    def _get_access_token(self):
        timestamp = '{0}000'.format(int(time.mktime(datetime.now().timetuple())))
        text = timestamp +'POST/v1/ws-auth{}'
        sign = self._auth.generate_sign(self._auth.secret, text)
        headers = {'API-KEY': self._auth.apikey, 'API-TIMESTAMP': timestamp, 'API-SIGN': sign}
        res = requests.post(self._endpoint_rest + '/ws-auth', headers=headers, data=json.dumps({})).json()
        try:
            if res['status']==0 :
                self._logger.info( "Success to generate accesss token : {}".format(res) )
                return res['data']
        except:
            pass
        self._logger.error( "Generate accesss token error : response {}".format(res) )

    def _extend_access_token(self):
        timestamp = '{0}000'.format(int(time.mktime(datetime.now().timetuple())))
        text = timestamp +'PUT/v1/ws-auth'
        sign = self._auth.generate_sign(self._auth.secret, text)
        headers = {'API-KEY': self._auth.apikey, 'API-TIMESTAMP': timestamp, 'API-SIGN': sign}
        res = requests.put(self._endpoint_rest + '/ws-auth', headers=headers, data=json.dumps({'token': self._token})).json()
        try:
            if res['status']==0 :
                self._logger.debug( "Success to extend accesss token" )
                return
        except:
            pass
        self._logger.error( "Extend accesss token error : response {}".format(res) )

        # アクセストークンが更新できなかった時には、最初から接続しなおし
        self._on_disconnect()

    def _on_my_position(self,d):
        """
        {'channel': 'positionEvents', 'leverage': '4', 'lossGain': '0', 'losscutPrice': '5972680', 'msgType': 'OPR', 'orderdSize': '0', 'positionId': 86266891, 'price': '5309049', 'side': 'SELL', 'size': '0.01', 'symbol': 'BTC_JPY', 'timestamp': '2021-03-06T07:26:35.030Z'}
        """
        self._logger.debug( self.__class__.__name__ + " : Position : " + str(d) )

    def _on_my_execution(self,d):

        """
        {'channel': 'executionEvents', 'executionId': 278209163, 'executionPrice': '5292138', 'executionSize': '0.01', 'executionTimestamp': '2021-03-06T07:10:32.004Z', 'executionType': 'LIMIT', 'fee': '0', 'lossGain': '0', 'msgType': 'ER', 'orderExecutedSize': '0.01', 'orderId': 1201641525, 'orderPrice': '5292138', 'orderSize': '0.01', 'orderTimestamp': '2021-03-06T07:10:10.795Z', 'positionId': 86266824, 'settleType': 'OPEN', 'side': 'SELL', 'symbol': 'BTC_JPY', 'timeInForce': 'FAS'}

        {'channel': 'executionEvents', 'executionId': 278233470, 'executionPrice': '5309049', 'executionSize': '0.01', 'executionTimestamp': '2021-03-06T07:26:35.030Z', 'executionType': 'LIMIT', 'fee': '0', 'lossGain': '0', 'msgType': 'ER', 'orderExecutedSize': '0.01', 'orderId': 1201663589, 'orderPrice': '5309049', 'orderSize': '0.01', 'orderTimestamp': '2021-03-06T07:25:21.866Z', 'positionId': 86266891, 'settleType': 'OPEN', 'side': 'SELL', 'symbol': 'BTC_JPY', 'timeInForce': 'FAS'}
        """
        self._logger.debug( self.__class__.__name__ + " : EXECUTION : " + str(d) )
        with self.my.lock :
            order_info = self.my.order.execution( id=str(d['orderId']), side=d['side'], price=float(d['executionPrice']), size=float(d['executionSize']) )
            if order_info or self.my.position.is_myorder(id=str(d['positionId'])) :

                closeid = order_info.get('closeid')
                if d['settleType']=='CLOSE' and closeid :
                    if d['side']=='BUY' :
                        self.my.position._short_position[closeid]['closeorder'] = False
                        self._logger.debug("Flag Off exec : {}".format(self.my.position._short_position[closeid]) )
                    else:
                        self.my.position._long_position[closeid]['closeorder'] = False
                        self._logger.debug("Flag Off exec : {}".format(self.my.position._long_position[closeid]) )

                self.my.position.execution( posid=str(d['positionId']), side=d['side'], price=float(d['executionPrice']), size=float(d['executionSize']), orderid=d['orderId'] , commission=-float(d['fee']), settleType=d['settleType'])

                # GMOポジションのデバッグ用
                self._logger.debug( 'order dict: {}'.format(self.my.order.order_dict) )
                self._logger.debug( 'long_pos: {}'.format(self.my.position._long_position) )
                self._logger.debug( 'short_pos: {}'.format(self.my.position._short_position) )
                self._logger.debug( 'size, ave, unreal: {}'.format(self.my.position._calc_position) )
                self._logger.debug( 'profit: {}'.format(self.my.position.realized) )

    def _on_my_order(self,d):
        """
        new_order
        {'channel': 'orderEvents', 'executionType': 'LIMIT', 'losscutPrice': '0', 'msgType': 'NOR', 'orderExecutedSize': '0', 'orderId': 1201501249, 'orderPrice': '5300000', 'orderSize': '0.01', 'orderStatus': 'ORDERED', 'orderTimestamp': '2021-03-06T05:29:53.188Z', 'settleType': 'OPEN', 'side': 'SELL', 'symbol': 'BTC_JPY', 'timeInForce': 'FAS'}

        change
        {'channel': 'orderEvents', 'executionType': 'LIMIT', 'losscutPrice': '0', 'msgType': 'ROR', 'orderExecutedSize': '0', 'orderId': 1201501249, 'orderPrice': '5299900', 'orderSize': '0.01', 'orderStatus': 'ORDERED', 'orderTimestamp': '2021-03-06T05:29:53.188Z', 'settleType': 'OPEN', 'side': 'SELL', 'symbol': 'BTC_JPY', 'timeInForce': 'FAS'}

        cancel
        {'cancelType': 'USER', 'channel': 'orderEvents', 'executionType': 'LIMIT', 'losscutPrice': '0', 'msgType': 'COR', 'orderExecutedSize': '0', 'orderId': 1201501249, 'orderPrice': '5299900', 'orderSize': '0.01', 'orderStatus': 'CANCELED', 'orderTimestamp': '2021-03-06T05:29:53.188Z', 'settleType': 'OPEN', 'side': 'SELL', 'symbol': 'BTC_JPY', 'timeInForce': 'FAS'}
        {'cancelType': 'USER', 'channel': 'orderEvents', 'executionType': 'LIMIT', 'losscutPrice': '0', 'msgType': 'COR', 'orderExecutedSize': '0', 'orderId': 1201683420, 'orderPrice': '5253214', 'orderSize': '0.02', 'orderStatus': 'CANCELED', 'orderTimestamp': '2021-03-06T07:37:10.764Z', 'settleType': 'OPEN', 'side': 'BUY', 'symbol': 'BTC_JPY', 'timeInForce': 'FAS'}
        """
        with self.my.lock :
            if d['orderStatus']=='ORDERED' :
                if self.my.order.update_order( id=str(d['orderId']), side=d['side'], price=float(d['orderPrice']), size=float(d['orderSize']) ) :
                    self._logger.debug( self.__class__.__name__ + " : [order] New Order : " + str(d) )
                    self._logger.debug( 'order dict: {}'.format(self.my.order.order_dict) )
                    self._logger.debug( 'long_pos: {}'.format(self.my.position._long_position) )
                    self._logger.debug( 'short_pos: {}'.format(self.my.position._short_position) )
                    self._logger.debug( 'size, ave, unreal: {}'.format(self.my.position._calc_position) )
                    self._logger.debug( 'profit: {}'.format(self.my.position.realized) )
            elif d['orderStatus']=='CANCELED' :
                order_info = self.my.order.remove_order( id=str(d['orderId']) )
                if order_info :
                    self._logger.debug( self.__class__.__name__ + " : [order] Canceled : " + str(d) )
                    self._logger.debug( 'order dict: {}'.format(order_info) )
                    self._logger.debug( 'long_pos: {}'.format(self.my.position._long_position) )
                    self._logger.debug( 'short_pos: {}'.format(self.my.position._short_position) )
                    self._logger.debug( 'size, ave, unreal: {}'.format(self.my.position._calc_position) )
                    self._logger.debug( 'profit: {}'.format(self.my.position.realized) )

                    # 決済オーダーがキャンセルされたら 当該のポジション情報のCloseorder発注済みフラグを削除
                    closeid = order_info.get('closeid')
                    if closeid :
                        if order_info['side']=='BUY' :
                            self.my.position._short_position[closeid]['closeorder'] = False
                            self._logger.debug("Flag Off cancel : {}".format(self.my.position._short_position[closeid]) )
                        else:
                            self.my.position._long_position[closeid]['closeorder'] = False
                            self._logger.debug("Flag Off cancel : {}".format(self.my.position._long_position[closeid]) )

            else:
                self._logger.info( self.__class__.__name__ + " : Order : " + str(d) )
