# 【BFSX2】複数取引所に対応した高速botフレームワーク


---
## １．環境構築と起動方法
---

基本的に**環境構築や起動方法はサポート対象外**ですが、簡単な説明だけをこちらに記載しておきます。  
こちらの説明を読んで理解いただける方を販売対象とさせていただきます。

<br>
<br>
<br>
<br>
<br>
<br>
<br>

---

### ■ フォルダ構成
配布されているファイルはフォルダ構成のまま圧縮されていますので、そのままのフォルダ構成でファイルを展開して用意してください。  
Pythonが稼働できる環境であれば、様々な環境で使用することが可能ですが、一例としてAWSでのフォルダ構成例はこちらです。  
何らかのサブフォルダを作ってからその中に展開していただいても結構です。

<img src="img/sec1-1.png" width="50%">

<br>
<br>
<br>
<br>
<br>



<div style="page-break-before:always"></div>

---
### ■ 構成ファイル
#### ●　```trade.py```
BFSX2の本体プログラムです。  
**このファイルがある場所をカレントフォルダにして起動**してください。


#### ●　```trade.yaml```
BFSX2の稼働パラメータです。詳細は6章を参照してください。  
trade.pyと同じフォルダに配置します。


#### ●　```libs```フォルダ
BFSX2を動かすためのライブラリが入っているフォルダです。


#### ●　```strategy```フォルダ
サンプルロジック（とそのパラメータファイル）が入っています。



---
> [Tips]  
 strategyフォルダにはたくさんのサンプルロジックが入っています。ご自身のロジックや、サンプルロジックの内で稼働させるロジックを別フォルダ(下図の例だと MyLogicフォルダ) に入れておくと分かりやすいでしょう。


<img src="img/sec1-2.png" width="50%">

<br>
<br>
<br>
<br>
<br>
<div style="page-break-before:always"></div>



---



### ■ 必要なパッケージのインストール
BFSX2では下記のパッケージを必要とします。
```
websocket-client
python-dateutil
pandas==0.24.2
pyyaml
matplotlib
requests
sortedcontainers
discord
influxdb
```

pipコマンドなどを用いてパッケージのインストールを行ってください。
当方で動作確認したawsの環境では下記のコマンドでインストールを行いました。各々の環境で異なる可能性はありますので、必要に応じて調べてみてください。

```
sudo pip3 install websocket-client python-dateutil pandas pyyaml matplotlib requests sortedcontainers 
```
実行例
<img src="img/sec1-3.png">


そのほか、指数の計算などのためにTA-Libなどもインストールされると良いかと思います。


<div style="page-break-before:always"></div>


---



### ■ 今後のバージョンアップ方法
新しいバージョンへのバージョンアップは基本的に **ルートフォルダにあるpythonファイル(```trade.py```)と、 ```libs```フォルダを上書きしていただけば更新いただけます**。  
ご自身のロジックを**別フォルダ**に入れられている場合には、```strategy```フォルダも上書きしても問題ありません。  
ただし、**trade.yamlファイルは設定したAPIキーなどが上書きされてしまうので上書きしていはいけません**。  
後述する起動方法でtrade.yaml以外のファイル名を使って起動させることもできるので、別のファイル名にして運用しておけば全て上書きしてバージョンアップすることもできるでしょう。



<br>
<br>
<br>
<br>

---

### ■ 起動方法

#### ●　【方法１】もっともシンプルな起動方法
```trade.py```があるフォルダをカレントフォルダにして```trade.py```をPython3で実行します。

実行コマンド
```
python3 trade.py
```
起動されると```trade.py```と同じフォルダにある```trade.yaml```がパラメータファイルとして読み込まれ、その中の```strategy_py:```で設定されたロジックファイルと```strategy_yaml:```で指定されたロジックパラメータファイルが読み込まれbotがスタートします。

取引所のapiとシークレットキーを```apikey:```と```secret:```に記載しておけば取引が開始されます。



<br>
<br>
<br>





#### ●　【方法２】稼働パラメータを指定しての起動方法 (引数1つ指定しての起動)
複数の稼働パラメータを使い分けたい場合や、デフォルトの```trade.yaml```という名前以外の稼働パラメータを使いたい場合(バージョンアップ時にそのまま上書きすると```trade.yaml```ファイルは上書きされてしまうため、それを避けたい場合など)には起動時にパラメータファイルを指定して起動させることも可能です。

実行コマンド例
```
python3 trade.py mytrade.yaml
```
起動されると```trade.py```と同じフォルダにある```mytrade.yaml```がパラメータファイルとして読み込まれ、その中の```strategy_py:```で設定されたロジックファイルと```strategy_yaml:```で指定されたロジックパラメータファイルが読み込まれbotがスタートします。  
また、下記のようにサブフォルダ内にパラメータを入れておいて起動させることも可能です。


稼働パラメータをサブフォルダに入れておく実行コマンド例
```
python3 trade.py myparams/mytrade.yaml
```
<br>
<br>
<br>

#### ●　【方法３】ロジックファイル・ロジックパラメータファイルを指定しての起動方法 (引数2つ指定しての起動)
ロジックファイルを稼働パラメータファイル(```mytrade.yaml```)内に記載しておくのではなく、コマンドライン引数として指定することも可能です。  
ロジックファイル(.py)とロジックパラメータファイル(.yaml)をカレントフォルダからの相対パス指定で引数として与えます。

実行コマンド例
```
python3 trade.py mylogic/oreno_logic.py mylogic/oreno_logic.yaml
```
起動されると```mylogic/oreno_logic.py```がロジックファイル、```mylogic/oreno_logic.yaml```がロジックパラメータファイルが読み込まれbotがスタートします。  

---
> [Tips]  
 複数のターミナルを開いて、それぞれ異なるロジックファイルを指定して起動せることで同一口座で複数のロジックを平行させて稼働させることが可能です。

稼働例

<img src="img/sec1-4.png">
<br>
<br>
<br>

---

#### ●　【方法４】稼働パラメータ・ロジックファイル・ロジックパラメータファイルを指定しての起動方法 (引数３つ指定しての起動)
稼働パラメータ・ロジックファイル(.py)・ロジックパラメータファイル(.yaml)の全てをコマンドラインから指定して起動することも可能です。

例えば　```trade_fx.yaml```にFX_BTC_JPY用の稼働ファイルを用意して、```trade_spot.yaml```に現物のBTC_JPY用の稼働ファイルを用意しておいて、下記のように両方の取引板で稼働させる事も可能です。

実行コマンド例
```
【bot1:FX】
python3 trade.py trade_fx.yaml mylogic/logic1.py mylogic/logic1.yaml

【bot2:現物】
python3 trade.py trade_spot.yaml mylogic/logic2.py mylogic/logic2.yaml
```
<br>
<br>
<br>
<div style="page-break-before:always"></div>

---
### ■ 停止・再稼働

BFSX2では停止する際に ```Ctrl+C``` キーを押して中断すれば、現在の未約定発注のキャンセルを行って、現在のポジションをファイルに書き出し保存します。  
この情報をもとに、再起動時には中断時のポジション情報から継続して稼働することが出来ます。

<br>
<br>

> [Tips1]  
 BFSX2では定期的に現在ポジをファイルに残しておいて、停止後再稼働した際に、持っていたポジ情報を復元して継続稼働することができます。  
 停止後ポジションを手動でクリアするなどしてポジションゼロから再スタートしたい場合には、ログフォルダ内のposition_xxxx.jsonを削除して再稼働させるとポジション情報を無しにして再稼働させることができます。

> [Tips2]  
 BFSX2では損益情報も定期的にファイルに保存しており、停止後再稼働した際にも当日の損益情報は引き続きグラフ化されます。損益情報をクリアしてゼロから再スタートしたい場合には、ログフォルダ内のprofit_xxxxx.jsonを削除して再稼働させればOKです。


<div style="page-break-before:always"></div>


---
## ２．ロジック部の構成（フレームワークを用いたロジックの記載方法）
---

BFSX2では、ユーザーがご自身のロジックを簡単なコードで記述することで容易にbotとして稼働させることが出来ます。  
同梱されているサンプルロジックなども参考にしてロジック部の構成を理解して、サンプルロジックを改良したり、ご自身のロジックを記載したりしてみてください。  
<br>
<br>
<br>

---
### ■ プログラムファイルとパラメータファイル 
ロジックは(1)プログラムファイルと(2)パラメータファイルのセットで構成されます。  
プログラムファイル(.py)には、Pythonで記述された実際のロジックコードを記載します。  
パラメータファイル(.yaml)にはbotやロジックの動作に関するパラメータファイルをyamlという記載方法を用いて記載します。BFSX2の大きな特徴として、パラメータファイルはbot稼働時でも変更することが出来、変更すると自動的に読み込まれます。
<br>
<br>
<br>

