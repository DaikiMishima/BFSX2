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

# https://bybit-exchange.github.io/docs/inverse/#t-introduction

class BybitAPI(RestAPIExchange):

    def __init__(self, logger, symbol='BTCUSD', testnet=False, auth=None, position=None, timeout=None):
        if testnet :
            self._api_url = "https://api-testnet.bybit.com"
        else:
            self._api_url = "https://api.bybit.com"
        self._symbol = symbol

        self._session = self._new_session()
        self._session.headers.update({'Content-Type': 'application/json'})

        # API Limit
        self.api_remain1 = 120

        RestAPIExchange.__init__(self,logger, symbol, auth, position, timeout)

        # APIアクセスしないときにも一定期間たったらAPI制限を解除するためのスレッド
        Scheduler(self._logger, interval=1, callback=self._limit_check)

    _minimum_order_size_dict = {'BTCUSD':1, 'ETHUSD':1, 'EOSUSD':1, 'XRPUSD':1,
                                'BTCUSDT':0.001 } # 最小取引単位は？（未調査）
    def minimum_order_size(self, symbol=None):
        return self._minimum_order_size_dict.get(symbol or self._symbol)

    def _new_session(self):
        return requests.Session()

    def _request(self, endpoint, method="GET", params={}, private=False):
        try:
            if private and self._auth!=None:
                params['api_key'] = self._auth.apikey
                params['timestamp'] = int(time.time() * 1000)
                params = dict(sorted(params.items()))
                param_str = ''
                for k,v in params.items():
                    if isinstance(params[k], bool):
                        if params[k]:
                            param_str += f'&{k}=true'
                        else :
                            param_str += f'&{k}=false'
                    else:
                        param_str += f'&{k}={v}'
                access_sign = self._auth.generate_sign(self._auth.secret, param_str[1:])
                params['sign'] = access_sign

            if method == "POST":
                response = self._session.post(self._api_url + endpoint, data=json.dumps(params), timeout=self._timeout)
            else:
                response = self._session.get(self._api_url + endpoint, params=params, timeout=self._timeout)
        except Exception as e:
            self._logger.error("Error occured at _request: {}".format(e))
            self._logger.info(traceback.format_exc())
            raise e

        res = response.json()
        self.api_remain1 = res.get('rate_limit_status',self.api_remain1)
        return res

    def _limit_check(self):
        # API制限
        if self.api_remain1<100 :
            self.api_remain1 += 1






    def ticker(self, **kwrgs):
        try:
            return self._request("/v2/public/tickers", "GET", params={'symbol': kwrgs.get('symbol', self.symbol)})
        except Exception as e:
            return {'stat': -999, 'msg': str(e)}


    # 残高 (BTC)
    def getbalance(self, coin='BTC', ):
        try:
            return self._request("/v2/private/wallet/balance", "GET", params={'coin': coin,}, private=True)
        except Exception as e:
            return {'stat': -999, 'msg': str(e)}

    def getpositions(self, **kwrgs):
        try:
            res = self._request("/v2/private/position/list", params={'symbol':kwrgs.get('symbol', self.symbol)}, private=True)
        except Exception as e:
            return []

        if res['ret_code']==0 :
            return [res.get("result")]
        else:
            return []



    # 証拠金残高 (BTC)
    def getcollateral(self, coin='BTC', ):
        try:
            res = self.getbalance()
            if res.get('ret_code',-1)!=0 :
                return {'stat': res.get('ret_code',-1), 'msg': res}
            return {'stat': 0, 'collateral': res['result'][coin]['equity'], 'msg': res}
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
            if k in ['symbol','time_in_force','reduce_only']:
                params[k]=v

        params['symbol']=params.get('symbol', self.symbol)
        params['time_in_force']=params.get('time_in_force', "GoodTillCancel")
        params['order_type']=order_type.capitalize()
        params['side']=side.capitalize()
        params['qty']=size
        params['price']=round(price*2)/2

        self._logger.debug("[sendorder] : {}".format(params) )
        with self._position.lock :
            try:
                res = self._request("/v2/private/order/create", 'POST', params=params, private=True )
            except Exception as e:
                return {'stat': -999, 'msg': str(e), 'ids':[]}
            ret_code = res.get('ret_code')

            if ret_code==0 : 
                if self._position and not adjust_flag:
                    r = res.get('result')
                    self._position.order.new_order( symbol=params['symbol'], id=r['order_id'] , side=r['side'].upper(), price=r['price'], size=r['qty'], expire=time.time()+auto_cancel_after, invalidate=time.time()+2592000 )
                return {'stat':0 , 'msg':"", 'ids':[r['order_id']]}

            # 証拠金不足
            # {'ret_code': 30031, 'ret_msg': 'oc_diff[61255], new_oc[61255] with ob[0]+AB[2194]', 'ext_code': '', 'ext_info': '', 'result': None, 'time_now': '1615409661.288081', 'rate_limit_status': 99, 'rate_limit_reset_ms': 1615409661286, 'rate_limit': 100}
            elif ret_code==30031 : 
                self.PendingUntil = time.time()+60  # 60秒注文保留
            else: 
                self._logger.error("Send order param : {}".format(params) )
                self._logger.error("Error response [sendorder] : {}".format(res) )
                return {'stat':ret_code , 'msg':res.get('ret_msg'), 'ids':[]}

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

        args['order_id']=id
        args['symbol']=args.get("symbol", self._position.order.order_dict[id]['symbol'] )

        self._logger.debug("[cancelorder] : {}".format(args) )

        self._position.order.mark_as_invalidate( id )

        try:
            res = self._request("/v2/private/order/cancel", 'POST', params=args, private=True )
        except Exception as e:
            return {'stat': -999, 'msg': str(e)}
        ret_code = res.get('ret_code',-999)

        if ret_code==0 : 
            return {'stat': 0, 'msg': ""}

        if ret_code==20001 : # 'ret_msg': 'order not exists or too late to cancel'
            self._position.order.remove_order( id )

        self._logger.error("Error response [cancelorder] : {}".format(res) )
        return {'stat':ret_code , 'msg':res.get('ret_msg')}
