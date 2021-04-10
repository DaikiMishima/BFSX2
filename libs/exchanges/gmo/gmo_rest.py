# coding: utf-8
#!/usr/bin/python3

from datetime import datetime
import json
import requests
import time
import traceback
import urllib
from libs.utils.scheduler import Scheduler
from libs.exchanges.base_module.base_rest import RestAPIExchange

# https://api.coin.z.com/docs/#private-api
# https://api.coin.z.com/docs/#references

class GmoAPI(RestAPIExchange):

    def __init__(self, logger, symbol='BTC_JPY', testnet=False, auth=None, position=None, timeout=None):
        self._publuc_api_url = "https://api.coin.z.com/public"
        self._private_api_url = "https://api.coin.z.com/private"
        self._symbol = symbol

        self._session = self._new_session()

        # API Limit
        self._last_access_time_post = time.time()
        self._last_access_time_get = time.time()

        RestAPIExchange.__init__(self,logger, symbol, auth, position, timeout)

    _minimum_order_size_dict = {'BTC_JPY':0.01, 'ETH_JPY':0.1, 'BCH_JPY':0.1, 'LTC_JPY':1, 'XRP_JPY':10,
                                'BTC':0.0001, 'ETH':0.01, 'BCH':0.01, 'LTC':0.1, 'XRP':1, }
    def minimum_order_size(self, symbol=None):
        return self._minimum_order_size_dict.get(symbol or self._symbol)

    def _new_session(self):
        return requests.Session()

    def _request(self, endpoint, method="GET", params=None, private=False):

        retry_counter = 5
        while retry_counter>0:

            # 前回のアクセスから0.5秒は次のアクセスを行わない
            last_access_time = self._last_access_time_get if method=="GET" else self._last_access_time_post
            wait = last_access_time+0.5-time.time()
            if wait>0:
                time.sleep(wait)

            api_url = self._private_api_url if private else self._publuc_api_url

            try:
                if private and self._auth!=None :
                    timestamp = '{0}000'.format(int(time.mktime(datetime.now().timetuple())))
                    if method == "POST":
                        text = timestamp + method + endpoint + json.dumps(params)
                    else:
                        text = timestamp + method + endpoint
                    sign = self._auth.generate_sign(self._auth.secret, text)
                    headers = {"API-KEY": self._auth.apikey, "API-TIMESTAMP": timestamp, "API-SIGN": sign }
                else:
                    headers = {'Content-Type': 'application/json'}

                if method == "POST":
                    response = self._session.post(api_url + endpoint, headers=headers, data=json.dumps(params), timeout=self._timeout)
                    self._last_access_time_post = time.time()
                else:
                    response = self._session.get(api_url + endpoint, headers=headers, params=params, timeout=self._timeout)
                    self._last_access_time_get = time.time()
            except Exception as e:
                self._logger.error("Error occured at _request: {}".format(e))
                self._logger.info(traceback.format_exc())
                self._last_access_time_post = time.time()
                self._last_access_time_get = time.time()
                raise e

            ret = json.loads(response.content.decode("utf-8")) if len(response.content) > 0 else ""

            if ret.get('status',0)==0 :
                return ret

            # {'status': 4, 'messages': [{'message_code': 'ERR-5003', 'message_string': 'Requests are too many.'}]
            if ret.get('messages',[{}])[0].get('message_code')=='ERR-5003' :
                # APIリミットエラーの場合には次のアクセスを2秒後まで禁止
                if method=="GET" : self._last_access_time_get = time.time()+2
                else:              self._last_access_time_post = time.time()+2
                self._logger.info( "Retry({}): {}".format(retry_counter,ret) )

            else:
                return ret

            retry_counter -= 1


    def ticker(self, **kwrgs):
        try:
            return self._request("/v1/ticker", params={'symbol':kwrgs.get('symbol', self.symbol)} )
        except Exception as e:
            return {'stat': -999, 'msg': str(e)}

    def getbalance(self):
        try:
            return self._request("/v1/account/assets", private=True)
        except Exception as e:
            return {'stat': -999, 'msg': str(e)}

    def getpositions(self, **kwrgs):
        try:
            return self._request("/v1/openPositions", params={'symbol':kwrgs.get('symbol', self.symbol)}, private=True).get('data',{}).get('list',[])
        except Exception as e:
            return []


    # 証拠金口座の証拠金額 (JPY)
    def getcollateral(self):
        try:
            res = self._request("/v1/account/margin", private=True)
            if res.get('status',-1)!=0 :
                return {'stat': res.get('status',-1), 'msg': res}
            return {'stat': 0, 'collateral': res['data']['actualProfitLoss'], 'msg': res}

        except Exception as e:
            return {'stat': -999, 'msg': traceback.format_exc()}



    def sendorder(self, order_type, side, size, price=0, auto_cancel_after=2592000, **args ):
        """
        sendorder( order_type='LIMIT',       # 指値注文の場合は "LIMIT", 成行注文の場合は "MARKET" を指定します。
                   side='BUY',               # 買い注文の場合は "BUY", 売り注文の場合は "SELL" を指定します。
                   size=0.01,                # 注文数量を指定します。
                   price=4800000,            # 価格を指定します。order_type に "LIMIT" を指定した場合は必須です。
                   auto_cancel_after,        # 0 以外を指定すると指定秒数経過後キャンセルを発行します
                   symbol="BTC_JPY"          # 省略時には起動時に指定した symbol が選択されます
                   timeInForce="GTC",        # FAK ( MARKET STOPの場合のみ設定可能 ) FAS FOK ((Post-onlyの場合はSOK) LIMITの場合のみ設定可能 ) *指定がない場合は成行と逆指値はFAK、指値はFASで注文されます。
                   losscutPrice,             # レバレッジ取引で、executionTypeが LIMIT または STOP の場合のみ設定可能。
                   cancelBefore,             # 
                  ) )

        return: { 'stat': エラーコード,            # オーダー成功時 0
                  'msg':  エラーメッセージ,
                  'ids' : オーダーIDのリスト,      # オーダー成功時 [id,]  オーダー失敗時 []
                }
        """

        def choose_close_order(positions, size):
            remain = size
            pos_id_list = []
            pos_list = [v for v in positions.values() if not v['closeorder']]
            pos_list.sort(key=lambda x: x['size'], reverse=True) # サイズの大きい順にソート
            for p in pos_list:
                if round(remain,8)==0 : break
                if p['size']>0 :
                    order_size = min(remain,p['size'])
                    pos_id_list.append({'positionId':p['posid'], 'size':order_size})
                    positions[p['posid']]['closeorder'] = True
                    self._logger.debug("Flag On0 : {}".format(positions[p['posid']]) )
                    remain -= order_size
            return [{'positionId':int(p['positionId']), 'size':str(round(p['size'],8))} for p in pos_id_list], round(remain,8)

        pos_side = self._position.position.side
        if self.noTrade and (pos_side==side or pos_side=='NONE'):
            self._logger.info("No trade period" )
            return {'stat': -999, 'msg': "No trade period", 'ids': []}

        if self.PendingUntil > time.time() :
            self._logger.info("Order pending : {:.1f}sec".format(self.PendingUntil-time.time()) )
            return {'stat': -999, 'msg': "Order pending : {:.1f}sec".format(self.PendingUntil-time.time()), 'ids': []}

        adjust_flag = args.get('adjust_flag', False)
        # 対応しているオプションだけにする
        params={}
        for k,v in args.items():
            if k=='timeInForce' :
                if v in ["FAK", "FAS", "FOK", "SOK", ] :
                    params[k]=v
            elif k in ['symbol','losscutPrice','cancelBefore']:
                params[k]=v

        # 決済オーダーを出していないポジション数を計算
        settlePosition = []
        remain_position = size
        with self._position.lock :
            if side=='BUY' :
                while True:
                    select_list, remain_position = choose_close_order(self._position.position._short_position, remain_position)
                    if len(select_list)==0 :
                        break
                    settlePosition += select_list
            else:
                while True:
                    select_list, remain_position = choose_close_order(self._position.position._long_position, remain_position)
                    if len(select_list)==0 :
                        break
                    settlePosition += select_list
            self._logger.debug( "ordersize={} remain={}\nsettlePosition={}".format(size, remain_position, settlePosition) )

            ordered_id_list = []
            if len(settlePosition)>0:
                params['symbol']=params.get('symbol', self.symbol)
                params['executionType']=order_type
                params['side']=side
                if price!=0 :
                    params['price']=int(price)
                self._logger.debug("[closeorder] : {}".format(params) )

                try :
                    # いったん Closeorder発注済みフラグを削除（成功してから再度Trueに）
                    for p in settlePosition :
                        if side=='BUY' :
                            self._position.position._short_position[str(p['positionId'])]['closeorder'] = False
                            self._logger.debug("Flag Off1 : {}".format(self._position.position._short_position[str(p['positionId'])]) )
                        else:
                            self._position.position._long_position[str(p['positionId'])]['closeorder'] = False
                            self._logger.debug("Flag Off1 : {}".format(self._position.position._long_position[str(p['positionId'])]) )

                    for p in settlePosition :
                        params['settlePosition'] = [p]
                        res = self._request("/v1/closeOrder", "POST", params=params, private=True )

                        ret_code = res.get('status')
                        if ret_code==0 :

                            ordered_id_list.append(res['data'])

                            # オーダーに成功したら、決済オーダー発出済みフラグをセット
                            if side=='BUY' :
                                self._position.position._short_position[str(p['positionId'])]['closeorder'] = True
                                self._logger.debug("Flag On : {}".format(self._position.position._short_position[str(p['positionId'])]) )
                            else:
                                self._position.position._long_position[str(p['positionId'])]['closeorder'] = True
                                self._logger.debug("Flag On : {}".format(self._position.position._long_position[str(p['positionId'])]) )

                            if self._position and not adjust_flag:
                                self._position.order.new_order( symbol=params['symbol'], id=res['data'] , side=params['side'], price=int(price),
                                                            size=float(p['size']), expire=time.time()+auto_cancel_after, invalidate=time.time()+2592000, closeid=str(p['positionId']) )
                        else:
                            # あるべきポジションが無い
                            if res.get('messages',[{}])[0].get('message_code')=='ERR-254' :
                                # {'status': 1, 'messages': [{'message_code': 'ERR-254', 'message_string': 'Not found position.'}], 'responsetime': '2021-04-02T04:50:26.480Z'}

                                if side=='BUY' :
                                    self._position.position._short_position[str(p['positionId'])]['closeorder'] = True
                                    self._logger.debug("Flag On (lost) : {}".format(self._position.position._short_position[str(p['positionId'])]) )
                                else:
                                    self._position.position._long_position[str(p['positionId'])]['closeorder'] = True
                                    self._logger.debug("Flag On (lost) : {}".format(self._position.position._long_position[str(p['positionId'])]) )

                            self._logger.error("Send closeorder param : {}".format(params) )
                            self._logger.error("Error response [closeorder] : {}".format(res) )

                            # 決済オーダー失敗の場合には、新規オーダーで
                            remain_position += float(p['size'])

                    # 決済だけでオーダー出し終わった場合
                    if round(remain_position,8)==0 :
                        return {'stat':0 , 'msg':"", 'ids':ordered_id_list}

                except Exception as e:
                    self._logger.info(traceback.format_exc())
                    return {'stat': -999, 'msg': str(e), 'ids': ordered_id_list}

                # 決済可能なポジションがない
                # [{'message_code': 'ERR-422', 'message_string': 'There are no open positions that can be settled.'}]
