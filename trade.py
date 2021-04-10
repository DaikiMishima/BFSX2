# coding: utf-8
#!/usr/bin/python3

import os
import signal
import sys
import time
from threading import Lock
import traceback
import importlib.machinery as imm
from libs.exchanges.base_module import Auth
from libs.plot import *
from libs.utils import *
import libs.version

class Trade(object):

    def __init__(self, args={}):

        self._logger = MyLogger(version_str=libs.version.version_str)

        # ^Cが押されたときのハンドラを登録
        signal.signal(signal.SIGINT, self.quit_loop)

        # パラメータの読み込み
        self.trade_yaml = DynamicParams(self._logger, args.get('trade_yaml','trade.yaml'), callback=self._update_params )
        self.strategy_yaml = DynamicParams(self._logger, args.get('strategy_yaml', self.trade_yaml.params['strategy_yaml']), callback=self._update_params )
        self.log_folder = self.strategy_yaml.params['logging']['folder']
        self._update_params()       # 初回の読み込み
        self.trade_yaml.start()    # 自動更新スタート
        self.strategy_yaml.start() # 自動更新スタート

        # 認証キー
        apikey, secret = self.trade_yaml.params.get('apikey',''), self.trade_yaml.params.get('secret','')
        if apikey=='' or secret=='':
            self._auth = None
        else:
            self._auth = Auth( self._logger, apikey=self.trade_yaml.params['apikey'], secret=self.trade_yaml.params['secret'] )

        # 取引所の選択
        if   self.trade_yaml.params['exchange'] == 'bitFlyer' :
            from libs.exchanges.bitflyer import BitflyerWebsocket as ExchangeWs
            from libs.exchanges.bitflyer import BitflyerAPI as ExchangeAPI
            
        elif self.trade_yaml.params['exchange'] == 'bybit' :
            from libs.exchanges.bybit import BybitWebsocket as ExchangeWs
            from libs.exchanges.bybit import BybitAPI as ExchangeAPI
            
        elif self.trade_yaml.params['exchange'] == 'GMO' :
            from libs.exchanges.gmo import GmoWebsocket as ExchangeWs
            from libs.exchanges.gmo import GmoAPI as ExchangeAPI
            
        elif self.trade_yaml.params['exchange'] == 'phemex' :
            from libs.exchanges.phemex import PhemexWebsocket as ExchangeWs
            from libs.exchanges.phemex import PhemexAPI as ExchangeAPI

        else:
            self._logger.error( "Not Supported yet" )
            return

        # websocket接続
        self.websocket = ExchangeWs(self._logger, subscribe=self.strategy_yaml.params.get('subscribe',{}), symbol=self.trade_yaml.params['symbol'],
                                    auth=self._auth, testnet=self.trade_yaml.params.get('testnet',False))
        self.myposition = self.websocket.my.position

        # rest_api接続
        self.api = ExchangeAPI(self._logger, symbol=self.trade_yaml.params['symbol'], auth=self._auth,
                              testnet=self.trade_yaml.params.get('testnet',False), position=self.websocket.my, timeout=5)

        # グラフプロットのための定期的ステータス収集クラス
        self.stats = Stats(self._logger, exchange=(self.websocket,self.api) )

        # 前回のポジションと損益を再構築
        self.myposition.renew_posfile(self.log_folder + 'position_' + self.trade_yaml.params['exchange'] + '.json')
        self.websocket.my.reload_profitfile(self.log_folder + 'profit_' + self.trade_yaml.params['exchange'] + '.json')
        self.stats.reload_statsfile(self.log_folder + 'stats_' + self.trade_yaml.params['exchange'] + '.json')

        # 動的に MyStrategy を読み込んでクラスを上書きする
        strategy_py_file = args.get('strategy_py', self.trade_yaml.params['strategy_py'])
        strategy_yaml_file = args.get('strategy_yaml', self.trade_yaml.params['strategy_yaml'])
        module_name = strategy_py_file.split('.')[0].replace('/', '.')
        module = imm.SourceFileLoader(module_name, strategy_py_file).load_module()
        self._logger.info( "Load MyStrategy class dynamically: module={}".format(module) )
        strategy_class = getattr(module, 'MyStrategy')
        self._strategy_class = strategy_class( logger=self._logger, exchange=(self.websocket,self.api,self.trade_yaml.params['exchange']))
        self._strategy_class.set_parameters( trade_param=self.trade_yaml.params, strategy_param=self.strategy_yaml.params)
        self._logger.info('Succeeded setup strategy. logic={}, yaml={}'.format(strategy_py_file,strategy_yaml_file))

        matplot_lock = Lock()
        # ポジショングラフのプロットクラス
        self.posgraph = PositionGraph(self._logger, stats=self.stats, strategy=strategy_yaml_file, lock=matplot_lock,
                                      setting = self.strategy_yaml.params.get('plot',{}).get('setting',{}) )
        # 損益グラフのプロットクラス
        self.profgraph = ProfitGraph(self._logger, stats=self.stats, strategy=strategy_yaml_file, lock=matplot_lock)

        # 1時間ごとに現在のパラメータ表示
        Scheduler(self._logger, interval=3600, basetime=1, callback=self._disp_params)

        # ノートレード期間のチェッククラス
        self.notradechecker = NoTradeCheck(self._logger, self.api)

        # websocketの接続待ち
        while not self.websocket.is_connected():
            time.sleep(0.1)

        self._update_params()       # パラメータファイルの再適用

        # ロジックの初期化
        self._strategy_class.initialize()

        # 一定時間ごとのプロット
        self.posplot_timer = Scheduler(self._logger, interval=self.strategy_yaml.params.get('plot',{}).get('pos_interval',60)*60,
                                    callback=self.posgraph.plot, basetime=0,
                                    args=(self.log_folder + 'position_' + self.trade_yaml.params['exchange'] + '.png', self.websocket,))

        # 一時間ごとのプロット
        self.pnlplot_timer = Scheduler(self._logger, interval=self.strategy_yaml.params.get('plot',{}).get('pnl_interval',60)*60,
                                    callback=self.profgraph.plot, basetime=0,
                                    args=(self.log_folder + 'profit_' + self.trade_yaml.params['exchange'] + '.png', self.websocket,))

        # ポジションサーバーとの接続
        self.posclient = PositionClient(self._logger, exchange=(self.websocket,self.api), strategy=strategy_yaml_file,
                                        pos_server=self.trade_yaml.params.get('pos_server',None))

        # ポジずれ補正
        if self.trade_yaml.params.get('adjust_position_with_api',False) :
            self._diff_count = 0
            self._last_pos_diff = 0
            Scheduler(self._logger, interval=30, callback=self.check_position)

        # メインループ
        try:
            discord_bot_token = self.strategy_yaml.params.get('discord_bot_token')
            if discord_bot_token :
                discord_bot_main_loop(self, discord_bot_token)
            else:
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            pass

        self.quit_loop()

    # ^Cが押されたときに行う停止処理
    def quit_loop(self, signal=signal.SIGINT, frame=0):
        self._logger.info( "\n\n\n\n Stop bot because of keyboard interrupt \n\n\n\n\n" )
        self.api.PendingUntil = time.time()+ 3000
        self._logger.stop()
        self.api.stop()
        self.websocket.stop()
        for i in range(10):
            self._logger.info( "Wait {}secs...  Current Pos : {}".format(10-i, round(self.myposition.size,8)) )
            time.sleep(1)
            self.websocket.my.update_profitfile()
            self.stats.add_stats()
        while self.websocket.running :
            self.websocket.stop()
            self._logger.info( "Waiting websocket closed" )
            time.sleep(1)
        self._logger.info( "All process is stopped" )
        os._exit(0)

    # strategy.yaml の 'parameters' 項目だけをリスト表示
    def _disp_params(self):
        self.strategy_yaml.params['parameters']={}
        self.strategy_yaml.load_param()

    # 動的に適用するパラメータの更新
    def _update_params(self):
        self._logger.set_param_fh(log_folder=self.log_folder, console_output=self.trade_yaml.params['console_output'],
                                  console_log_level=self.trade_yaml.params.get('console_log_level','INFO'),
                                  file_log_level=self.strategy_yaml.params['logging'].get('level','INFO'))

        self._logger.discord.webhook = self.strategy_yaml.params.get('discord',{}).get('webhook','')

        if hasattr(self,'posgraph') :
            self.posgraph.setting = self.strategy_yaml.params.get('plot',{}).get('setting',{})

        if hasattr(self,'posplot_timer') :
            self.posplot_timer.interval = self.strategy_yaml.params.get('plot',{}).get('pos_interval',self.posplot_timer.interval/60)*60

        if hasattr(self,'pnlplot_timer') :
            self.pnlplot_timer.interval = self.strategy_yaml.params.get('plot',{}).get('pnl_interval',self.pnlplot_timer.interval/60)*60

        if hasattr(self,'_strategy_class') :
            self._strategy_class.set_parameters( trade_param=self.trade_yaml.params, strategy_param=self.strategy_yaml.params)

        if hasattr(self,'myposition') :
            self.myposition.base_position = self.trade_yaml.params.get('base_position',0.0)

        if hasattr(self,'notradechecker') :
            self.notradechecker.notrade = self.strategy_yaml.params.get('no_trade')

        if hasattr(self,'api') :
            self.api.close_while_noTrade = self.strategy_yaml.params.get('close_while_noTrade',False)


    # 定期的に APIから建玉一覧を取得してポジずれをチェック
    def check_position(self):

        pos = self.api.getpositions()
        long = 0
        short = 0
        for i in pos:
            self._logger.debug( "OpenPosition : {}".format(i) )
            if i['side'].upper()=='BUY' :
                long += float(i['size'])
            else :
                short += float(i['size'])
        current = self.websocket.my.position.size

        # 同じずれが繰り返すとカウントアップ
        actual = round(long-short,8)
        pos_diff = round(actual-current-self.trade_yaml.params.get('base_position',0), 8)
        if self._last_pos_diff != pos_diff or abs(pos_diff)<self.api.minimum_order_size() :
            self._diff_count = 0
        if abs(pos_diff)>=self.api.minimum_order_size() :
            self._diff_count += 1
        self._last_pos_diff = pos_diff

        self._logger.info( "Long : {}  / Short : {}  = Total :{} / est:{}.   Diff:{} {}".format(
                           long, short, round(long-short,8), round(current,8), round(long-short-current,8), '*'*self._diff_count) )

        # 4度続けてポジションがズレていれば成売買で補正行う
        if self.api._auth!=None and self.trade_yaml.params.get('adjust_position_with_api',True) and self._diff_count>=4 :
            maxsize = self.trade_yaml.params.get('adjust_max_size',100)
            if pos_diff < 0:
                size = min(-pos_diff,maxsize)
                self._logger.info( "Adjust position with 'MARKET BUY' : size:{}".format(size) )
                self.api.sendorder(order_type='MARKET', side='BUY', size=size, adjust_flag=True)
            else:
                size = min(pos_diff,maxsize)
                self._logger.info( "Adjust position with 'MARKET SELL' : size:{}".format(size) )
                self.api.sendorder(order_type='MARKET', side='SELL', size=size, adjust_flag=True)
            self.api.PendingUntil = time.time()+30
            self._diff_count = 0

