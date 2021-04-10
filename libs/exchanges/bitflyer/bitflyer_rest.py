# coding: utf-8
#!/usr/bin/python3

from datetime import datetime, timedelta, timezone
import json
import requests
import pandas as pd
import time
import traceback
import urllib
from libs.utils.scheduler import Scheduler
from libs.exchanges.base_module.base_rest import RestAPIExchange

# https://lightning.bitflyer.com/docs?lang=ja

class BitflyerAPI(RestAPIExchange):

    def __init__(self, logger, symbol='FX_BTC_JPY', testnet=False, auth=None, position=None, timeout=None):
        self._api_url = "https://api.bitflyer.com"
        self._symbol = symbol

        self._session = self._new_session()

        # API Limit
        self.UserLimitPeriod = 300
        self.api_remain1 = 500
        self.HttpAccessTime1 = time.time()

        self.OrderLimitPeriod = 300
        self.api_remain2 = 300
        self.HttpAccessTime2 = time.time()

        self.PerIpLimitPeriod = 300
        self.api_remain3 = 500
        self.HttpAccessTime3 = time.time()

        RestAPIExchange.__init__(self,logger, symbol, auth, position, timeout)

        # APIアクセスしないときにも一定期間たったらAPI制限を解除するためのスレッド
        Scheduler(self._logger, interval=1, callback=self._limit_check)

        # 定期的にpublucAPIへアクセスしてIPごとのアクセス制限をチェック
        self.server_health='NONE'
        Scheduler(self._logger, interval=60, callback=self._check_server_status)

    _minimum_order_size_dict = {'FX_BTC_JPY':0.01, 'BTC_JPY':0.001, 'ETH_JPY':0.01, 'ETH_BTC':0.01, 'BCH_BTC':0.01}
    def minimum_order_size(self, symbol=None):
        return self._minimum_order_size_dict.get(symbol or self._symbol)

    def _new_session(self):
        return requests.Session()

    def _request(self, endpoint, method="GET", params=None, private=False):

        # IPごとのアクセスカウントをカウントダウン
        self.api_remain3 -= 1

        if method == "POST":
            body = json.dumps(params)
        else:
            body = "?" + urllib.parse.urlencode(params) if params else ""
        try:
            if private and self._auth!=None :
                access_timestamp = str(time.time())
                text = access_timestamp + method + endpoint + body
                access_sign = self._auth.generate_sign(self._auth.secret, text)
                headers = {"ACCESS-KEY": self._auth.apikey, "ACCESS-TIMESTAMP": access_timestamp,
                               "ACCESS-SIGN": access_sign, "Content-Type": "application/json" }
            else:
                headers = {'Content-Type': 'application/json'}

            if method == "POST":
                response = self._session.post(self._api_url + endpoint, headers=headers, data=body, timeout=self._timeout)
            else:
                response = self._session.get(self._api_url + endpoint, headers=headers, params=params, timeout=self._timeout)
        except Exception as e:
            self._logger.error("Error occured at _request: {}".format(e))
            self._logger.info(traceback.format_exc())
            raise e

