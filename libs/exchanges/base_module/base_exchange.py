# coding: utf-8
#!/usr/bin/python3

from libs.exchanges.base_module.ws.base_websocket import WebsocketMultiChannel

from libs.exchanges.base_module.board.base_board import WebsocketBoard
from libs.exchanges.base_module.execution.average_execution import WebsocketExecuions
from libs.exchanges.base_module.ticker.base_ticker import WebsocketTicker

# 取引所ベースクラス（板情報＋約定情報＋Ticker）
class WebsocketExchange(WebsocketMultiChannel, WebsocketBoard, WebsocketExecuions, WebsocketTicker):

    def __init__(self, logger):
        WebsocketBoard.__init__(self,logger)
        WebsocketExecuions.__init__(self,logger)
        WebsocketTicker.__init__(self,logger)
        WebsocketMultiChannel.__init__(self,logger)

