# -*- coding: utf-8 -*-
from libs.base_strategy import Strategy
import time

class MyStrategy(Strategy):
    """
    未確定足も含めて loop_period間隔で表示するサンプルロジック
    """

    def initialize(self):
        # bybitのwebsocketを受信するクラスを作成
        from libs.exchanges.bybit import BybitWebsocket
        ref = BybitWebsocket(self._logger, subscribe={'execution': True})

        # 引数wsに作成したwebsocket受信クラスを指定して自炊してローソク足を生成する
        self.candlegen = self.CandleGenerator(timescale=10,
                       num_of_candle=500, callback=self.logic, ws=ref)

    def logic(self):
        # 未確定足も表示
        self._logger.info( '-'*100 + "\n{}\n\n".format(self.candlegen.candle) )