---
### ■ クラスの形と、その中で用意する関数
ロジックは**MyStrategy**というClassとして記述します。
このClassに必要な関数を用意してその中にロジックの中身を記載します。
各々の関数は決められたタイミングで呼び出されますので、その中で必要な処理を行ってその関数を終えるスタイルでロジックを記述します（イベントドリブンと呼ばれるプログラミングスタイル）  
多くのサンプルロジックが **strategy** フォルダに用意されていますので参考にしてみてください。  

BFSX2では用意されたモジュールを使う事で約定履歴の受信タイミングで取引するモード（mmbotモード）や、自炊ローソクをもとに取引するモード（秒スキャモード）やAPIから取得するローソク足をもとに取引するモード（スイングモード）などが使用できます。

まずは、**initialize関数**を用意してその中で必要な初期化作業を行います。この **initialize関数**は初回に１回だけ呼び出されます。
<br>
<br>
<br>
<div style="page-break-before:always"></div>

---
### ■ ロジックの動作を決める主要な関数
BFSX2では **initialize関数の中でどのように初期化を行うか** によって様々な動作を行うことができます。こちらでは実際の記述例を挙げて主要な関数を説明します。
<br>
<br>

### **self.CandleGenerator 関数**
この関数は自炊ローソク足を作るクラスを起動してローソク足が更新されたら指定された関数を呼び出すように設定することができます。この関数を使うことで、簡単に **「秒スキャモード」** のロジックを記述することができます。

```python
# -*- coding: utf-8 -*-
from libs.base_strategy import Strategy

class MyStrategy(Strategy):
    """
    確定足だけを表示するサンプルロジック
    """
    def initialize(self):
        # 10秒足を自炊してローソク足が更新されたら logic関数を呼び出すよう設定します
        self.candlegen = self.CandleGenerator(timescale=10,
                                              num_of_candle=100,
                                              callback=self.logic)

    def logic(self):
        # 未確定足もローソク足に含まれているので最後の１本を削除
        self._logger.info( self.candlegen.candle[:-1] )
```

このロジック例では、10秒足ローソクを作って、10秒足が更新されたタイミングでself.logic関数が呼び出されます。

ローソク足データは **pandas形式** でself.candlegen.candleに格納されています。得られるデータのうち最後のローソク足は未確定足ですので、[:-1]とつけてスライスを使って「先頭から最後の一つ前まで」を取得することで最後の１本を除いています。  

その得られたデータを self._logger.info関数を使って表示しています。
このサンプルでは延々と生成されるローソク足を表示し続けます。（取引はしません）

生成される最大本数は num_of_candle で指定した100本（プラス未確定の１本）です

同梱サンプルの dp_candle1.py が実際のコードです。
<br>
<br>
<br>
<div style="page-break-before:always"></div>

### **self.Scheduler 関数**
この関数は callback で指定された関数を一定間隔で呼び出すよう登録します。  
例えば定期的なポジション情報表示やロスカット判断などに使えます。  
(従来のBFS-Xにおける loss_cut_check()関数の変わりに使えます)


```python
# -*- coding: utf-8 -*-
from libs.base_strategy import Strategy

class MyStrategy(Strategy):
    """
    未確定足も含めて loop_period間隔で表示するサンプルロジック
    """

    def initialize(self):
        # 10秒足を自炊してローソク足を生成します、未確定足も都度更新します
        self.candlegen = self.CandleGenerator(timescale=10
                                              num_of_candle=500,
                                              update_current=True)

        # 2秒間隔で callback で指定した logic関数が呼び出されるように設定します
        self.Scheduler(interval=2, callback=self.logic)

    def logic(self):
        # 未確定足も表示
        self._logger.info( self.candlegen.candle )
```
この記述例は2秒ごとに未確定足も含めたローソク足を表示し続ける例です。  
self.CandleGenerator では callbackを指定していないので、10秒足のローソク足更新時にはなにも呼び出されませんが、self.Scheduler 関数で指定した 2秒間隔で callback に指定した logic関数が呼び出されます。  
また、update_current=True と指定しているため、約定履歴受信の際に未確定足も都度更新されます。  

同梱サンプルの dp_candle2.py が実際のコードです。  

self.Scheduler関数を使ってローソク足確定タイミング以外のタイミングで未確定足も参照することで、エントリー判断は確定足で行いたいが未確定足の取引ボリューム（売りと買いの）差などを見て急変前にクローズしたいようなときに未確定足も含めたローソク足を使ったりすることができます。


> [Tips]  
```python
self.Scheduler(interval=60, basetime=0, callback=self.logic)
```
のように basetime引数を指定すると毎回指定したジャストの時間に呼び出すことも可能です。
```
interval=60, basetime=0 とすると、毎分00秒
interval=60, basetime=5 とすると、毎分05秒
interval=3600, basetime=0 とすると、毎時00分
interval=3600, basetime=300 とすると、毎時05分
```
のように指定します。basetimeを指定しない場合には self.Scheduler 関数を呼び出したときを基準として指定間隔で呼び出しされます。（例 interval=3600で 時刻が09:34:10に関数呼び出しをしたら、以後 10:34:10 / 11:34:10 / 12:34:10 ....という時刻に呼び出されます）
<br>
<br>
<br>
> [Tips]  
```python
schedule = self.Scheduler(interval=60, callback=self.logic)
```
のように戻り値(Scheduleクラス)を保存しておくと、
```
schedule.interval = 10
```
のようにインターバルを変更することが可能です
<br>
<br>
<br>




### **self.ExecutionQueue 関数**
この関数は約定データを受信して動作する **mmbotモードのbotを作るとき** に使います。  
呼び出すと約定データを格納するキューを作成して、約定データがため込まれるように登録します。  
約定データが届くと callback で指定した関数が呼び出されますので、ため込まれている約定データはpopコマンドで順に取り出して処理します。  


```python
# -*- coding: utf-8 -*-
from libs.base_strategy import Strategy

class MyStrategy(Strategy):

    def initialize(self):
        # 約定データを受信したら格納される deque を作成し、約定データを受信した際に
        # callback で指定した関数が呼び出されるように設定
        self.exec_list = self.ExecutionQueue( callback=self.executions )

    def executions(self):
        # self.exec_listデータが残っている限り順次処理する
        while len(self.exec_list)!=0:

            # self.exec_list に入っている約定データを一つ取り出す
            e = self.exec_list.popleft()
            """
            この部分でe['price'] や e['side']、e['size'] などに格納されて
            いるデータをもとに処理を行う
            """
            self._logger.info( i )   # 受信した約定履歴を表示
```

この記述例では、約定データを受信してそれをすべて表示します。  
実際のロジックの例は同梱サンプルの mm_spread.py などをサンプルロジックを参考にしてみてください。

以前のBFS-Xでは executions 関数の中では売買判断だけを行って迅速に終了し、イベントを設定することで呼び出される realtime_logic 関数内で実際の売買を行うスタイルでしたが、BFSX2では約定履歴は別スレッドでキューに格納されるので、executions 関数の中で実際の売買まで行っても問題ありません。
<br>
<br>
<br>
<div style="page-break-before:always"></div>

### **self.AddBoardUpdateHandler 関数**
この関数は板の更新情報を受信して動作する mmbotモードのbotを作るときに使います。  
呼び出すと板の更新情報が届くと callback で指定した関数が呼び出されますので、self.asksおよびself.bidsから板情報を取得します。


```python
# -*- coding: utf-8 -*-
from libs.base_strategy import Strategy

class MyStrategy(Strategy):

    def initialize(self):
        # 板情報が更新されたら callbackで指定したboard_update関数を呼び出す
        self.AddBoardUpdateHandler( callback=self.board_update )

    def board_update(self):
        # self.asks/self.bids に入っている板データ(上下5個)を表示
        self._logger.info( '-'*50 )
        for i in self.asks[5::-1] :
            self._logger.info( i )
        self._logger.info( "-----mid : {}".format(self.mid_price) )
        for i in self.bids[:5] :
            self._logger.info( i )
```

この記述例では、更新データを受信するたびに板情報を表示させます。
実行例はこのようになります。  
(同梱サンプルの dp_board1.py が実際のコードです。)  
<img src="img/sec2-1.png" width="50%">


> [Hint]  
板情報を取得するには第４章で説明するロジックの設定ファイルに下記の設定を行う必要があります。（負荷低減のためデフォルトでは False になっており板情報の読み込みは行われません）
```
subscribe:
  board: True  
```

なお板情報が更新されたときに表示するのではなく、一定期間（例えば2秒ごと）に表示させるためのコードはこちらです。  

