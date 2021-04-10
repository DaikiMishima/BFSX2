# coding: utf-8
#!/usr/bin/python3

import json
import requests
from threading import Thread
import time
import traceback
import urllib
from libs.utils.scheduler import Scheduler
from libs.exchanges.base_module.base_rest import RestAPIExchange

# https://github.com/phemex/phemex-api-docs/blob/master/Public-Contract-API-en.md
# https://github.com/phemex/phemex-python-api/blob/master/phemex/client.py
# https://github.com/ccxt/ccxt/blob/master/python/ccxt/phemex.py

class PhemexAPI(RestAPIExchange):

    def __init__(self, logger, symbol, testnet=False, auth=None, position=None, timeout=None):
        if testnet :
            self._api_url = "https://testnet-api.phemex.com"
        else:
            self._api_url = "https://api.phemex.com"
        self._symbol = symbol

        self._session = self._new_session()
        self._session.headers.update({'Content-Type': 'application/json'})

        # API Limit
        self.api_remain1 = 500

        RestAPIExchange.__init__(self,logger, symbol, auth, position, timeout)

        # APIアクセスしないときにも一定期間たったらAPI制限を解除するためのスレッド
        Scheduler(self._logger, interval=1, callback=self._limit_check)

    _minimum_order_size_dict = {'BTCUSD':1, 'XRPUSD':1, 'ETHUSD':1, 'LINKUSD':1, 'XTZUSD':1,
                                'LTCUSD':1, 'GOLDUSD':1, 'ADAUSD':1, 'BCHUSD':1, 'COMPUSD':1,
                                'ALGOUSD':1, 'YFIUSD':1, 'DOTUSD':1, 'UNIUSD':1 }
    def minimum_order_size(self, symbol=None):
        return self._minimum_order_size_dict.get(symbol or self._symbol)

    def _new_session(self):
        return requests.Session()

    def _request(self, endpoint, method="GET", params={}, private=False):
        try:
            if private and self._auth!=None :
                timestamp = str(int(time.time()) + 60)
                if method == "POST":
                    body_str = json.dumps(params, separators=(',', ':'))
                    text =  endpoint + timestamp + body_str
                else:
                    query_string = '&'.join(['{}={}'.format(k,v) for k,v in params.items()])
                    text = endpoint + query_string + timestamp
                sign = self._auth.generate_sign(self._auth.secret, text)
                headers = {'x-phemex-request-signature': sign,
                           'x-phemex-request-expiry': timestamp,
                           'x-phemex-access-token': self._auth.apikey,
                           'Content-Type': 'application/json' }
            else:
                headers = {'Content-Type': 'application/json' }


            if method == "POST":
                response = self._session.post(self._api_url + endpoint, headers=headers, data=body_str.encode(), timeout=self._timeout)
            elif method == "DELETE":
                response = self._session.delete(self._api_url + endpoint, headers=headers, params=params, timeout=self._timeout)
            else:
                response = self._session.get(self._api_url + endpoint, headers=headers, params=params, timeout=self._timeout)

            self.api_remain1 = int(response.headers.get('X-RateLimit-Remaining-CONTRACT',self.api_remain1))
            if 'X-RateLimit-Retry-After-CONTRACT' in response.headers :
                self.PendingUntil = time.time()+response.header['X-RateLimit-Retry-After-CONTRACT']

        except Exception as e:
            self._logger.error("Error occured at _request: {}".format(e))
            self._logger.info(traceback.format_exc())
            raise e

        res = response.json()

        return res

    def _limit_check(self):
        # API制限
        if self.api_remain1<100 :
            self.api_remain1 += 1

    def ticker(self, **kwrgs):
        try:
            return self._request("/md/ticker/24hr", "GET", params={'symbol': kwrgs.get('symbol', self.symbol)})
        except Exception as e:
            return {'stat': -999, 'msg': str(e)}

    def getbalance(self ):
        try:
            return self._request("/phemex-user/users/children", "GET", params={}, private=True)
        except Exception as e:
            return {'stat': -999, 'msg': str(e)}

    def getpositions(self, **kwrgs):
        try:
            res = self._request("/accounts/positions", params={'currency': 'BTC'}, private=True)
        except Exception as e:
            return []

        if res['code']==0 :
            return res.get("data",{}).get("positions")
        else:
            return []


    # 証拠金口座の証拠金額 (BTC)
    def getcollateral(self):
        try:
            import pprint
            res= self.getbalance()
            if res.get('code',-1)!=0 :
                return {'stat': res.get('code',-1), 'msg': res}

            balance = 0
            for r in res['data'][0]['userMarginVo'] :
                try:
                    if r['currency']=='BTC' :   balance = float(r['accountBalance'])
                except:
                    pass
            return {'stat': 0, 'collateral': balance, 'msg': res}

        except Exception as e:
            return {'stat': -999, 'msg': traceback.format_exc()}

    def sendorder(self, order_type, side, size, price=0, auto_cancel_after=2592000, **args ):
        """
        sendorder( order_type='LIMIT',             # 指値注文の場合は "LIMIT", 成行注文の場合は "MARKET" を指定します。
                   side='BUY',                     # 買い注文の場合は "BUY", 売り注文の場合は "SELL" を指定します。
                   size=0.01,                      # 注文数量を指定します。
                   price=4800000,                  # 価格を指定します。order_type に "LIMIT" を指定した場合は必須です。
                   auto_cancel_after,              # 0 以外を指定すると指定秒数経過後キャンセルを発行します
                   symbol="BTCUSD"                 # 省略時には起動時に指定した symbol が選択されます
                   time_in_force="GoodTillCancel", # 執行数量条件 を "GoodTillCancel", "ImmediateOrCancel", "FillOrKill", "PostOnly"で指定します。
                   reduce_only,                    # True means your position can only reduce in size if this order is triggered
                  ) )

        return: { 'stat': エラーコード,            # オーダー成功時 0
                  'msg':  エラーメッセージ,
                  'ids' : オーダーIDのリスト,      # オーダー成功時 [id,]  オーダー失敗時 []
                }
        """

        pos_side = self._position.position.side
        if self.noTrade and (pos_side==side or pos_side=='NONE'):
            self._logger.info("No trade period" )
            return {'stat': -999, 'msg': "No trade period", 'ids': []}

        if self.api_remain1<10 :
            self._logger.info("LimitRemaining(api_remain1) : {}/120".format(self.api_remain1) )
            return {'stat': -999, 'msg': "LimitRemaining(api_remain1) "+str(self.api_remain1)+"/120", 'ids': []}

        if self.PendingUntil > time.time() :
            self._logger.info("Order pending : {:.1f}sec".format(self.PendingUntil-time.time()) )
            return {'stat': -999, 'msg': "Order pending : {:.1f}sec".format(self.PendingUntil-time.time()), 'ids': []}

        adjust_flag = args.get('adjust_flag', False)
        # 対応しているオプションだけにする
        params={}
        for k,v in args.items():
            if k=='timeInForce' :
                if v in ["GoodTillCancel", "ImmediateOrCancel", "FillOrKill", "PostOnly"] :
                    params[k]=v
            elif k=='triggerType' :
                if v in ["ByMarkPrice", "ByLastPrice"] :
                    params[k]=v
            elif k=='pegPriceType' :
                if v in ["TrailingStopPeg", "TrailingTakeProfitPeg"] :
                    params[k]=v
            elif k in ['symbol','clOrdID','stopPxEp','reduceOnly','closeOnTrigger','takeProfitEp','stopLossEp','pegOffsetValueEp']:
                params[k]=v

        params['clOrdID']=params.get('clOrdID', 'BFSX2-'+str(int(time.time()*100000)))
        params['symbol']=params.get('symbol', self.symbol)
        params['ordType']=order_type.capitalize()
        params['side']=side.capitalize()
        params['orderQty']=size
        params['priceEp']=price*10000

        self._logger.debug("[sendorder] : {}".format(params) )
        with self._position.lock :
            try:
                res = self._request("/orders", 'POST', params=params, private=True )
            except Exception as e:
                return {'stat': -999, 'msg': str(e), 'ids':[]}

            ret_code = res.get('code')

            if ret_code==0 : 
                r = res.get('data')
                if self._position and not adjust_flag:
                    self._position.order.new_order( symbol=r['symbol'], id=r['orderID'] , side=r['side'].upper(), price=r['priceEp']/10000, size=r['orderQty'], expire=time.time()+auto_cancel_after, invalidate=time.time()+2592000 )
                return {'stat':0 , 'msg':"", 'ids':[r['orderID']]}
            else: 
                self._logger.error("Send order param : {}".format(params) )
                self._logger.error("Error response [sendorder] : {}".format(res) )
                return {'stat':ret_code , 'msg':res.get('msg'), 'ids':[]}

    def cancelorder(self, id, **args ):
        """
        cancelorder( id                      # キャンセルする注文の ID です。
                   symbol="BTCUSD"           # 省略時には起動時に指定した symbol が選択されます
                  ) )

        return: { 'stat': エラーコード,      # キャンセル成功時 0
                  'msg':  エラーメッセージ,
                }
        """

        if id not in self._position.order.order_dict :
            self._logger.info("ID:{} is already filled or canceld or expired".format(id) )
            return {'stat':-999 , 'msg':"Order is already filled or canceld or expired"}

        if self.api_remain1<10 :
            self._logger.info("LimitRemaining(api_remain1) : {}/120".format(self.api_remain1) )
            return {'stat': -999, 'msg': "LimitRemaining(api_remain1) "+str(self.api_remain1)+"/120"}

        args['orderID']=id
        args['symbol']=args.get("symbol", self._position.order.order_dict[id]['symbol'] )

        self._logger.debug("[cancelorder] : {}".format(args) )

        self._position.order.mark_as_invalidate( id )

        try:
            res = self._request("/orders/cancel", 'DELETE', params=args, private=True )
        except Exception as e:
            return {'stat': -999, 'msg': str(e)}

        ret_code = res.get('code',-999)

        if ret_code==0 : 
            return {'stat': 0, 'msg': ""}

        # すでにオーダーがなくなっている？
        # {'code': 10002, 'msg': 'OM_ORDER_NOT_FOUND', 'data': None}
        if ret_code==10002 :
            self._position.order.remove_order( id=str(id) )

        self._logger.error("Error response [cancelorder] : {}".format(res) )
        return {'stat':ret_code , 'msg':res.get('msg')}
