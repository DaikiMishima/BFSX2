# -*- coding: utf-8 -*-
from libs.base_strategy import Strategy
import talib as ta
import math

class MyStrategy(Strategy):

    def initialize(self):
        # 自炊ローソク足を作るクラスを起動、ローソク足が更新されたら callbackで指定したlogic関数が呼び出す(未確定足も都度更新）
        self.candlegen = self.CandleGenerator(callback=self.logic, timescale=self.parameters['timescale'],
                                              num_of_candle=self.parameters['num_of_candle'], update_current=True)

        # loop_period間隔で callback で指定したloss_cut_check関数が呼び出されるように設定
        self.Scheduler(callback=self.loss_cut_check, interval=self.parameters['loop_period'])

    def logic(self):
        # 未確定足もローソク足に含まれているので最後の１本を削除
        candle = self.candlegen.candle[:-1]

        # 自炊ローソクが計算に必要な本数がたまっていない場合には取引しない
        if len(candle) <= self.parameters['mfi_period'] :
            self._logger.info( 'Waiting candles.  {}/{}'.format(len(candle),self.parameters['mfi_period']) )
            return

        # 指数の計算
        mfi = ta.MFI(candle['high'],candle['low'],candle['close'],candle['volume'], self.parameters['mfi_period'])*2-100

        self._logger.info( '[{} LTP:{:.0f}] MFI:{:>7.2f} Profit:{:>+8.0f}({:+4.0f}) Position:{:.3f} Delay:{:>4.0f}ms'.format(
            self.candlegen.date, self.ltp, mfi[-1], self.current_profit, self.current_profit_unreal, self.current_pos, self.server_latency) )

        # MAX_LOTに近づくと指値を離して約定しづらくする
        buyprice  = self.ltp - max(0,int(self.parameters['position_slide']*self.current_pos/self.parameters['max_lot']))-self.parameters['depth']
        sellprice = self.ltp - min(0,int(self.parameters['position_slide']*self.current_pos/self.parameters['max_lot']))+self.parameters['depth']

        # 閾値を超えていれば売買
        if self.current_pos<=self.parameters['max_lot'] and mfi[-1] < -self.parameters['mfi_limit'] :
            self.sendorder(order_type='LIMIT', side='BUY', size=self.parameters['lotsize'], price=buyprice)

        if self.current_pos>=-self.parameters['max_lot'] and mfi[-1] > self.parameters['mfi_limit'] :
            self.sendorder(order_type='LIMIT', side='SELL', size=self.parameters['lotsize'], price=sellprice)


    def loss_cut_check(self):

        # マイナスポジで大きな買いが入った場合には成でクローズ
        if self.current_pos<0 and self.vol_rate()>self.parameters['volume_limit'] :
            return self.close_position()

        # プラスポジで大きな売りが入った場合には成でクローズ
        if self.current_pos>0 and self.vol_rate()<-self.parameters['volume_limit'] :
            return self.close_position()

    def vol_rate(self):
        # 直近のローソク足（未確定足）の取引ボリュームの売買比率を算出
        vol_rate = math.fabs(math.sqrt(self.candlegen.candle['buy_volume'][-1]) - math.sqrt(self.candlegen.candle['sell_volume'][-1]))
        if self.candlegen.candle['buy_volume'][-1] < self.candlegen.candle['sell_volume'][-1] :
            vol_rate = -vol_rate
        return vol_rate