#        self._logger.debug( "endpoint: {}  / header: {}".format(endpoint,response.headers) )

        if private :
            self.UserLimitPeriod = int(response.headers.get('X-RateLimit-Period',self.UserLimitPeriod))
            self.api_remain1 = int(response.headers.get('X-RateLimit-Remaining',self.api_remain1))
            if 'X-RateLimit-Period' in response.headers :
                self.HttpAccessTime1 = time.time()
        else:
            self.PerIpLimitPeriod = int(response.headers.get('X-RateLimit-Period',self.PerIpLimitPeriod))
            self.api_remain3 = int(response.headers.get('X-RateLimit-Remaining',self.api_remain3))
            if 'X-RateLimit-Period' in response.headers :
                self.HttpAccessTime3 = time.time()

        self.OrderLimitPeriod = int(response.headers.get('X-OrderRequest-RateLimit-Period',self.OrderLimitPeriod))
        self.api_remain2 = int(response.headers.get('X-OrderRequest-RateLimit-Remaining',self.api_remain2))
        if 'X-OrderRequest-RateLimit-Period' in response.headers :
            self.HttpAccessTime2 = time.time()

        return json.loads(response.content.decode("utf-8")) if len(response.content) > 0 else ""

    def _limit_check(self):
        self._logger.debug( "perUser {} / orderAPI {} / perIP {}".format(self.api_remain1, self.api_remain2, self.api_remain3) )
        # API制限のクリア
        if self.UserLimitPeriod!=0 :
            if time.time()>self.HttpAccessTime1+self.UserLimitPeriod :
                self.api_remain1 = 500
                self.UserLimitPeriod = 0
        if self.OrderLimitPeriod!=0 :
            if time.time()>self.HttpAccessTime2+self.OrderLimitPeriod :
                self.api_remain2 = 300
                self.OrderLimitPeriod = 0
        if self.PerIpLimitPeriod!=0 :
            if time.time()>self.HttpAccessTime3+self.PerIpLimitPeriod :
                self.api_remain3 = 500
                self.PerIpLimitPeriod = 0

    def _check_server_status(self):
        try:
            res = self._request("/v1/gethealth")
            self.server_health = res['status']