```python
# -*- coding: utf-8 -*-
from libs.base_strategy import Strategy

class MyStrategy(Strategy):
    """
    2秒間隔で板情報を表示し続けるサンプルロジック
    """
    def initialize(self):
        # 2秒間隔で callback で指定した logic関数が呼び出されるように設定
        self.Scheduler(interval=2, callback=self.logic)

    def logic(self):
        # self.asks/self.bids に入っている板データ(上下5個)を表示
        self._logger.info( '-'*50 )
        for i in self.asks[5::-1] :
            self._logger.info( i )
        self._logger.info( "-----mid : {}".format(self.mid_price) )
        for i in self.bids[:5] :
            self._logger.info( i )
```
板情報が更新されたときに呼び出される関数の登録は必要ないので **self.AddBoardUpdateHandler関数** は実行する必要はありません。  
ロジックの設定ファイルで
```
subscribe:
  board: True  
```
の指定をすることで板情報の受信は自動で行われていますので常に self.asks / self.bids へアクセスることでその時点での最新の板情報を読み取ることができます。  
（同梱のサンプルコードは dp_board2.py です）
<br>
<br>
<br>
<div style="page-break-before:always"></div>

### **self.AddExecutionHandler 関数**
この関数は自分の約定を検知して callback で指定した関数を呼び出すように設定します。
約定したデータは self.executed_history などで確認することができます。

```python
# -*- coding: utf-8 -*-
from libs.base_strategy import Strategy

class MyStrategy(Strategy):

    def initialize(self):

        self.AddExecutionHandler(callback=self.exec_call)

    def exec_call(self):
        self._logger.info("Execution!!!!!!!")
        self._logger.info(self.executed_history)
```

> [Hint]  
self.executed_historyを参照する場合、self.executed_historyには部分約定は含まれませんので部分約定の処理は別途検討してください。

<br>
<br>
<br>
<div style="page-break-before:always"></div>

---
### ■ 複数の取引所サポート例
BFSX2では様々な取引所をサポートしている（今後していく）事も特徴の一つで、 trade.yaml で指定した売買を行う取引所とは別の取引所を参照して動作することができます。

こちらの例では bybitの自炊ローソクを作ってbitFlyer(trade.yamlで指定した取引所)で取引する例です。

```python
# -*- coding: utf-8 -*-
from libs.base_strategy import Strategy

class MyStrategy(Strategy):

    def initialize(self):
        # bybitのwebsocketを受信するクラスを作成
        from libs.exchanges.bybit import BybitWebsocket
        self.bybitws = BybitWebsocket(self._logger, subscribe={'execution': True})

        # 引数wsに作成したwebsocket受信クラスを指定して自炊してローソク足を生成する
        self.candlegen = self.CandleGenerator(timescale=10,
                       num_of_candle=500, callback=self.logic, ws=self.bybitws)

    def logic(self):
        """
        self.candlegen.candle にbybitの10秒ローソク足が入っているので
        それをもとにここで(bitFlyerで)取引を行う
        """
```

> [Hint]  
**self.CandleGenerator関数**と同様に **self.ExecutionQueue関数** や **self.AddBoardUpdateHandler関数** にも引数(ws=)を与えて実行することで、他の取引所の約定履歴に沿って取引したりほかの取引所の板情報更新タイミングで取引を行うことも可能です。

<br>
<br>

現時点でwebsocketの取得に対応しているのは現時点で下記のとおりです。
```
from libs.exchanges.binance import BinanceWebsocket
from libs.exchanges.binance_spot import BinanceSpotWebsocket
from libs.exchanges.bitflyer import BitflyerWebsocket
from libs.exchanges.bitflyer_spot import BitflyerSpotWebsocket
from libs.exchanges.bitmex import BitmexWebsocket
from libs.exchanges.btcmex import BtcmexWebsocket
from libs.exchanges.bybit import BybitWebsocket
from libs.exchanges.bybit_testnet import BybitTestWebsocket
from libs.exchanges.coinbase import CoinbaseWebsocket
from libs.exchanges.deribit import DeribitWebsocket
from libs.exchanges.ftx import FtxWebsocket
from libs.exchanges.gmo import GmoWebsocket
from libs.exchanges.huobi import HuobiWebsocket
from libs.exchanges.kraken import KrakenWebsocket
from libs.exchanges.okex import OkexWebsocket
```

たとえばこのコードのように多くの取引所と接続してすべての情報を取得することも可能です。  
BFSX2で用意されている **get_size_group()関数** を使うことで簡単に板をグルーピングすることもできます。
下記の例ではパラメータ['size']で指定したサイズごとの板の価格を表示するサンプルです。  
(同梱サンプル dp_board_size.py)
```python
# -*- coding: utf-8 -*-
from libs.base_strategy import Strategy

class MyStrategy(Strategy):
    """
    2秒間隔で板情報を表示し続けるサンプルロジック
    """
    def initialize(self):
        self._exchanges = []

        from libs.exchanges.binance import BinanceWebsocket
        self._exchanges.append( BinanceWebsocket(self._logger,
                                subscribe={'execution': False, 'board': True}) )
        from libs.exchanges.bitflyer import BitflyerWebsocket
        self._exchanges.append( BitflyerWebsocket(self._logger,
                                subscribe={'execution': False, 'board': True}) )
        from libs.exchanges.bitmex import BitmexWebsocket
        self._exchanges.append( BitmexWebsocket(self._logger,
                                subscribe={'execution': False, 'board': True}) )
        from libs.exchanges.bybit import BybitWebsocket
        self._exchanges.append( BybitWebsocket(self._logger,
                                subscribe={'execution': False, 'board': True}) )
        from libs.exchanges.ftx import FtxWebsocket
        self._exchanges.append( FtxWebsocket(self._logger,
                                subscribe={'execution': False, 'board': True}) )
        from libs.exchanges.okex import OkexWebsocket
        self._exchanges.append( OkexWebsocket(self._logger,
                                subscribe={'execution': False, 'board': True}) )
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
        boards = [(e.board.get_size_group(splitsize= size , limitnum=rows),
                   e.board.mid) for e in self._exchanges]

        for i in reversed(range(rows)):
            s = ''
            for b in boards:
                s += "  {:>10.2f} ({:>+7.1f})  |".format(
                    (b[0]['ask']+[0]*rows)[i],(b[0]['ask']+[0]*rows)[i]-b[1])
            self._logger.info( s )
        s = ''
        for b in boards:
            s += "===   mid {:>10.2f} ===+".format(b[1])
        self._logger.info( s )
        for i in range(rows):
            s = ''
            for b in boards:
                s += "  {:>10.2f} ({:>+7.1f})  |".format(
                    (b[0]['bid']+[0]*rows)[i],(b[0]['bid']+[0]*rows)[i]-b[1])
            self._logger.info( s )

        self._logger.info( s )
        self._logger.info('')

```
<br>
1 btc ごとの価格にまとめた実際の実行例はこのようになります。
<br>
<br>

<img src="img/sec2-2.png">
<br>
<br>
<div style="page-break-before:always"></div>

BFSX2には価格ごとに板をグルーピングする関数 **get_price_group()** も用意されているので、簡単に価格ごとの板の厚みも確認することができます。
同梱サンプルの dp_board_price.py では指定した価格ごとに板情報をまとめて表示するサンプルも用意されていて、実際の実行例はこのようになります。
<br>

<img src="img/sec2-3.png">
<br>
<br>

---
### ■ 従来のBFS-Xでのロジックを移植する場合

従来の「秒スキャモード」と似たような動きをする構成はこちらです。  
同梱サンプルの st_mfi.py なども以前のBFS-X同梱の st_mfi.py と比較するなどして参考にしてみてください。

```python
# -*- coding: utf-8 -*-
from libs.base_strategy import Strategy

class MyStrategy(Strategy):

    def initialize(self):
        # 自炊ローソク足を作るクラスを起動、ローソク足が更新されたら
        # callbackで指定したlogic関数が呼び出す
        self.candlegen = self.CandleGenerator(callback=self.logic,
                 timescale=self.parameters['timescale'],
                 num_of_candle=self.parameters['num_of_candle'])

        # loop_period間隔で callback で指定したloss_cut_check関数が呼び出されるように設定
        self.Scheduler(callback=self.loss_cut_check,
                 interval=self.parameters['loop_period'])

    def logic(self):
        # 未確定足もローソク足に含まれているので最後の１本を削除
        self._logger.info( self.candlegen.candle[:-1] )

        # ここで取引を行う

    def loss_cut_check(self):
        self._logger.info( "loss_cut_check" )

        # ここで定期的な処理を行う
```
<br>
<br>
<br>

