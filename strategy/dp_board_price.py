# -*- coding: utf-8 -*-
from libs.base_strategy import Strategy

class MyStrategy(Strategy):
    """
    2秒間隔で板情報を表示し続けるサンプルロジック
    """
    def initialize(self):

        # 為替情報の取得クラス
        from libs.market import GaitameUSDJPY
        self._usdjpy = GaitameUSDJPY(self._logger, keepupdate=True)

        # 複数取引所への接続
        self._exchanges = []

        from libs.exchanges.binance import BinanceWebsocket
        self._exchanges.append( (BinanceWebsocket(self._logger, subscribe={'execution': False, 'board': True}), 0) )

        from libs.exchanges.bitflyer import BitflyerWebsocket
        self._exchanges.append( (BitflyerWebsocket(self._logger, subscribe={'execution': False, 'board': True}), 1) ) # 1にしているのはドル->円換算を行う

        from libs.exchanges.bitmex import BitmexWebsocket
        self._exchanges.append( (BitmexWebsocket(self._logger, subscribe={'execution': False, 'board': True}), 0) )

        from libs.exchanges.bybit import BybitWebsocket
        self._exchanges.append( (BybitWebsocket(self._logger, subscribe={'execution': False, 'board': True}), 0) )

        from libs.exchanges.ftx import FtxWebsocket
        self._exchanges.append( (FtxWebsocket(self._logger, subscribe={'execution': False, 'board': True}), 0) )

        from libs.exchanges.okex import OkexWebsocket
        self._exchanges.append( (OkexWebsocket(self._logger, subscribe={'execution': False, 'board': True}), 0) )

        # 表示用のヘッダ
        self._header = ""
        for e,r in self._exchanges :
            self._header += "{:=^22}+".format(e.__class__.__name__[:-9])

        # 2秒間隔で callback で指定した logic関数が呼び出されるように設定
        self.Scheduler(interval=2, callback=self.logic)

    def logic(self):

        rows = self.parameters['rows']
        price = self.parameters['price']

        self._logger.info(self._header)
        boards = [e.board.get_price_group(splitprice= price*(self._usdjpy.price**r) ) for e,r in self._exchanges]

        for i in reversed(range(rows)):
            s = ''
            for b in boards:
                s += " (${:>+6}){:>10.3f}  |".format((i+1)*price,(b['ask']+[0]*rows)[i])
            self._logger.info( s )

        # mid値とbinance価格との差を表示
        s = ''
        for e,r in self._exchanges:
            s += "--  mid : {:>9.1f} --+".format(e.board.mid)
        self._logger.info( s )

        for i in range(rows):
            s = ''
            for b in boards:
                s += " (${:>+6}){:>10.3f}  |".format((-1-i)*price,(b['bid']+[0]*rows)[i])
            self._logger.info( s )

        self._logger.info('')
