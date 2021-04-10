# coding: utf-8
#!/usr/bin/python3

import time
from collections import deque
from threading import Thread, Event
from datetime import datetime, timedelta, timezone
import pandas as pd
import traceback
import numpy as np
pd.set_option('display.expand_frame_repr', False)

class CandleGenerator(object):

    def __init__( self,logger, websocket, timescale, num_of_candle=500, update_current=False, callback=None  ):
        self._logger = logger
        self._websocket = websocket
        self._timescale = timescale
        self._num_of_candle = num_of_candle
        self._callback = callback
        self._update_current = update_current

        # 約定をためるキュー
        self._execution_buffer = deque(maxlen=timescale*10000)
        self._executions = deque(maxlen=timescale*10000)

        # ローソク足データ
        self._candle = pd.DataFrame(index=[], columns=['date', 'open', 'high', 'low', 'close', 'volume', 'buy_volume', 'sell_volume',
                                                      'count', 'buy_count', 'sell_count', 'value', 'buy_value', 'sell_value']).set_index('date')
        self._current_ohlc = {'date':0, 'open': 0, 'high': 0, 'low': 0, 'close': 0, 'volume': 0, 'buy_volume': 0, 'sell_volume': 0,
                              'count': 0, 'buy_count': 0, 'sell_count': 0, 'value': 0, 'buy_value': 0, 'sell_value': 0}


        self._lastcandle = datetime.now(timezone(timedelta(hours=9), 'JST'))-timedelta(minutes=10)
        self._last_conveted = 0

        self._candle_generate = Event()
        self._stop = False
        generate_thread = Thread(target=self._loop)
        generate_thread.daemon = True
        generate_thread.start()
        clean_thread = Thread(target=self._clean_up)
        clean_thread.daemon = True
        clean_thread.start()
        self._logger.stop_list.append([self.stop,self._clean_up])

        self._websocket.execution.add_handler( exec_que=self._execution_buffer, handler=self._on_execution )

    def _update_current_candle( self, i ):

        # 現在足のデータ生成
        price = int(i['price'])
        size = i['size']
        c = self._current_ohlc
        if c['open'] == 0:
            c['open'] = c['high'] = c['low'] = price
        c['high'] = max(price, c['high'])
        c['low'] = min(price, c['low'])
        c['close'] = price
        c['volume'] += size
        c['count'] += 1
        c['value'] += price * size

        if i['side'] == 'BUY':
            c['buy_volume'] += size
            c['buy_count'] += 1
            c['buy_value'] += price * size
        else:
            c['sell_volume'] += size
            c['sell_count'] += 1
            c['sell_value'] += price * size

    def _loop(self):
        while not self._stop:
            self._candle_generate.wait()
            self._candle_generate.clear()
            self._updatecandle()

    def stop(self):
        self._stop = True

    def _on_execution( self ):
        while len(self._execution_buffer)>0:
            i = self._execution_buffer.popleft()

            self._executions.append(i)
            if self._update_current :
                self._update_current_candle(i)

        # 送られてきたexecutionの時間が前回ローソク足更新時の最後の足よりもtimescale進んでいればローソク足の更新作業を行う
        if self._executions[-1]['exec_date'].timestamp() - self._lastcandle.timestamp() >= self._timescale:
            self._candle_generate.set()

    # executionリストをもとに指定秒足のローソクを生成
    def _updatecandle(self):
        try:
            tmpExecutions = list(self._executions)
            self.raw = pd.DataFrame([[
                    tick['exec_date'], tick['price'],
                    tick['size'],
                    tick['size']if tick['side'] == 'BUY'else 0,
                    tick['size']if tick['side'] == 'SELL'else 0,
                    1 if tick['size'] != 0 else 0,
                    1 if tick['side'] == 'BUY' else 0,
                    1 if tick['side'] == 'SELL' else 0,
                    tick['price'] * tick['size'],
                    tick['price'] * tick['size'] if tick['side'] == 'BUY' else 0,
                    tick['price'] * tick['size'] if tick['side'] == 'SELL' else 0
                    ] for tick in tmpExecutions],
                    columns=['date', 'price', 'volume', 'buy_volume', 'sell_volume', 'count', 'buy_count', 'sell_count',
                             'value', 'buy_value', 'sell_value'])
            tmpcandle = self.raw.set_index('date').resample(str(self._timescale)+'s').agg({
                    'price': 'ohlc', 'volume': 'sum', 'buy_volume': 'sum', 'sell_volume': 'sum',
                     'count': 'sum', 'buy_count': 'sum', 'sell_count': 'sum',
                    'value': 'sum', 'buy_value': 'sum', 'sell_value': 'sum'})
            tmpcandle.columns = tmpcandle.columns.droplevel()

            if len(self._candle)<2 :
                self._candle = tmpcandle
            else:
                # 前回変換済みのところを検索
                last_index = np.where(tmpcandle.index.values>=self._last_conveted)[0][0]-len(tmpcandle) if self._last_conveted!=0 else -len(tmpcandle)
                self._candle = pd.concat([self._candle[:-2], tmpcandle[last_index:]])
            self._last_conveted = self.candle.tail(2).index.values[0]

            self._candle['close'] = self._candle['close'].fillna(method='ffill')
            self._candle['open'] = self._candle['open'].fillna(self._candle['close'])
            self._candle['high'] = self._candle['high'].fillna(self._candle['close'])
            self._candle['low'] = self._candle['low'].fillna(self._candle['close'])

            # 必要な本数だけにカット
            self._candle = self._candle.tail(self._num_of_candle+1)

            # 現在足データの更新
            if self._update_current :
                self._current_ohlc = {'date':self._candle.index[-1],
                                      'open': self._candle['open'][-1],
                                      'high': self._candle['high'][-1],
                                      'low': self._candle['low'][-1],
                                      'close': self._candle['close'][-1],
                                      'volume': self._candle['volume'][-1],
                                      'buy_volume': self._candle['buy_volume'][-1],
                                      'sell_volume': self._candle['sell_volume'][-1],
                                      'count': self._candle['count'][-1],
                                      'buy_count': self._candle['buy_count'][-1],
                                      'sell_count': self._candle['sell_count'][-1],
                                      'value': self._candle['value'][-1],
                                      'buy_value': self._candle['buy_value'][-1],
                                      'sell_value': self._candle['sell_value'][-1] }

            if self._lastcandle!=self._candle.index[-1] and self._callback!=None :
                # ローソク足更新時のロジックを呼び出す
                self._callback()

            self._lastcandle = self._candle.index[-1]

        except Exception as e:
            self._logger.error("Error occured at _updatecandle: {}".format(e))
            self._logger.info(traceback.format_exc())

    # 負荷軽減のため、ローソク足に変換済みの約定履歴を破棄
    def _clean_up(self):
        while not self._stop:
            time.sleep(10)
            self._reduce_exeution_buffer()

    def _reduce_exeution_buffer(self):
        if len(self._executions) == 0: return
        if self._last_conveted == 0:  return

        while len(self._executions)>0:
            i = self._executions.popleft()
            if int(self._last_conveted)/1000000000 <= i['exec_date'].timestamp():
                self._executions.appendleft(i)
                break

    # 確定ローソク足の時刻
    @property
    def date(self):
        return self._candle.index[-2] if len(self._candle)>1 else 0

    @property
    def candle(self):
        if not self._update_current :
            return self._candle

        # 最後に未確定ローソクを追加
        current_candle = pd.DataFrame.from_dict(self._current_ohlc, orient='index').T.set_index('date')
        candle = pd.concat([self._candle[:-1],current_candle])
        candle[['open','high','low','close']] = candle[['open','high','low','close']].applymap("{:.1f}".format)
        return candle