# Discordライブラリの初期化（もしインストールされていれば）
try:
    import discord
    discord_client = discord.Client()
except:
    discord_client = None

try:
    @discord_client.event
    async def on_ready():
        try:
            discord_client.broker._logger.info('Logged to Discord in as {}'.format(discord_client.user.name))
        except Exception as e:
            discord_client.broker._logger.exception("Error in on_ready routine : {}, {}".format(e, traceback.print_exc()))
except:
    pass

# メッセージとリアクションのハンドラ
try:
    @discord_client.event
    async def on_message(message):
        try:
            # 自分自身の書き込みには反応させない
            if message.author == discord_client.user:
                return
            if hasattr(discord_client.broker._strategy_class,'discord_on_message') :
                await discord_client.broker._strategy_class.discord_on_message(message)
        except Exception as e:
            discord_client.broker._logger.exception("Error in on_message routine : {}, {}".format(e, traceback.print_exc()))

    @discord_client.event
    async def on_reaction_add(reaction, user):
        try:
            # 自分自身の書き込みには反応させない
            if user == discord_client.user:
                return
            if hasattr(discord_client.broker._strategy_class,'discord_on_reaction_add') :
                await discord_client.broker._strategy_class.discord_on_reaction_add(reaction, user)
        except Exception as e:
            discord_client.broker._logger.exception("Error in on_reaction_add routine : {}, {}".format(e, traceback.print_exc()))
except:
    pass

def discord_bot_main_loop(broker, discord_bot_token):
    try:

        if discord_client != None:
            discord_client.broker = broker
            discord_client.broker._logger.info('Start Discord bot')
            discord_client.loop.run_until_complete(discord_client.start(discord_bot_token))
        else:
            broker._logger.error('Discord bot is not active.')
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":

    # python trade.py
    if len(sys.argv) == 1:
        args={}

    # python trade.py trade.yaml
    elif len(sys.argv) == 2:
        args={'trade_yaml': sys.argv[1]}

    # python trade.py strategy/strategy.py strategy/strategy.yaml
    elif len(sys.argv) == 3:
        args={'strategy_py': sys.argv[1], 'strategy_yaml': sys.argv[2], }

    # python trade.py trade.yaml strategy/strategy.py strategy/strategy.yaml
    elif len(sys.argv) == 4:
        args={'trade_yaml': sys.argv[1], 'strategy_py': sys.argv[2], 'strategy_yaml': sys.argv[3], }

    broker = Trade(args)
