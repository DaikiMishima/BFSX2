# -*- coding: utf-8 -*-
from threading import Event
import time

# それぞれのメンバ・関数は、親クラス(backtestまたはtrade)を呼び出す

class Strategy:

    _exec_que_list = []
    _board_que_list = []

    def __init__(self, logger, exchange):
        self._logger = logger
        self.ws, self.api, self.exchange = (exchange)



    def CandleGenerator(self, timescale, num_of_candle=500, update_current=False, callback=None, ws=None):
        from libs.candle import CandleGenerator
        return CandleGenerator(self._logger, (ws or self.ws), timescale=timescale, num_of_candle=num_of_candle, update_current=update_current, callback=callback)

    def Scheduler(self, interval=1, basetime=None, callback=None, args=()):
        from libs.utils.scheduler import Scheduler
        return Scheduler(self._logger, interval=interval, basetime=basetime, callback=callback, args=args)

    def ExecutionQueue(self, callback, ws=None):
        from collections import deque
        exec_que = deque(maxlen=10000)
        self._exec_que_list.append([ws,exec_que])
        (ws or self.ws).execution.add_handler( exec_que=exec_que, handler=callback )
        return exec_que

    def BoardQueue(self, callback, ws=None):
        from collections import deque
        board_que = deque(maxlen=10000)
        self._board_que_list.append([ws,board_que])
        (ws or self.ws).board.add_handler( board_que=board_que, handler=callback )
        return board_que

    def AddBoardUpdateHandler(self, callback, ws=None):
        (ws or self.ws).board.add_handler( handler=callback )

    def AddExecutionHandler(self, callback, ws=None):
        (ws or self.ws).my.order.add_handler( handler=callback )




    def sendorder(self, order_type, side, size, **kwargs):
        if not self.ws.is_connected() :
            self._logger.error( "Private ws is not connected" )
            return {'stat': -999, 'msg': "Private ws is not connected", 'id': None}

        res = self.api.sendorder(order_type=order_type, side=side, size=round(size,8),
                                **dict(self._strategy_param.get('order',{}).get('option',{}), **kwargs))

        # 成り行き売買のあとは所定の時間のオーダーを禁止させるパラメータ
        if order_type=="MARKET" and 'wait_after_order' in self._strategy_param.get('order',[]) :
            self.api.PendingUntil = time.time()+self._strategy_param['order']['wait_after_order']
            self._logger.info( "Order will be disabled next {}secs".format(self._strategy_param['order']['wait_after_order']) )

        return res

    def cancelorder(self, id, **args):
        return self.api.cancelorder(id=id, **args)

    def close_position(self):
        if self.current_pos >= self.minimum_order_size:
            res = self.sendorder(order_type='MARKET', side='SELL', size=self.current_pos)
            if res.get('id') :
                self._logger.info('        Emergency SELL!!! ({})'.format(res.get('id')))
                return True
            self._logger.info('        Close Position Error ({})'.format(res))

        elif self.current_pos <= -self.minimum_order_size:
            res = self.sendorder(order_type='MARKET', side='BUY', size=-self.current_pos)
            if res.get('id') :
                self._logger.info('        Emergency BUY!!! ({})'.format(res.get('id')))
                return True
            self._logger.info('        Close Position Error ({})'.format(res))

        return False

    def getcollateral_api(self):
        return self.api.getcollateral()

    @property
    def collateral_rate(self):
        return self.ws.units()['unitrate']

    def set_parameters(self, trade_param, strategy_param):
        self._trade_param = trade_param
        self._strategy_param = strategy_param
        self.parameters = self._strategy_param['parameters']

    @property
    def symbol(self):
        return self.api.symbol

    @property
    def minimum_order_size(self):
        return self.api.minimum_order_size()

    @property
    def current_pos(self):
        return self.ws.my.position.size

    @property
    def current_average(self):
        return self.ws.my.position.average_price

    @property
    def current_profit(self):
        return round(self.ws.my.position.realized+self.ws.my.position.unreal+self.ws.my.position.commission,8)

    @property
    def current_fixed_profit(self):
        return round(self.ws.my.position.realized+self.ws.my.position.commission,8)

    @property
    def current_profit_unreal(self):
        return self.ws.my.position.unreal

    @property
    def commission(self):
        return self.ws.my.position.commission

    @property
    def ltp(self):
        return self.ws.execution.last

    @property
    def best_ask(self):
        return self.ws.execution.best_ask

    @property
    def best_bid(self):
        return self.ws.execution.best_bid



    @property
    def asks(self):
        return self.ws.board.asks

    @property
    def bids(self):
        return self.ws.board.bids

    @property
    def mid_price(self):
        return self.ws.board.mid

    @property
    def server_latency(self):
        return self.ws.execution.avg_latency_1s

    @property
    def ordered_list(self):
        with self.ws.my.lock :
            return self.ws.my.order.list

    @property
    def api_remain1(self):
        return int(self.api.api_remain1) if hasattr(self.api,'api_remain1') else 300

    @property
    def api_remain2(self):
        return int(self.api.api_remain2) if hasattr(self.api,'api_remain2') else 300

    @property
    def api_remain3(self):
        return int(self.api.api_remain3) if hasattr(self.api,'api_remain3') else 300

    @property
    def sfd(self):
        return self.ws.sfd if hasattr(self.ws,'sfd') else 0

    @property
    def executed_history(self):
        return self.ws.my.order.executed_list

    @property
    def canceled_history(self):
        return self.ws.my.order.canceled_list

    def get_historical_counter(self, sec):
        return self.ws.my.order.historical_counter(sec)

    @property
    def log_folder(self):
        return self._strategy_param['logging']['folder']

    def send_discord(self, message, image_file=None):
        return self._logger.discord.send( message=message, image_file=image_file)

    @property
    def no_trade_period(self):
        return self.api.noTrade

    def time(self):
        return time.time()

