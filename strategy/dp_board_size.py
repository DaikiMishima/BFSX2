# -*- coding: utf-8 -*-
from libs.base_strategy import Strategy

class MyStrategy(Strategy):
    """
    2秒間隔で板情報を表示し続けるサンプルロジック
    """
    def initialize(self):
        self._exchanges = []

        from libs.exchanges.binance import BinanceWebsocket
        self._exchanges.append( BinanceWebsocket(self._logger, subscribe={'execution': False, 'board': True}) )

        from libs.exchanges.bitflyer import BitflyerWebsocket
        self._exchanges.append( BitflyerWebsocket(self._logger, subscribe={'execution': False, 'board': True}) )

        from libs.exchanges.bitmex import BitmexWebsocket
        self._exchanges.append( BitmexWebsocket(self._logger, subscribe={'execution': False, 'board': True}) )

        from libs.exchanges.bybit import BybitWebsocket
        self._exchanges.append( BybitWebsocket(self._logger, subscribe={'execution': False, 'board': True}) )

        from libs.exchanges.ftx import FtxWebsocket
        self._exchanges.append( FtxWebsocket(self._logger, subscribe={'execution': False, 'board': True}) )

        from libs.exchanges.okex import OkexWebsocket
        self._exchanges.append( OkexWebsocket(self._logger, subscribe={'execution': False, 'board': True}) )

        # 表示用のヘッダ
        self._header = ""
        for e in self._exchanges :
            self._header += "{:=^24}+".format(e.__class__.__name__[:-9])

        # 2秒間隔で callback で指定した logic関数が呼び出されるように設定
        self.Scheduler(interval=2, callback=self.logic)

    def logic(self):

        rows = self.parameters['rows']
        size = self.parameters['size']

        self._logger.info(self._header)
        boards = [(e.board.get_size_group(splitsize= size , limitnum=rows),e.board.mid) for e in self._exchanges]

        for i in reversed(range(rows)):
            s = ''
            for b in boards:
                s += "  {:>10.2f} ({:>+7.1f})  |".format((b[0]['ask']+[0]*rows)[i],(b[0]['ask']+[0]*rows)[i]-b[1])
            self._logger.info( s )
        s = ''
        for b in boards:
            s += "===   mid {:>10.2f} ===+".format(b[1])
        self._logger.info( s )
        for i in range(rows):
            s = ''
            for b in boards:
                s += "  {:>10.2f} ({:>+7.1f})  |".format((b[0]['bid']+[0]*rows)[i],(b[0]['bid']+[0]*rows)[i]-b[1])
            self._logger.info( s )

        self._logger.info( s )
        self._logger.info('')