従来の「mmbotモード」と似たような動きをする構成はこちらです。  
（下記の例では従来のBFS-Xとの対比でロジックを記載したため executions関数と realtime_logic関数を用意しましたが、BFSX2では約定データ処理部と売買部を分ける必要がなくなったので、下記のような executions関数と realtime_logic関数に分ける必要もありません。）  
同梱サンプルの mm_spread.py なども以前のBFS-X同梱の mm_spread.py と比較するなどして参考にしてみてください。
```python
# -*- coding: utf-8 -*-
from libs.base_strategy import Strategy

class MyStrategy(Strategy):

    def initialize(self):
        # 約定データを受信したら格納される deque を作成し、約定データを受信した際に
        # callback で指定した関数が呼び出されるように設定
        self.exec_list = self.ExecutionQueue( callback=self.executions )

        # loop_period間隔で callback で指定したloss_cut_check関数が呼び出されるように設定
        self.Scheduler(callback=self.loss_cut_check,
                 interval=self.parameters['loop_period'])

    def executions(self):
        # self.exec_list に入っている約定データを取り出して処理する
        while len(self.exec_list)!=0:
            i = self.exec_list.popleft()

            # ここで売買判定を行う
            # BFS-Xでの売買イベントセット( self.order_signal_event.set() )の代わりに
            # 直接 self.realtime_logic を実行する
            if 売買する場合 :
                self.realtime_logic()

    def realtime_logic(self):
        # ここで売買を行う


    def loss_cut_check(self):
        self._logger.info( "loss_cut_check" )

        # ここで定期的な処理を行う
```


<div style="page-break-before:always"></div>



---
## ３．オーダーの行い方（取引所ごとの違い）
---

BFSX2では、異なる取引所でも同じコマンドでオーダーが行うことができ、取引所ごとの異なるオプションをサポートしています。

ここでは発注関数の self.sendorder関数でのオプションの指定方法を説明します。
<br>
<br>
<br>

---
### ■ self.sendorder関数 

<br>

#### **●　基本的な発注関数の使い方は下記のとおりです**

　self.sendorder(order_type, side, size, price)
> 注文を発行します。  

|入力|型|説明|
|---|---|---|
|order_type|string|注文の執行条件(LIMIT/MARKET)|
|side|string|売買方向。買い注文の場合は "BUY", 売り注文の場合は "SELL" を指定します。すべて大文字で指定してください。|
|size|float|売買数量|
|price|float|執行条件がLIMITの場合の指値価格(MARKETの場合には省略可能)|
|auto_cancel_after|float|指定すると、指定秒数経過後にBFSX2内部で自動的にキャンセルが実行されます。省略した場合のデフォルトは2592000(30 日間) です。なお order_type が"MARKET" の場合にはこのパラメータは意味がありません。|

|出力|型|説明|
|---|---|---|
|res|dict| 'stat': ステータスコード（0が正常終了）'msg':  エラーメッセージ　'ids' :  オーダーIDリスト|
コード例
```python
self.sendorder(order_type="LIMIT", side="BUY", size=0.01, price=3854000, auto_cancel_after=5)
```

<br>

実行例(正常オーダー時)
```python
{'stat':0 , 'msg':'', 'ids':['JRF20191211-001824-668915']}

{'stat':0 , 'msg':'', 'ids':['7b9055dc-5cde-425f-8bf9-13b9021d0c24']}

{'stat':0 , 'msg':'', 'ids':['1254842748', '1254842749', '1254842750', '1254842751']}
```
実行例(エラー時　(例))
```python
{'stat':-106 , 'msg':'The price is too low.', 'ids':[]}
```
```python
{'stat':-205 , 'msg':'Margin amount is insufficient for this order.', 'ids':[]}
```

<br>

> BFSX2では本体側でのオーダーリトライを行っていません。戻り値のステータスコードやIDを見て必要ならリトライするようにロジック側で処理してください。

> [Hint!]  
GMOなどのオーダー時ではオーダーをポジション数に応じて自動的に決済指値に振り分けるため、複数のオーダーIDが割り当てられることがあります。

<br>


#### **●　使用可能なオプション**
取引所によっては発注オプションを指定することができます。

<br>
<br>

**bitFlyerで使用可能なオプション**
|入力|型|説明|
|---|---|---|
|minute_to_expire|int|期限切れまでの時間を分で指定します。省略した場合の値は 43200 (30 日間) です。|
|time_in_force|str|執行数量条件 を "GTC", "IOC", "FOK" のいずれかで指定します。省略した場合の値は "GTC" です。|

<br>
<br>

**bybitで使用可能なオプション**
|入力|型|説明|
|---|---|---|
|time_in_force|str|執行数量条件 を "GoodTillCancel", "ImmediateOrCancel", "FillOrKill", "PostOnly" のいずれかで指定します。省略した場合の値は "GoodTillCancel" です。|
|reduce_only|bool|True/False で指定します。Trueの場合には現在のポジションを減らすオーダー以外は無効となります。|

<br>
<br>

**Phemexで使用可能なオプション**
|入力|型|説明|
|---|---|---|
|timeInForce|str|執行数量条件 を "GoodTillCancel", "ImmediateOrCancel", "FillOrKill", "PostOnly" のいずれかで指定します。省略した場合の値は "GoodTillCancel" です。|
|reduceOnly|bool|True/False で指定します。Trueの場合には現在のポジションを減らすオーダー以外は無効となります。|

<br>
<br>

**GMOで使用可能なオプション**
|入力|型|説明|
|---|---|---|
|timeInForce|str|執行数量条件 を FAK (MARKETの場合のみ設定可能) FAS FOK((Post-onlyの場合はSOK) LIMITの場合のみ設定可能) のいずれかで指定します。省略した場合は成行はFAK、指値はFASで注文されます。|

<br>
<br>
<br>

#### **●　オプションは下記のいずれかの方法または両方で指定可能です**  
<br>

**self.sendorder関数実行時に指定**

例)

```python
self.sendorder(order_type="LIMIT", side="BUY", size=100, price=46500, time_in_force="PostOnly")

self.sendorder(order_type="LIMIT", side="SELL", size=100, price=50500, reduce_only=True)

self.sendorder(order_type="LIMIT", side="BUY", size=0.01, price=3854000)
, minute_to_expire=1)
```

<br>


**ロジックの設定ファイルで指定**  
ロジックの設定ファイル内に下記のように記載することでデフォルトのオプションとして指定することもできます。

例)

```python
order:
  option : {"minute_to_expire": 1, "auto_cancel_after" : 30}
  
  ```

例)

```python
order:
  option : {"time_in_force":"PostOnly", "reduce_only": True}
  
  ```

<br>
<br>

<div style="page-break-before:always"></div>


---
## ４．他取引所 websocket クラスの使い方
---

２章のサンプルで記載した通り、BFSX2では他取引所のwebsocketを受信するクラスが用意されています。

現時点でwebsocketの取得に対応しているのは現時点で下記のとおりです。
```
from libs.exchanges.binance import BinanceWebsocket
from libs.exchanges.binance_spot import BinanceSpotWebsocket
from libs.exchanges.bitflyer import BitflyerWebsocket
from libs.exchanges.bitflyer_spot import BitflyerSpotWebsocket
from libs.exchanges.bitmex import BitmexWebsocket
from libs.exchanges.btcmex import BtcmexWebsocket
from libs.exchanges.bybit import BybitWebsocket
from libs.exchanges.bybit_testnet import BybitTestWebsocket
from libs.exchanges.coinbase import CoinbaseWebsocket
from libs.exchanges.deribit import DeribitWebsocket
from libs.exchanges.ftx import FtxWebsocket
from libs.exchanges.gmo import GmoWebsocket
from libs.exchanges.huobi import HuobiWebsocket
from libs.exchanges.kraken import KrakenWebsocket
from libs.exchanges.okex import OkexWebsocket
```

この章ではwebsockettクラスの使い方を説明します。

---
### ■ クラスの生成・初期化

<br>

#### **●　まず初めにライブラリを読み込んでクラスを生成し・初期化します。**

ロジックの Initialize 関数内などで、下記のサンプルのようにライブラリを読み込んで、生成します。（下記の例ではBitmexのwwbsocketを受信するクラスを生成しています）

```python
from libs.exchanges.binance import BinanceWebsocket
self.bitmex = BitmexWebsocket(logger=self._logger,
                              subscribe={'execution': True,
                                         'board': True, 'ticker': True} )
```


|入力|型|説明|
|---|---|---|
|logger|class logger|ロガークラスを与えます。 BFSX2のロジック内では self._logger がロガークラスですので、これを指定してください。|
|subscribe|dict|購読するwebsocketのチャンネルを指定します。'execution'をTrueに指定すると約定通知（マーケットでの全約定）を受信し、'boardをTrueに指定すると板情報の更新を受信し、'ticker'をTrueにすると定期的に配信されるTicker情報を受信します。必要なチャンネルだけ受信することで無駄な負荷を増やさないようにすることが可能です。|

