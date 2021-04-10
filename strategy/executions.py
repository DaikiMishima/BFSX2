# -*- coding: utf-8 -*-
from libs.base_strategy import Strategy
from datetime import datetime, timedelta, timezone
from logging import getLogger,INFO,FileHandler
import os
from threading import Thread, Lock
import time
import zipfile

class MyStrategy(Strategy):

    # 初期化
    def initialize(self):

        self.exchanges = []
        self.lock = Lock()

        for exchange, symbol in self.parameters['exchanges']:

            if exchange == 'bitFlyer' :
                from libs.exchanges.bitflyer import BitflyerWebsocket
                websocket = BitflyerWebsocket(self._logger, subscribe={'execution': True}, symbol=symbol)

            elif exchange == 'binance' :
                from libs.exchanges.binance import BinanceWebsocket
                websocket = BinanceWebsocket(self._logger, subscribe={'execution': True}, symbol=symbol)

            elif exchange == 'bitfinex' :
                from libs.exchanges.bitfinex import BitfinexWebsocket
                websocket = BitfinexWebsocket(self._logger, subscribe={'execution': True}, symbol=symbol)

            elif exchange == 'phemex' :
                from libs.exchanges.phemex import PhemexWebsocket
                websocket = PhemexWebsocket(self._logger, subscribe={'execution': True}, symbol=symbol)

            elif exchange == 'bybit' :
                from libs.exchanges.bybit import BybitWebsocket
                websocket = BybitWebsocket(self._logger, subscribe={'execution': True}, symbol=symbol)

            elif exchange == 'GMO' :
                from libs.exchanges.gmo import GmoWebsocket
                websocket = GmoWebsocket(self._logger, subscribe={'execution': True}, symbol=symbol)

            elif exchange == 'bitmex' :
                from libs.exchanges.bitmex import BitmexWebsocket
                websocket = BitmexWebsocket(self._logger, subscribe={'execution': True}, symbol=symbol)

            elif exchange == 'coinbase' :
                from libs.exchanges.coinbase import CoinbaseWebsocket
                websocket = CoinbaseWebsocket(self._logger, subscribe={'execution': True}, symbol=symbol)

            elif exchange == 'deribit' :
                from libs.exchanges.deribit import DeribitWebsocket
                websocket = DeribitWebsocket(self._logger, subscribe={'execution': True}, symbol=symbol)

            elif exchange == 'FTX' :
                from libs.exchanges.ftx import FtxWebsocket
                websocket = FtxWebsocket(self._logger, subscribe={'execution': True}, symbol=symbol)

            elif exchange == 'huobi' :
                from libs.exchanges.huobi import HuobiWebsocket
                websocket = HuobiWebsocket(self._logger, subscribe={'execution': True}, symbol=symbol)

            elif exchange == 'kraken' :
                from libs.exchanges.kraken import KrakenWebsocket
                websocket = KrakenWebsocket(self._logger, subscribe={'execution': True}, symbol=symbol)

            elif exchange == 'okex' :
                from libs.exchanges.okex import OkexWebsocket
                websocket = OkexWebsocket(self._logger, subscribe={'execution': True}, symbol=symbol)


            else:
                self._logger.info( "Not supported : {}".format(exchange) )
                continue

            exec_list = self.ExecutionQueue( callback=self.executions, ws=websocket)
            self.exchanges.append( { 'websocket': websocket, 'name':websocket.__class__.__name__[:-9],
                                     'exec_list': exec_list, 'symbol': symbol.replace('/','-'), 'counter':0 } )

        # 定期的にカウンター表示
        self.Scheduler(callback=self.disp_stat, interval=10)


    # 約定データを処理
    def executions(self):

        # 処理中に次の callback が発生して重複処理しないように
        with self.lock:

            # ファイル名日付部を作成
            today_str = self.filename()

            for exchange in self.exchanges:

                # 初回は出力用ロガーを生成
                if'logger' not in exchange :
                    exchange['logger'] = getLogger(exchange['name'] + exchange['symbol'])
                    exchange['logger'].setLevel(INFO)
                logger = exchange['logger']

                # 日付が変わったらファイルハンドラを変更
                filename = exchange['name'] + '_' + exchange['symbol'] + '_' + today_str
                if exchange.get('filename','') != filename :
                    log_folder = self.parameters['folder'] + exchange['name'] + '/' + exchange['symbol'] + '/'
                    if not os.path.exists(log_folder):
                        os.makedirs(log_folder)
                    for h in logger.handlers :
                        logger.removeHandler(h)
                    fh = FileHandler(log_folder+filename + '.csv')
                    logger.addHandler(fh)

                    # 前日のログ圧縮を別スレッドで起動
                    if 'filename' in  exchange:
                        exchange['yesterday'] = exchange['filename']
                        Thread(target=self._ziplog, args=(log_folder, exchange['yesterday'])).start()
                    exchange['filename'] = filename

                # 約定データの書き出し
                while len(exchange['exec_list'])!=0:
                    i = exchange['exec_list'].popleft()
                    logger.info("{},{},{},{},{},{}".format(i['exec_date'], i['side'], i['price'], i['size'], i['id'], exchange['websocket'].execution.avg_latency_1s))
                    exchange['counter'] +=1


    # ファイルの圧縮
    def _ziplog(self,log_folder, previous_filename):
        self._logger.info( "Zipping {}.csv to {}.zip".format(previous_filename,previous_filename) )
        with zipfile.ZipFile(log_folder + previous_filename + '.zip', 'w') as log_zip:
            log_zip.write(log_folder + previous_filename + '.csv', arcname=previous_filename + '.csv', compress_type=zipfile.ZIP_DEFLATED)
        self._logger.info( "Zipped to {}.zip".format(previous_filename) )
        os.remove(log_folder + previous_filename + '.csv')
        self._logger.info( "Deleted {}.csv".format(previous_filename) )


    # 現在時刻のファイル名を生成（サーバー時刻によらずJSTで生成）
    def filename(self):
        return (datetime.utcfromtimestamp(time.time()) + timedelta(hours=9)).replace(tzinfo=timezone(timedelta(hours=9),'JST')).strftime('%Y-%m-%d')


    # 定期的にカウンター表示
    def disp_stat(self):
        self._logger.info( '-'*50 )
        for exchange in self.exchanges:
            self._logger.info( "{:<25} : {}executions".format(exchange['name'] + ' / ' + exchange['symbol'], exchange['counter']) )
            exchange['counter'] = 0