#            self._logger.debug(self.server_health)
        except:
            self.server_health = "FAIL"

    def ticker(self, **kwrgs):
        try:
            return self._request("/v1/ticker", params={'product_code':kwrgs.get('symbol', self.symbol)} )
        except Exception as e:
            return {'stat': -999, 'msg': str(e)}

    # 現物口座の残高 (JPY)
    def getbalance(self):
        try:
            res = self._request("/v1/me/getbalance", private=True)
            balance = 0
            for r in res :
                try:
                    if r['currency_code']=='JPY' :   balance = float(r['amount'])
                except:
                    pass
            return {'stat': 0, 'balance': balance, 'msg': res}

        except Exception as e:
            return {'stat': -999, 'msg': str(e)}

    def getpositions(self, **kwrgs):
        try:
            return self._request("/v1/me/getpositions", params={'product_code':kwrgs.get('symbol', self.symbol)}, private=True)
        except Exception as e:
            return []



    # 証拠金口座の証拠金額 (JPY)
    def getcollateral(self):
        try:
            res = self._request("/v1/me/getcollateral", private=True)
            return {'stat': 0, 'collateral': res.get('collateral',0), 'msg': res}
        except Exception as e:
            return {'stat': -999, 'msg': traceback.format_exc()}

    def sendorder(self, order_type, side, size, price=0, auto_cancel_after=2592000, **args ):
        """
        sendorder( order_type='LIMIT',       # 指値注文の場合は "LIMIT", 成行注文の場合は "MARKET" を指定します。
                   side='BUY',               # 買い注文の場合は "BUY", 売り注文の場合は "SELL" を指定します。
                   size=0.01,                # 注文数量を指定します。
                   price=4800000,            # 価格を指定します。order_type に "LIMIT" を指定した場合は必須です。
                   auto_cancel_after,        # 0 以外を指定すると指定秒数経過後キャンセルを発行します
                   product_code="FX_BTC_JPY" # 省略時には起動時に指定した symbol が選択されます
                   time_in_force="GTC",      # 執行数量条件 を "GTC", "IOC", "FOK" のいずれかで指定します。省略した場合の値は "GTC" です。
                   minute_to_expire=1,       # 期限切れまでの時間を分で指定します。省略した場合の値は 43200 (30 日間) です。
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

        if self.api_remain1<50 :
            self._logger.info("LimitRemaining(api_remain1) : {}/500".format(self.api_remain1) )
            return {'stat': -999, 'msg': "LimitRemaining(api_remain1) "+str(self.api_remain1)+"/500", 'ids': []}

        if self.api_remain2<50 :
            self._logger.info("OrderLimitRemaining(api_remain2) : {}/300".format(self.api_remain2) )
            return {'stat': -999, 'msg': "LimitRemaining(api_remain2) "+str(self.api_remain2)+"/300", 'ids': []}

        if self.api_remain3<50 :
            self._logger.info("OrderLimitRemaining(api_remain3) : {}/500".format(self.api_remain3) )
            return {'stat': -999, 'msg': "LimitRemaining(api_remain3) "+str(self.api_remain3)+"/300", 'ids': []}

        if self.PendingUntil > time.time() :
            self._logger.info("Order pending : {:.1f}sec".format(self.PendingUntil-time.time()) )
            return {'stat': -999, 'msg': "Order pending : {:.1f}sec".format(self.PendingUntil-time.time()), 'ids': []}

        adjust_flag = args.get('adjust_flag', False)
        # 対応しているオプションだけにする
        params={}
        for k,v in args.items():
            if k=='time_in_force' :
                if v in ["GTC", "IOC", "FOK"] :
                    params[k]=v
            elif k in ['product_code','minute_to_expire']:
                params[k]=v

        params['product_code']=params.get('product_code', self.symbol)
        params['child_order_type']=order_type
        params['side']=side
        params['size']=round(size,8)
        params['price']=int(price)

        # 最低取引量のチェック（無駄なAPIを叩かないように事前にチェック）
        if params['size']<self.minimum_order_size(symbol=params['product_code']) :
            return {'stat': -153, 'msg': '最低取引数量を満たしていません', 'ids': []}

        self._logger.debug("[sendorder] : {}".format(params) )
        with self._position.lock :
            try:
                res = self._request("/v1/me/sendchildorder", "POST", params=params, private=True )
            except Exception as e:
                return {'stat': -999, 'msg': str(e), 'ids': []}

            if res and "JRF" in str(res) : 
                if self._position and not adjust_flag:
                    invalidate = min(auto_cancel_after, params.get('minute_to_expire',43200)*60)+120
                    self._position.order.new_order( symbol=params['product_code'], id=res['child_order_acceptance_id'] ,
                                                    side=side, price=price, size=size, expire=time.time()+auto_cancel_after, invalidate=time.time()+invalidate )
                return {'stat':0 , 'msg':"", 'ids':[res['child_order_acceptance_id']]}
            else: 
                # オーダー失敗
                self._logger.error("Send order param : {}".format(params) )
                self._logger.error("Error response [sendorder] : {}".format(res) )
                return {'stat':res.get('status') , 'msg':res.get('error_message'), 'ids':[]}

    def cancelorder(self, id, **args ):
        """
        cancelorder( id                          # キャンセルする注文の ID です。
               #-------------以下 bitFlyer独自パラメータ
                   product_code="FX_BTC_JPY"     # 省略時には起動時に指定した symbol が選択されます
                    )

        return: { 'stat': エラーコード,      # キャンセル成功時 0
                  'msg':  エラーメッセージ,
                }
        """

        if id not in self._position.order.order_dict :
            self._logger.info("ID:{} is already filled or canceld or expired".format(id) )
            return {'stat':-999 , 'msg':"Order is already filled or canceld or expired"}

        if self.api_remain1<50 :
            self._logger.info("LimitRemaining : {}".format(self.api_remain1) )
            return {'stat': -999, 'msg': 'LimitRemaining(api_remain1) '+str(self.api_remain1)+'/500'}

        if self.api_remain3<50 :
            self._logger.info("OrderLimitRemaining(api_remain3) : {}/500".format(self.api_remain3) )
            return {'stat': -999, 'msg': "LimitRemaining(api_remain3) "+str(self.api_remain3)+"/300"}

        args['child_order_acceptance_id']=id

        self._logger.debug("[cancelorder] : {}".format(args) )
        args['product_code']=args.get("product_code", self._position.order.order_dict[id]['symbol'] )

        self._position.order.mark_as_invalidate( id )

        try:
            res = self._request("/v1/me/cancelchildorder", "POST", params=args, private=True )
        except Exception as e:
            return {'stat': -999, 'msg': str(e)}

        if res :
            self._logger.error("Error response [cancelorder] : {}".format(res) )
            return {'stat':res.get('status') , 'msg':res.get('error_message')}

        return {'stat': 0, 'msg': ""}


    def get_candles( self, timeframe, numofcandle, firsttime=None ):
        """
        get_candles( timeframe   # ローソク足の長さ（単位：分）
                     numofcandle # ローソク足の数
                     firsttime   # 指定されればそこからのローソク足を取得
                    )

        return: candle           # pandas形式のローソク足
        """

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'}
        limittime = datetime.now(tz=timezone.utc)-timedelta(seconds=timeframe*60*(numofcandle+1))
        endtime = firsttime.to_pydatetime() if firsttime else limittime
        try:
            responce = requests.get( f"https://lightchart.bitflyer.com/api/ohlc?symbol={self.symbol}&period=m", headers= headers).json()

            lasttime = responce[0][0]

            # 未確定足
            c=responce[0]
            df = pd.DataFrame([[datetime.fromtimestamp(int(str(c[0])[:10]), tz=timezone.utc), c[1], c[2], c[3], c[4], c[5], c[6], c[7], c[8], c[9] ]],
                            columns=["date", "open", "high", "low", "close", "volume","ask_volume", "bid_volume", "sell_volume", "buy_volume"]).set_index("date")

            if datetime.fromtimestamp(int(str(responce[1][0])[:10]), tz=timezone.utc) < endtime :
                return None

        except Exception as e:
            self._logger.info( responce )
            self._logger.exception( e )
            return None

        keep_running = True
        while keep_running:

            df_tmp = pd.DataFrame( columns=["date", "open", "high", "low", "close", "volume", "ask_volume", "bid_volume", "sell_volume", "buy_volume"] )
 
            responce = requests.get( f"https://lightchart.bitflyer.com/api/ohlc?symbol={self.symbol}&period=m&before={lasttime}", headers= headers).json()
            self._logger.info( "Fetch candles from lightchart API" )

            try:
                if len(responce)==0 :
                    keep_running = False
                else:
                    tm_pool = []
                    for i in range(0, len(responce)):
                        c=responce[i]
                        last = int(str(c[0])[:10])  # タイムスタンプのミリ秒を削除

                        if datetime.fromtimestamp(last, tz=timezone.utc) < endtime or datetime.fromtimestamp(last, tz=timezone.utc) < limittime:
                            keep_running = False
                            break

                        tm_pool.append([datetime.fromtimestamp(last, tz=timezone.utc), c[1], c[2], c[3], c[4], c[5], c[6], c[7], c[8], c[9] ] )

                    df_tmp = pd.concat([df_tmp,pd.DataFrame(reversed(tm_pool), columns=["date", "open", "high", "low", "close", "volume","ask_volume", "bid_volume", "sell_volume", "buy_volume"])])

                    self._logger.info( "  from  : {}".format(tm_pool[-1][0].astimezone(timezone(timedelta(hours=9), 'JST'))) )
                    self._logger.info( "  until : {}".format(tm_pool[0][0].astimezone(timezone(timedelta(hours=9), 'JST'))) )

                    df = pd.concat([df_tmp.set_index("date"), df])

                    self._logger.info( "  Total {} candles\n".format(int(len(df)/timeframe)) )

                    lasttime = str(last-60)+"000"

                if keep_running : time.sleep(3)

            except Exception as e:
                self._logger.info( responce )
                self._logger.exception( e )
                return None
                break

        df = df.sort_index()
        df = df.resample(f'{timeframe*60}S').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last',
                         'volume': 'sum', 'ask_volume': 'sum', 'bid_volume': 'sum', 'sell_volume': 'sum', 'buy_volume': 'sum' })
        df['close'] = df['close'].fillna(method='ffill')
        df['open'] = df['open'].fillna(df['close'])
        df['high'] = df['high'].fillna(df['close'])
        df['low'] = df['low'].fillna(df['close'])

        return df.tz_convert(timezone(timedelta(hours=9), 'JST'))
