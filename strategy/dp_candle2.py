# -*- coding: utf-8 -*-
from libs.base_strategy import Strategy
import time

class MyStrategy(Strategy):
    """
    未確定足も含めて loop_period間隔で表示するサンプルロジック
    """

    def initialize(self):
        # 自炊ローソク足を生成します、未確定足も都度更新します
        self.candlegen = self.CandleGenerator(timescale=self.parameters['timescale'],
                                              num_of_candle=self.parameters['num_of_candle'],
                                              update_current=True)

        # loop_period間隔で callback で指定した logic関数が呼び出されるように設定
        self.Scheduler(interval=self.parameters['loop_period'], callback=self.logic)

    def logic(self):
        # 未確定足も表示
        self._logger.info( '-'*100 + "\n{}\n\n".format(self.candlegen.candle) )