#                elif res.get('messages',[{}])[0].get('message_code')=='ERR-422' :
#                    self._logger.debug("Send closeorder param : {}".format(params) )
#                    self._logger.info("Error response [closeorder] : {}".format(res) )
#                    remain_position = 0

            params['symbol']=params.get('symbol', self.symbol)
            params['executionType']=order_type
            params['side']=side
            params['size']=round(remain_position,8)
            if price!=0 :
                params['price']=int(price)
            self._logger.debug("[sendorder] : {}".format(params) )

            try:
                res = self._request("/v1/order", "POST", params=params, private=True )
            except Exception as e:
                return {'stat': -999, 'msg': str(e), 'ids': ordered_id_list}

            ret_code = res.get('status')
            if ret_code==0 :
                ordered_id_list.append(res['data'])

                if self._position and not adjust_flag:
                    self._position.order.new_order( symbol=params['symbol'], id=res['data'] , side=params['side'], price=int(price),
                                                    size=params['size'], expire=time.time()+auto_cancel_after, invalidate=time.time()+2592000 )
                return {'stat':0 , 'msg':"", 'ids':ordered_id_list}
            else: 
                self._logger.error("Send order param : {}".format(params) )
                self._logger.error("Error response [sendorder] : {}".format(res) )
                return {'stat':ret_code , 'msg':res.get('data'), 'ids':ordered_id_list}


    def cancelorder(self, id, **args ):
        """
        cancelorder( id                          # キャンセルする注文の ID です。
               #-------------以下 bitFlyer独自パラメータ
                   product_code="FX_BTC_JPY"     # 省略時には起動時に指定した symbol が選択されます
                  ) )

        return: { 'stat': エラーコード,      # キャンセル成功時 0
                  'msg':  エラーメッセージ,
                }
        """

        if id not in self._position.order.order_dict :
            self._logger.info("ID:{} is already filled or canceld or expired".format(id) )
            return {'stat':-999 , 'msg':"Order is already filled or canceld or expired"}

        args['orderId']=id

        self._logger.debug("[cancelorder] : {}".format(args) )

        self._position.order.mark_as_invalidate( id )

        try:
            res = self._request("/v1/cancelOrder", "POST", params=args, private=True )
        except Exception as e:
            return {'stat': -999, 'msg': str(e)}

        if res.get('status')!=0 : 
            self._logger.error("Error response [cancelorder] : {}".format(res) )

            # すでにオーダーがなくなっている
            # [{'message_code': 'ERR-5122', 'message_string': 'The request is invalid due to the status of the specified order.'}]
            if res.get('messages',[{}])[0].get('message_code')=='ERR-5122' :
                order_info = self._position.order.mark_as_invalidate( id, timeout=3 ) # 3秒後にオーダーリストから削除(キャンセルと約定が同時になったときには約定を優先させるため)

                # 決済オーダーが無くなっていたら 当該のポジション情報のCloseorder発注済みフラグを削除
                if order_info :
                    closeid = order_info.get('closeid')
                    if closeid :
                        if order_info['side']=='BUY' :
                            self._position.position._short_position[closeid]['closeorder'] = False
                            self._logger.debug("Flag Off invalidate : {}".format(self._position.position._short_position[closeid]) )
                        else:
                            self._position.position._long_position[closeid]['closeorder'] = False
                            self._logger.debug("Flag Off invalidate : {}".format(self._position.position._long_position[closeid]) )

            return {'stat':res.get('status') , 'msg':res.get('messages')}

        return {'stat': 0, 'msg': ""}

