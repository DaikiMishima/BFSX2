# coding: utf-8
#!/usr/bin/python3

from libs.exchanges.base_module.utils.time_conv import TimeConv

# Tickerを管理するクラス
class WebsocketTicker(TimeConv):

    def __init__(self, logger):
        self.ticker = TickerInfo()
        self.ticker.time = self._jst_now_dt() #　直近のTicker受信時刻     (datetime形式)

class TickerInfo(object):
    def __init__(self):
        self.last = 0




# テストコード
if __name__ == "__main__":
    from logging import getLogger, StreamHandler, INFO
    import time
    try:
        from .base_websocket import WebsocketConnection
    except ImportError:
        from base_websocket import WebsocketConnection

    logger = getLogger(__name__)
    handler = StreamHandler()
    handler.setLevel(INFO)
    logger.setLevel(INFO)
    logger.addHandler(handler)

    class ticker_ws(WebsocketTicker,WebsocketConnection):
        _endpoint = "wss://stream.binance.com/ws/btcusdt@ticker"
        def __init__(self,logger):
            WebsocketTicker.__init__(self,logger)
            WebsocketConnection.__init__(self,logger)
        def _message(self, msg):
            self.ticker.last = float(msg.get('c',0))

    ws = ticker_ws(logger)

    while True:
        try:
            logger.info( "{:.2f}".format(ws.ticker.last) )
            time.sleep(1)

        except KeyboardInterrupt:
            ws.stop()
            break
