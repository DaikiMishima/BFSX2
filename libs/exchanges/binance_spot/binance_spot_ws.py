# coding: utf-8
#!/usr/bin/python3

#-------------参考
# https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md

from libs.exchanges.binance.binance_ws import BinanceWebsocket
from libs.exchanges.base_module.base_exchange import WebsocketExchange

class BinanceSpotWebsocket(BinanceWebsocket):

    def __init__(self, logger, subscribe={}, auth=None):
        self._endpoint = "wss://stream.binance.com:9443/ws/btcusdt"    # Binance 現物
        self._channel_str = "e"
        self._param = subscribe
        WebsocketExchange.__init__(self,logger)

