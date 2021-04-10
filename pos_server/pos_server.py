# -*- coding: utf-8 -*-
from libs.base_strategy import Strategy
from libs.database import database

from datetime import datetime, timedelta
from datetime import time as datetime_time
from threading import Thread, Lock, Event
import time
import traceback
import socket

MAX_MESSAGE = 2048

class MyStrategy(Strategy):

    def initialize(self):

        # グラフプロット用ハンドラの登録
        self.ws.add_stats = self.add_stats
        self.ws.daily_reset = self.daily_reset
        self._latest_summarize={'pos':0, 'profit':0, 'base':0}

        # データ保管用
        self._database = {}

        # botごとの前回の損益額
        self._last_profit = {}

        # ずれの履歴
        self._diff_count = 0
        self._last_pos_diff = 0
        self._limit_try_count = 0

        # データ更新中ロック
        self.lock = Lock()

        # InfluxDBへの接続
        if 'influxdb' in self.parameters :
            influx_addr = self.parameters['influxdb']
            self.influxdb = database(self._logger, host=influx_addr[0], port=influx_addr[1], database='bots')
        else:
            self.influxdb = database(self._logger)

        # パケットの受信を別スレッドで起動
        comth = Thread(target=self.com_thread)
        comth.daemon = True
        comth.start()

        self.Scheduler(callback=self.delete_check, basetime=0.5, interval=1)
        self.Scheduler(callback=self.summarize_position, basetime=0, interval=30)

    def com_thread(self):

        while True:
            self.com_read()

    def com_read(self):

        # 通信の確立
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.settimeout(3)
        self._logger.info('Create UDP receiver : {}'.format(udp_sock))

        addr = self.parameters['pos_server'][0]
        if addr != 'localhost' and addr != '127.0.0.1':
            addr = '0.0.0.0'
        udp_sock.bind((addr, self.parameters['pos_server'][1]))

        stop_event = Event()
        recvth = Thread(target=self.recv_thread, args=(stop_event,udp_sock))
        recvth.daemon = True
        recvth.start()

        # ウォッチドッグタイマーで監視 15 分受信が無ければソケットを廃棄・再作成
        self.udp_wdt = time.time()
        while time.time()-self.udp_wdt < 900:
            time.sleep( 1 )

        # 通信の終了
        stop_event.set()
        self._logger.error('Close UDP receiver : {}'.format(udp_sock))
        udp_sock.close()
        time.sleep( 30 )

    def recv_thread(self, stop_event, udp_sock):
        while not stop_event.wait(1):
            # UDPパケットの受信
            try:
                packet, addr = udp_sock.recvfrom(MAX_MESSAGE)
            except socket.timeout as e :
                continue
            except Exception as e :
                self._logger.error('UDP socket error : {}\n{}'.format(e,traceback.print_exc()))
                break
            self.udp_wdt = time.time()

            # 受信データのデコード
            message = packet.decode('utf-8')
            symbol = message[0:11].strip()
            pos = float(message[12:29])
            base = float(message[30:47])
            profit = float(message[48:59])
            api1 = int(message[60:65])
            api2 = int(message[66:71])
            strategy = message[73:]

            if self.symbol != symbol:
                self._logger.error("Symbol is not correct. Expect[{}] but receive[{}]".format(self.symbol, symbol))
                self._logger.info(message)

            with self.lock:
                self._database[strategy] = {'pos': pos, 'base': base, 'profit': profit, 'api1': api1, 'api2': api2, 'timestamp': time.time()}
            self._logger.debug("{} : {} : {}".format(symbol, strategy, self._database[strategy]))

        self._logger.info('Exit recv_thread')

    # 300秒ポジション報告の無かったbotはリストから削除
    def delete_check(self):
        with self.lock:
            for strategy, value in self._database.items():
                if time.time()-value['timestamp'] > 300:
                    del self._database[strategy]
                    datas = {}
                    break

    # API経由で実際のポジションを取得
    def check_current_pos(self):
        pos = self.api.getpositions()
        long = 0
        short = 0
        for i in pos:
            self._logger.debug( "OpenPosition : {}".format(i) )
            if i['side'].upper()=='BUY' :
                long += float(i['size'])
            else :
                short += float(i['size'])
        total = round(long-short,8)
        self._logger.debug( "Long : {}  / Short : {}  = Total :{}".format(long,short,total))
        return total

    def summarize_position(self):
        def time_in_range(start, end, x):
            if start <= end:
                return start <= x <= end
            else:
                return start <= x or x <= end

        with self.lock:
            summarize={'pos':0, 'profit':0}
            self._logger.info('\n\n')
            self._logger.info('-'*100)
            for strategy, value in self._database.items():
                self._logger.info("profit({:>+17.8f}) : Pos({:>+17.8f}) : Base({:>+10.3f}) : {:5.1f} : {}".format(
                            value['profit'], value['pos'], value['base'], time.time()-value['timestamp'], strategy))

                try:
                    # 0:00～0:02はグラフに入れない
                    now = datetime_time((datetime.utcnow()+timedelta(hours=9)).hour, (datetime.utcnow()+timedelta(hours=9)).minute, 0)
                    if not time_in_range(datetime_time(0, 0, 0), datetime_time(0, 2, 0), now):
                        # 損益をInfluxに保存
                        self.influxdb.write( measurement="bfsx2",
                                             tags={'exchange': "{}_{}".format(self.exchange,self.symbol), 'bot': strategy},
                                             profit = value['profit'],
                                             profit_diff = value['profit']-self._last_profit.get(strategy,value['profit']),
                                             position = value['pos'])
                        self._last_profit[strategy] = value['profit']
                    else:
                        self._last_profit[strategy] = 0
                except Exception as e:
                    self._logger.exception("Error while exporting to InfluxDB : {}, {}".format(
                        e, traceback.print_exc()))

                summarize['pos'] += value['pos']
                summarize['profit'] += value['profit']

                if summarize.get('base',value['base'])!=value['base'] :
                    self._logger.error('base_offset error')
                summarize['base'] = value['base']

            self._logger.info('-'*100)
            self._logger.info('         profit            position    (     base            target  )            fromAPI             diff')

            # 実際のポジション取得
            actual = self.check_current_pos() if self.api._auth!=None else 0

            # 同じずれが繰り返すとカウントアップ
            pos_diff = round(actual-summarize['pos']-summarize.get('base',0), 8)
            if self._last_pos_diff != pos_diff or abs(pos_diff)<self.minimum_order_size :
                self._diff_count = 0
            if abs(pos_diff)>=self.minimum_order_size and self._diff_count<5:
                self._diff_count += 1
            self._last_pos_diff = pos_diff
            if len(self._database)==0 :
                self._diff_count = 0

            self._logger.info('{:>+17.8f} : {:>17.8f}  ({:>+10.3f} ={:>17.8f}) : {:>17.8f} : {:+17.8f} {}'.format(
                    summarize['profit'], summarize['pos'], summarize.get('base',0), summarize['pos'] + summarize.get('base',0), actual, pos_diff,'*'*self._diff_count))
            self._latest_summarize = summarize

            # 4度続けてポジションがズレていれば成売買で補正行う
            if self.api._auth!=None and self.parameters.get('adjust_position',True) and self._diff_count>=4 :
                self._limit_try_count +=1
                maxsize = self.parameters.get('adjust_max_size',100)

                if self._limit_try_count> self.parameters.get('try_limit_order',0) :
                    if pos_diff < 0:
                        self.sendorder(order_type='MARKET', side='BUY', size=min(-pos_diff,maxsize))
                    else:
                        self.sendorder(order_type='MARKET', side='SELL', size=min(pos_diff,maxsize))
                    self._diff_count = 0
                else:
                    if pos_diff < 0:
                        self.sendorder(order_type='LIMIT', side='BUY', size=min(-pos_diff,maxsize), price=self.ltp-self.parameters.get('imit_order_offset',0), auto_cancel_after=20)
                    else:
                        self.sendorder(order_type='LIMIT', side='SELL', size=min(pos_diff,maxsize), price=self.ltp+self.parameters.get('imit_order_offset',0), auto_cancel_after=20)
            else:
                self._limit_try_count =0


    def add_stats(self):
        return {
               'timestamp': time.time(),

               'ltp': self.ltp,
               'current_pos': self._latest_summarize.get('pos',0) ,
               'average': self.ltp,

               'realized': self._latest_summarize.get('profit',0),
               'commission': 0,
               'unreal': 0,

               'profit': self._latest_summarize.get('profit',0),
               'fixed_profit': self._latest_summarize.get('profit',0),

               'lantency': self.server_latency,
               'api1': self.api_remain1,
               'api2': self.api_remain2,

               'exec_vol': 0,
               'exec_vol_day': 0,
               }

    def daily_reset(self):
        self._latest_summarize={'pos':self._latest_summarize.get('pos',0), 'profit':0, 'base':0}