|出力|型|説明|
|---|---|---|
|戻り値| class| 生成されたクラス|

<br>

> クラスが生成されたら自動的にwebsocketの接続とチャンネルの購読が始まります。

<br>
<br>
<br>

#### **●　参照可能な情報（メンバ変数・メンバ関数）**

<u>**executionをTrueに指定して受信開始すると、下記のメンバ変数が使用可能です。**</u>

|変数|型|説明|
|---|---|---|
|(class WebsocketExchange).execution.time|datetime形式|直近のexecutions受信時刻|
|(class WebsocketExchange).execution.last|float|最新の約定価格 (LTP)|
|(class WebsocketExchange).execution.best_ask|float|最終のBUY価格|
|(class WebsocketExchange).execution.best_bid|float|最終のSELL価格|
|(class WebsocketExchange).execution.avg_price_1s|float|直近１秒の平均価格|
|(class WebsocketExchange).execution.avg_latency_1s|float|直近１秒の平均配信遅延 (msec)|

<br>
<br>

使用例）
```python
from libs.exchanges.binance import BinanceWebsocket
bitmex = BitmexWebsocket(logger=self._logger,
                              subscribe={'execution': True,
                                         'board': True, 'ticker': True} )
while True:
    spread = bitmex.execution.best_ask - bitmex.execution.best_bid
    self._logger.info( "spread : {}".format(spread))
    time.sleep(1)
```

<br>
<br>
<br>
<br>

<u>**boardをTrueに指定して受信開始すると、下記のメンバ変数が使用可能です。**</u>

|変数|型|説明|
|---|---|---|
|(class WebsocketExchange).board.time|datetime形式|直近のboard受信時刻|
|(class WebsocketExchange).board.asks|sorteddict.SortedValuesView|売り板のリスト。asks[0]が最もLTPに近い板の価格とサイズ|
|(class WebsocketExchange).board.bids|sorteddict.SortedValuesView|買い板のリスト。bids[0]が最もLTPに近い板の価格とサイズ|
|(class WebsocketExchange).board.best_ask|float|最もLTPに近い売り板の価格|
|(class WebsocketExchange).board.best_bid|float|最もLTPに近い買い板の価格|
|(class WebsocketExchange).board.mid|float|best_askとbest_bidの平均|

<br>
そのほか下記のメンバ関数で板をサイズごと（例：1btcごと）にまとめた情報や価格ごと（例：$10ごと）にまとめた情報を得ることができます。

<br>
<br>


#### **self.get_size_group(splitsize, limitprice, limitnum, startprice)**
> startprice (指定されていなければmid_priceからとなる) splitsize (単位:BTC)で指定したサイズで板の情報をグループ化し価格リストを返します。  
上下に向かって検索する限界ラインはlimitprice (単位:JPY) で指定できます。

|入力|型|説明|
|---|---|---|
|splitsize|float|分割するサイズ(単位:btc))|
|limitprice|float|探索する上限範囲（探索開始からの価格差）|
|limitnum|int|探索する上限個数|
|startprice|int|検索開始位置 (0の場合はその時点でのmid_priceから)|

|出力|型|説明|
|---|---|---|
|res|dict| {'ask': [売り板の価格リスト] , 'bid': [買い板の価格リスト] }|

<br>
使用例は
サンプルの dp_board_size.py などを参考にしてみてください。
<br>
<br>
<br>


#### **self.get_price_group(splitprice)**
> splitprice (単位:価格)で指定したサイズで板の情報をグループ化します。

|入力|型|説明|
|---|---|---|
|splitprice|float|分割する価格|

|出力|型|説明|
|---|---|---|
|res|dict| {'ask': [売り板のサイズリスト] , 'bid': [買い板のサイズリスト] }|

<br>
使用例は
サンプルの dp_board_price.py などを参考にしてみてください。
<br>
<br>
<br>
<br>

<u>**tickerをTrueに指定して受信開始すると、下記のメンバ変数が使用可能です。**</u>

|変数|型|説明|
|---|---|---|
|(class WebsocketExchange).ticker.time|datetime形式|直近のticker受信時刻|
|(class WebsocketExchange).ticker.last|float|最新の価格 (LTP)|

<br>
<br>
以下の情報は取引所によってサポートしている場合があります。

|変数|型|説明|
|---|---|---|
|(class WebsocketExchange).ticker.best_ask|float|best_ask|
|(class WebsocketExchange).ticker.best_bid|float|best_bid|
|(class WebsocketExchange).ticker.open_interest|float|open_interest (Bitmex/bybit/deribit などでサポート)|
|(class WebsocketExchange).ticker.best_ask|float|best_ask|
|(class WebsocketExchange).ticker.best_ask|float|best_ask|

<br>

>[hint]  
vars関数を使って　print(vars(websocket.ticker)) とすることでサポートしている変数を確認することが出来ます。

<br>

<div style="page-break-before:always"></div>

---
## ５．ロジック内で使用できるメンバ変数
---

BFSX2では、ユーザーがロジックを記載したクラス(MyStrategy)はベースとなるロジッククラスを継承する形で記載することで、事前に用意されたクラスメンバ変数を利用できます。これらの変数を参照することで売買判断などを行います。  


<br>
<br>


### ■ メンバ変数詳細

<br>

#### ●　self.parameters
> この変数ではロジックパラメータファイル(yamlファイル）で指定したparameters以下にアクセスできます

例えばyamlファイルに
```python
parameters:
 mfi_period : 50
 mfi_limit : 15
```
の様に記載されていた場合、self.parameters[`'mfi_period'`]には50が入っていて、self.parameters[`'mfi_limit'`]には15が入っています。

> [Tips]  
パラメータファイルは稼働中でも書き換え可能で、ファイルスタンプの変更を検知して自動的に再読み込みが行われます。パラメータを変えてみてパラメータの変化によるbotの挙動の変化を確認することが出来て便利ですので、変更する可能性のあるパラメータは出来るだけロジックパラメータファイル(yamlファイル）に記載してself.parametersから呼び出すようにしておきましょう。  

<br>
<br>

#### ●　self.symbol
> 取引対象の通貨 ( 'FX_BTC_JPY' / 'BTC_JPY' / 'BTCJPY29MAR2019' など) ```trade.yaml```で指定した```symbol```が取得できます。

<br>
<br>


#### ●　self.minimum_order_size
> 指定した取引所・通貨での最小売買単位を返します。

<br>
<br>

#### ●　self.collateral_rate
> 証拠金額の単位変換のために使用します。メンバ関数self.getcollateral_api()で得られる証拠金額にこの値を乗算すると、取引（ポジション数）に使用される単位に変換出来ます。

<br>
<br>




#### ●　self.current_pos
> 現在保有しているポジションです。  
ポジションは自炊管理して計算されたものですので、何度参照してもAPIアクセスは発生しません。売り建てポジの場合には数値はマイナスとなります。

使用例
```python
lotsize = self.parameters['lotsize']
# 現在ポジをプラスしてドテンロング
if fLong and lotsize-self.current_pos >= 0.01 :
    self._market_buy( size = lotsize-self.current_pos )
# 現在ポジをプラスしてドテンショート
if fShort and lotsize+self.current_pos >= 0.01 :
    self._market_sell( size = lotsize+self.current_pos )    
```

<br>
<br>


#### ●　self.current_average
> 現在保有しているポジションの平均価格です。

<br>
<br>



#### ●　self.current_profit
> 現在の算出利益です。（0:00に一度リセットされますので0:00からの利益です）


<br>
<br>


#### ●　self.current_fixed_profit
> 現在の確定損益です。


<br>
<br>


#### ●　self.current_profit_unreal
> 現在保有しているポジションの含み損益です。


<br>
<br>


#### ●　self.commission
> メイカー・テイカーフィーなどの手数料や、SFDなどの手数料損益です。


<br>
<br>


#### ●　self.ltp
> 現在のLTP価格です(trade.yamlファイルの中のproductで指定された取引所のLTP価格です)

> [Hint]  
ロジックの設定ファイルで  
subscribe:  
　execution: False  
と指定して約定通知の配信を受信しないように設定されていると使用できません

<br>
<br>

  
#### ●　self.best_ask
> 現在のbest_ask価格です(配信された約定履歴の最後のBUY価格をbest_askとしています)

> [Hint]  
ロジックの設定ファイルで  
subscribe:  
　execution: False  
と指定して約定通知の配信を受信しないように設定されていると使用できません
  
> [Hint]  
板情報からのbest_ask を取得するには self.ws.board.best_ask  
Tickerからbest_ask を取得するには self.ws.ticker.best_ask   
を使うことが可能です

<br>
<br>


#### ●　self.best_bid
> 現在のbest_bid価格です(配信された約定履歴の最後のSELL価格をbest_bidとしています)

> [Hint]  
ロジックの設定ファイルで  
subscribe:  
　execution: False  
と指定して約定通知の配信を受信しないように設定されていると使用できませんに
    
> [Hint]  
板情報からのbest_bid を取得するには self.ws.board.best_bid  
Tickerからbest_bid を取得するには self.ws.ticker.best_bid  
を使うことが可能です

<br>
<br>


#### ●　self.mid_price
> 板情報から得られる mid 価格です

> [Hint]  
websocketから板情報の受信を行うにはロジックの設定ファイルで  
subscribe:  
　board: True  
の指定をしておく必要があります


<br>
<br>


#### ●　self.asks
> 売り板のリスト。asks[0]が最もLTPに近い板の価格とサイズ

> [Hint]  
websocketから板情報の受信を行うにはロジックの設定ファイルで  
subscribe:  
　board: True  
の指定をしておく必要があります

データ例
```python
SortedValuesView(SortedDict({5662857.0: [5662857.0, 0.02], 5662858.0: [5662858.0, 0.01], 5662944.0: [5662944.0, 0.06], 5663121.0: [5663121.0, 0.0791], 5663575.0: [5663575.0, 0.01], 5663910.0: [5663910.0, 0.01], 5663960.0: [5663960.0, 0.2025689], 5664196.0: [5664196.0, 0.02], 5664288.0: [5664288.0, 0.02], 5664719.0: [5664719.0, 0.08], 5664841.0: [5664841.0, 0.02], 5664873.0: [5664873.0, 0.014], 5664946.0: [5664946.0, 0.08392789], 5664992.0: [5664992.0, 0.02704285], 5665005.0: [5665005.0, 0.0706], 5665079.0: [5665079.0, 0.02], 5665109.0: [5665109.0, 0.01], 5665605.0: [5665605.0, 0.05], 5665669.0: [5665669.0, 0.05], 5665681.0: [5665681.0, 0.01], 5665781.0: [5665781.0, 0.2], 5665865.0: [5665865.0, 0.01], 5666135.0: [5666135.0, 0.01], 5666335.0: [5666335.0, 0.010663], 5666410.0: [5666410.0, 0.05], 5667262.0: [5667262.0, 0.1], 5667344.0: [5667344.0, 0.17], 5669578.0: [5669578.0, 0.125], 5670575.0: [5670575.0, 0.12660324], 5670593.0: [5670593.0, 0.01], 5670601.0: [5670601.0, 0.12997119], 5671088.0: [5671088.0, 0.05], 5671494.0: [5671494.0, 0.02], 5671930.0: [5671930.0, 0.02], 5684780.0: [5684780.0, 0.1186278], 5684797.0: [5684797.0, 0.08178658], 5684803.0: [5684803.0, 0.01]}))
```

<br>
<br>


#### ●　self.bids
> 買い板のリスト。bids[0]が最もLTPに近い板の価格とサイズ

> [Hint]  
websocketから板情報の受信を行うにはロジックの設定ファイルで  
subscribe:  
　board: True  
の指定をしておく必要があります


```python
SortedValuesView(SortedDict({-5650005.0: [5650005.0, 0.04], -5650004.0: [5650004.0, 0.01], -5650003.0: [5650003.0, 0.04], -5650001.0: [5650001.0, 0.43588034], -5650000.0: [5650000.0, 0.0367], -5649931.0: [5649931.0, 0.05], -5649930.0: [5649930.0, 0.01], -5649929.0: [5649929.0, 0.02], -5649927.0: [5649927.0, 0.1], -5649888.0: [5649888.0, 0.01181], -5649887.0: [5649887.0, 0.04422532], -5649841.0: [5649841.0, 0.01], -5649781.0: [5649781.0, 0.01], -5649772.0: [5649772.0, 0.02], -5649770.0: [5649770.0, 0.16523845], -5649730.0: [5649730.0, 0.01], -5649718.0: [5649718.0, 0.0708], -5649640.0: [5649640.0, 0.02], -5649621.0: [5649621.0, 0.05], -5649607.0: [5649607.0, 0.01], -5649590.0: [5649590.0, 0.05], -5649521.0: [5649521.0, 0.05], -5649500.0: [5649500.0, 0.073], -5649416.0: [5649416.0, 0.01], -5649384.0: [5649384.0, 0.01], -5649366.0: [5649366.0, 0.02], -5649334.0: [5649334.0, 0.05], -5649332.0: [5649332.0, 0.4], -5649328.0: [5649328.0, 0.01], -5649254.0: [5649254.0, 0.05], -5649243.0: [5649243.0, 0.01], -5649208.0: [5649208.0, 0.8229462], -5649187.0: [5649187.0, 0.05], -5649185.0: [5649185.0, 0.011], -5649181.0: [5649181.0, 0.037], -5649178.0: [5649178.0, 0.02], -5649129.0: [5649129.0, 0.01]}))
```

<br>
<br>


#### ●　self.server_latency
> 直近１秒の平均配信遅延 (msec)です。サーバーの遅延判断などにお使い頂けます。


<br>
<br>


#### ●　self.api_remain1
> APIリミットまでの残数


<br>
<br>

#### ●　self.api_remain2
> APIリミットまでの残数

>[Hint]  
bitFlyerでの発注系のAPIリミットです


<br>
<br>

#### ●　self.sfd
> 現在の乖離率(SFD値)です　(bitFlyer限定)


<br>
<br>

#### ●　self.ordered_list
> 現在の発注済み（子注文）の未約定リストが取得できます。(dict型のリスト形式)  
> 特殊注文(親注文)のトリガーによって発生した子注文も含まれます

|キー|型|説明|
|---|---|---|
|id|string|order_id|
|ordered_time|timestamp|発注時のタイムスタンプ|
|remain|float|未約定数|
|symbol|str|取引ペア|
|side|str|```'BUY'``` / ```'SELL'```|
|price|float|注文価格|
|size|float|注文数量|
|expire|timestamp|auto_cancel_afterにより自動的にキャンセルされる時間|
|invalidate|timestamp|オーダーリストから削除される時間|
|close|bool|決済注文かどうか|
|accepted_time|timestamp|サーバーからオーダー完了のイベントを受け取った時間|

データ例
```python
[{'id': '1206378535', 'ordered_time': 1615200306.5398426, 'remain': 0.01, 'symbol': 'BTC_JPY', 'side': 'BUY', 'price': 5445050.0, 'size': 0.01, 'expire': 1615200336.5398378, 'invalidate': 1617792306.5398386, 'close': True, 'accepted_time': 1615200306.6065586}, {'id': '1206378547', 'ordered_time': 1615200319.2071667, 'remain': 0.01, 'symbol': 'BTC_JPY', 'side': 'BUY', 'price': 5447223.0, 'size': 0.01, 'expire': 1615200349.207162, 'invalidate': 1617792319.2071626, 'close': True, 'accepted_time': 1615200319.332975}]
```


<br>
<br>

<div style="page-break-before:always"></div>

#### ●　self.executed_history
> 約定済みのリスト（直近300件）


|キー|型|説明|
|---|---|---|
|id|string|order_id|
|exec_time|timestamp|約定時ののタイムスタンプ|
|ordered_time|timestamp|発注時のタイムスタンプ|
|remain|float|未約定数|
|symbol|str|取引ペア|
|side|str|```'BUY'``` / ```'SELL'```|
|price|float|注文価格|
|size|float|注文数量|
|expire|timestamp|auto_cancel_afterにより自動的にキャンセルされる時間|
|invalidate|timestamp|オーダーリストから削除される時間|
|close|bool|決済注文かどうか|
|accepted_time|timestamp|サーバーからオーダー完了のイベントを受け取った時間|

データ例
```python
[{'id': '1206378530', 'exec_time': 1615200309.203294, 'ordered_time': 1615200299.203301, 'remain': 0.0, 'symbol': 'BTC_JPY', 'side': 'SELL', 'price': 5447237.0, 'size': 0.01, 'expire': 1615200329.203294, 'invalidate': 1617792299.203295, 'close': False, 'accepted_time': 1615200299.374965}, {'id': '1206378524', 'exec_time': 1615200317.0502915, 'ordered_time': 1615200297.0502994, 'remain': 0.0, 'symbol': 'BTC_JPY', 'side': 'SELL', 'price': 5448562.0, 'size': 0.01, 'expire': 1615200327.0502915, 'invalidate': 1617792297.0502925, 'close': False, 'accepted_time': 1615200297.075869}]
```

<br>
<br>


#### ●　self.log_folder
> ロジックの設定ファイルで指定されたログフォルダ  
ロジック側で何らかの保存ファイルなどを作成したい場合にはこのフォルダの中に作成することが推奨されます。

<br>
<br>

#### ●　self.no_trade_period
> 指定されたノートレード期間かどうか (True/False) を確認できます。  

<br>
<br>


#### ●　self.time
> 現在時刻のタイムスタンプです。実稼働時は time.time() と同じですが、今後サポートするバックテストなどでも正常動作するように time.time() の代わりに self.time() を使用することをお勧めします。

<br>
<br>



<div style="page-break-before:always"></div>

---
## ６．ロジック内で使用できるメンバ関数
---

BFSX2では、2章で説明した **「ロジックの動作を決める主要な関数」** 以外にいくつかのメンバ関数が用意されています。事前に用意されたクラスメンバ関数を利用することで実際の売買を行います。 

### ■ メンバ関数詳細

<br>
<br>


#### ●　self.sendorder(order_type, side, size, price)
> 注文を発行します。  
詳細なオプションは3章を参照ください

|入力|型|説明|
|---|---|---|
|order_type|string|注文の執行条件(LIMIT/MARKET)|
|side|string|売買方向。買い注文の場合は "BUY", 売り注文の場合は "SELL" を指定します。すべて大文字で指定してください。|
|size|float|売買数量|
|price|float|執行条件がLIMITの場合の指値価格(MARKETの場合には省略可能)|
|auto_cancel_after|float|指定すると、指定秒数経過後にBFSX2内部で自動的にキャンセルが実行されます。省略した場合のデフォルトは2592000(30 日間) です。なお order_type が"MARKET" の場合にはこのパラメータは意味がありません。|

|出力|型|説明|
|---|---|---|
|res|dict| 'stat': ステータスコード（0が正常終了）'msg':  エラーメッセージ　'id' :  オーダーID|  
コード例
```python
self.sendorder(order_type="LIMIT", side="BUY", size=0.01, price=3854000, auto_cancel_after=5)
```

<br>

実行例(正常オーダー時)
```python
{'stat':0 , 'msg':'', 'id':'JRF20191211-001824-668915'}

{'stat':0 , 'msg':'', 'id':'7b9055dc-5cde-425f-8bf9-13b9021d0c24'}

```
実行例(エラー時　(例))
```python
{'stat':-106 , 'msg':'The price is too low.', 'id':None}
```
```python
{'stat':-205 , 'msg':'Margin amount is insufficient for this order.', 'id':None}
```

<br>

> BFSX2では本体側でのオーダーリトライを行っていません。戻り値のステータスコードやIDを見て必要ならリトライするようにロジック側で処理してください。


<br>
<br>


#### ●　self.cancelorder( id )
> idを指定して注文キャンセルを行います。オーダー発注時の戻りから `id` を保存しておいて、idを指定することで個別キャンセル処理を行えます。

|入力|型|説明|
|---|---|---|
|id|string|オーダーID|

|出力|型|説明|
|---|---|---|
|res|dict| 'stat': ステータスコード（0が正常終了）'msg':  エラーメッセージ|

実行例(正常オーダー時)
```python
{'stat':0 , 'msg':''}
```

<br>
<br>



#### ●　get_historical_counter(sec)
> 直近のオーダー数、約定数や約定サイズを取得することができます。

|入力|型|説明|
|---|---|---|
|sec|int|取得する期間（秒）|

|出力|型|説明|
|---|---|---|
|res|dict| 'ordered':発出したオーダー数　'filled':全約定したオーダー数  'partially_filled':部分約定数  'canceled':キャンセルされたオーダー数  'size':取引量|

実行例
```python
{'ordered': 27, 'filled': 7, 'partially_filled': 0, 'canceled': 19, 'size': 0.07}
```

> [Hint]  
たとえば sec=5 の場合、5秒以上前にオーダーした指値が直近5秒以内に約定した場合、'ordered'は0で、'filled'が1となります。  
ですので完全約定率 (分子=['filled']) や、部分約定率 (分子=['partially_filled']) を計算したい場合の分母は['ordered']ではなく、['filled']+['partially_filled']+['canceled']を使ってください。

<br>
<br>


#### ●　self.getcollateral_api()
> REST APIを利用して証拠金残高を取得します。  
どの取引所でも辞書型戻り値の 'collateral'キーに証拠金残高が入っています。  
'msg'キーには取引所ごとに異なる詳細なレスポンス情報が入ってますので必要に応じて参照することができます。

|入力|型|説明|
|---|---|---|
|無し|||

|出力|型|説明|
|---|---|---|
|res|dict| 'stat': ステータスコード（0が正常終了）'collateral' 証拠金残高  'msg':  取引所からのレスポンスメッセージ|

実行例(正常オーダー時)
```python
bitFlyerでの実行例
{'stat': 0, 'collateral': 13381356.656250449, 'msg': {'collateral': 13381356.656250449, 'open_position_pnl': -79025.0, 'require_collateral': 3199500.0, 'keep_rate': 4.1576282719957645}}

bybitでの実行例
{'stat': 0, 'collateral': 0.03361992, 'msg': {'ret_code': 0, 'ret_msg': 'OK', 'ext_code': '', 'ext_info': '', 'result': {'BTC': {'equity': 0.03361992, 'available_balance': 0.03361552, 'used_margin': 1.95e-06, 'order_margin': 0, 'position_margin': 0.03359217, 'occ_closing_fee': 2.53e-05, 'occ_funding_fee': 0, 'wallet_balance': 0.03361747, 'realised_pnl': 2.96e-06, 'unrealised_pnl': 2.45e-06, 'cum_realised_pnl': -0.00160589, 'given_cash': 0, 'service_cash': 0}}, 'time_now': '1617002700.423162', 'rate_limit_status': 119, 'rate_limit_reset_ms': 1617002700420, 'rate_limit': 120}}

GMOでの実行例
{'stat': 0, 'collateral': '6076245', 'msg': {'status': 0, 'data': {'actualProfitLoss': '6076245', 'availableAmount': '5621707', 'margin': '455799', 'marginRatio': '1911.1', 'profitLoss': '-1261'}, 'responsetime': '2021-03-29T07:25:54.609Z'}}
```

<br>
<br>

>[Tips]  
証拠金残高の単位は取引所によってはBTCであったりJPYであったりしますので、メンバ変数 self.collateral_rate を使って必要に応じて換算してください。


<br>
<br>


#### ●　self.send_discord( text, image )
> position_discord_webhooksで指定したDiscord webhookへメッセージまたはメッセージと画像を送ることが出来ます。メッセージに@everyoneなどのメンションを付けておき、通知設定することでスマートフォンなどへの通知にも使えます。

|入力|型|説明|
|---|---|---|
|text|string|送信するメッセージ|
|image|string|送信する画像のパス名 (画像がない場合は省略可)|

|出力|型|説明|
|---|---|---|
|-|-|-|





<div style="page-break-before:always"></div>


---
## ７．BFSX2の稼働パラメータファイル(trade.yaml)のパラメータ
---


BFSX2の動作に関して、稼働パラメータファイルで設定を変更することが出来ます。  
稼働パラメータファイルのデフォルト名は```trade.yaml```ですが、1章で説明した通り起動時引数で指定することも可能です。

### ■ ファイル形式
稼働パラメータファイルはYAML形式で記載されており、```項目名 : 値``` の形式で記載されています。



記述例（デフォルトのパラメータ）  
<br>
<img src="img/sec7-1.png">

<br>
<br>

<div style="page-break-before:always"></div>

### ■ 設定パラメータ詳細

<br>
<br>


#### ●　strategy_py :
読み込むロジックファイル(.py)を指定します。
カレントフォルダ(trade.pyがあるフォルダ)からの相対パスで指定します。


<br>
<br>



#### ●　strategy_yaml :
読み込むロジックパラメータファイル(.yaml)を指定します。
カレントフォルダ(trade.pyがあるフォルダ)からの相対パスで指定します。

<br>
<br>



#### ●　exchange :
取引する取引所を選択します。現在サポートしているのは下記の4つの取引所です（2021/04現在)
```
bitFlyer
GMO
bybit
phemex
```

<br>
<br>



#### ●　testnet :
testnetを使用するかどうかを選択します。bybitとphemexにはデモトレードを行えるtestnetがあります。（別途登録必要）
testnetを使用する場合には **true** に設定します。

<br>
<br>

<div style="page-break-before:always"></div>

#### ●　symbol :
取引するシンボルペアを指定します。取引所によって指定できるシンボルが異なります。
```
bitFlyer : FX_BTC_JPY / BTC_JPY(現物) /ETH_JPY(現物) 等
GMO : BTC_JPY / BTC(現物) 等
bybit : BTCUSD / ETHUSD 等
phemex : BTCUSD / ETHUSD 等
```

<br>
<br>



#### ●　apikey :
APIの ```API Key``` を設定します。  

<br>
<br>



#### ●　secret :
APIの ```API Secret``` を設定します。

<br>
<br>



#### ●　base_position :
ある一定のポジションをキープしながら運用する場合に使用します。  
apiから取得したgetpositionsの値に対して、ここで指定した数(単位はBTC)を引いて判定することで、adjust_position_with_apiを使用した際に常に一定のポジションを持つようにすることができます。  
例えば常にショートポジションをもってSFDを回避するようなときに使用します。

<br>
<br>




#### ●　adjust_position_with_api :
定期的なポジション補正を行うかどうかを指定します。(true / false)  
trueを指定しておくと定期的にAPIでgetpositionsを行い、自炊している想定ポジションと実際のポジションがズレている場合に、成売買でポジション数を合わせるように補正を行います。  
複数botを稼働させる場合にはこの項目は```false```にして、別途ポジションサーバーを稼働させるようにしてください。（9章を参照してください）

<br>
<br>

<div style="page-break-before:always"></div>

#### ●　adjust_max_size :
ポジズレを補正する際に、一度に大きな成行売買を行わないように、一度に発注する最大量を指定することが出来ます。

<br>
<br>



#### ●　pos_server :
ポジションサーバーを利用する際に接続先を指定します。（詳細は9章を参照してください）


<br>
<br>



#### ●　console_log_level :（DEBUG / INFO / WARNING / ERROR)
コンソールに出力するログレベルを変更します。
このパラメータは稼働中でも変更可能です。


<br>
<br>



#### ●　console_output :
稼働時にコンソール出力を行うかどうかを選択します。(true / false)  
この項目をfalseにすると、コンソールに出力する代わりにログフォルダ内にconsole.txtというファイルを作成しそちらへ出力を行います。  
SSHなどでターミナル接続して稼働させる場合にターミナルを切断しても稼働を続けるためnohupコマンドで起動させますが、その際にコンソールの代わりファイルに出力させておけば、tail -f console.txtとコマンドを打つことでログをリアルタイム表示させて稼働チェックを行う事が出来ます。  
このパラメータは稼働中でも変更可能です。


<br>
<br>





<div style="page-break-before:always"></div>

---
## ８．ロジックの設定ファイル(strategy.yaml)のパラメータ
---

各ロジックごとに異なる設定に関しては、ロジックごとのパラメータファイルで設定を変更することが出来ます。  
パラメータ類は（一部を除いて）稼働中でも変更でき、再起動の必要はありません。  
使用する設定ファイルは1章で説明した通り、稼働パラメータファイル(trade.yaml)にて指定することもできますし、起動時引数で指定することも可能です。

### ■ ファイル形式
稼働パラメータファイルはYAML形式で記載されており、```項目名 : 値``` の形式で記載されています。



記述例  
<br>
<img src="img/sec8-1.png">

<br>
<br>

<div style="page-break-before:always"></div>

### ■ 設定パラメータ詳細

<br>
<br>


#### ●　parameters :
ロジックの中で読み込むパラメータをこのセクションに記載します。  
ロジックの判定基準などに使うパラメータをここに記載しておくことで、リアルタイムにパラメータを変更することが可能です。  

記述例
```python
parameters:
  short_sma : 7
  long_sma : 14
  lotsize : 0.1
```
上記の記載例であれば、ロジック内からは ```self.parameters['short_sma']``` などでパラメータにアクセス可能です。

<br>
<br>

#### ●　order :
発注に関するパラメータをこのセクションに記載します。  

 →　option :  
>  オーダー発出時のデフォルトオプションを指定することができます。詳細は3章の「ロジックの設定ファイルで指定」の項を参照してください。

 →　wait_after_order :  
>  成り行き売買後のオーダー禁止時間を指定することができます。取引所によっては成り行きオーダー発出後ポジションに反映されるまで時間がかかるの場合があるので急変時などに2重発注しないように適切な秒数を指定します。

<br>
<br>

<div style="page-break-before:always"></div>

#### ●　logging :
ファイルとして残るログに関するパラメータをこのセクションに記載します。

 →　folder :  
>  log フォルダ名を指定します（最後にスラッシュ必要）  
注）このパラメータは稼働後に変更することができません

 →　level :  
>  logファイルに残すログのレベルを指定します。  
DEBUG/INFO/ERROR が選択できます。  
コンソールに表示されるログレベルは 稼働パラメータファイル(trade.yaml) で別途指定しますので、特段の理由がない場合には不具合時の解析などのためにDEBUGレベルに指定してファイルにログを残しておくことをお勧めします。  

<br>

#### ●　plot :
プロット関連の設定パラメータをこのセクションに記載します。

 →　pos_interval :  
>  ポジション通知間隔(分)を指定します  

 →　pnl_interval :  
>  損益グラフ通知間隔(分)を指定します  

 →　setting / period :  
>  ポジション損益のプロット区間(分)を指定します（最大は1440分＝1日）です  

 →　setting / plot_commission :  
>  テイカー・メイカーコミッションやSFDコミッションをプロットするかどうかを指定します（True/False）  

 →　setting / plot_fixed_pnl :  
>  Trueに指定すると含み損益は含まず確定損益のグラフをプロットします（True/False）  


<br>

#### ●　discord :
discordへの通知関連の設定パラメータをこのセクションに記載します。

 →　webhook :  
>  Discord 通知先チャンネルの webhook を指定します


<div style="page-break-before:always"></div>

#### ●　no_trade :
>トレード停止する時間を指定することが可能です。   
指定した期間はポジションを減らす方向（ロングポジを持っている場合にはショートオーダー、ショートポジを持っている場合にはロングオーダー）のみを実行します。  


記述例１
```python
# メンテ前の3:50～メンテ明けの4:10までの期間トレードを停止する
no_trade :
  - period: 03:50-04:10
```

カンマの後に曜日指定することも可能です。（0=月曜日、1=火曜日、…　5=土曜日、6=日曜日）  

記述例２
```python
# 土曜日の1:50～11:00まではトレードを停止する
no_trade :
  - period: 01:50-11:00,5
```

日付指定を行うことも可能です。

記述例３
```python
# 2020/8/26 23:50～2020/8/27 9:10 まではトレードを停止する
no_trade :
  - period: 2020-08-26T23:50,2020-08-27T09:10
```

複数行記述することで複数の時間帯を指定することも可能です。

記述例４
```python
no_trade :
  - period: 23:45-00:10
  - period: 03:50-04:10
  - period: 01:50-11:00,5
```
> [Tips]   
ノートレード期間に入った時にポジションを強制的にクローズするかどうかは`close_while_noTrade`で指定できます。  
`True`に指定した場合には no_trade 期間に入ったときに強制的に成売買でポジションクローズします。  


<br>
<br>

#### ●　close_while_noTrade :
>no_tradeパラメータでトレード停止期間を指定している場合、そのトレード停止期間に入ったさいに持っていたポジションをクローズするかどうかを指定します。(true/false)  
短期間に取引を行うmmbotなどではノートレード期間の価格変動リスクを避けるためにノーポジションにするほうが安全ですが、長期間の取引を行うスイングロジックなどではノートレード期間でもポジションを保持する方が良いでしょう。

<br>
<br>







<div style="page-break-before:always"></div>

---
## ９．ポジションサーバーについて
---

BFSX2では複数稼働させた場合のポジずれ補正のため、および合計損益のプロットやInfluxDBへの損益書き込みなどをサポートするポジションサーバーを使うことができます。



### ■ 起動方法

<br>
<br>
BFSX2でのポジションサーバーはメインのフレームワーク(BFSX2)上で動作するストラテジーとして稼働し、

```
python3 trade.py pos_server/pos_server.py pos_server/pos_server_bitflyer_fxbtcjpy.yaml
```
という様に起動します。  
（当然 bot稼働と同様に、trade.yaml 内の strategy_py: と strategy_yaml: に記載しても起動可能です）

取引所や取引シンボル、APIキーなどは trade.yaml 内に記載し、使用するポートやその他設定は ストラテジーの設定ファイル（上記起動例であればpos_server_bitflyer_fxbtcjpy.yaml）に記載します。


<br>
<br>

<img src="img/sec9-1.png">

<br>
<br>


複数の取引所または複数の取引ペアに対応するためには、複数のポジションサーバーを起動させます。
その際はポート番号が重複しないように設定してください。

<br>
<br>

<img src="img/sec9-2.png">

<br>
<br>

ポジションサーバーを別のVPSで動かす場合にはサーバー側のIPアドレスは 0.0.0.0 を指定します。  
UDPの通信ポートを開放する必要がありますので、ファイヤーウォールの設定などを適宜行うようにしてください。

<br>
<br>

<img src="img/sec9-3.png">

<br>
<br>

ポジションサーバーではInfluxDBへデータを書き込んでGrafanaなどで一括して損益やポジションを監視することもできます。
<br>
<br>

<img src="img/sec9-4.png">

