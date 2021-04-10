from logging import getLogger, INFO, StreamHandler, FileHandler
import datetime
import json
import websocket
import dateutil.parser
import time
from threading import Thread
import signal
import os

logger = getLogger(__name__)

handler = StreamHandler()
handler.setLevel(INFO)
logger.setLevel(INFO)
logger.addHandler(handler)


def quit_loop(signal, frame):
    os._exit(0)

class Websocketexecutions(object):
    def __init__(self, url, product):
        self._url = url
        self._channel_executions = product
        self.last_acceptance_id = ""
        self.total_size = 0
        self.last_day = 0

    def startWebsocket(self):
        def format_date(date_line):
            milii_second = date_line * 0.001
            return datetime.datetime.fromtimestamp(milii_second)

        def on_open(ws):
            print("Websocket connected")
            ws.send(json.dumps({"event": "subscribe", "channel": 'book', 'symbol': self._channel_executions}))

        def on_error(ws, error):
            print(error)

        def on_close(ws):
            print("Websocket closed")

        def run(ws):
            while True:
                ws.run_forever()
                time.sleep(3)

        def on_message(ws, message):
            messages = json.loads(message)
            print(messages)
            recept_data = messages[2]
            te_tu = messages[1]
            currenttime = time.time()
            if te_tu == 'tu':
                exec_date = format_date(recept_data[1])
                latency = round(currenttime - exec_date.timestamp(), 3)
                if recept_data[2] > 0:
                    side = 'BUY'
                else:
                    side = 'SELL'
                price = recept_data[3]
                size = abs(recept_data[2])
                id = recept_data[0]

                logger.info("{},{},{},{},{},{}".format(exec_date, side, price, size, id, latency))

                if self.last_day != exec_date.day:  # 日付が変わったら出力ファイルを変更
                    for h in logger.handlers[1:]:
                        logger.removeHandler(h)  # 標準出力(logger.handlers[0])以外を除去
                    fh = FileHandler('finex_exec-pack_' + exec_date.strftime('%Y-%m-%d') + '.csv')
                    logger.addHandler(fh)  # 日ごとのCSVファイルハンドラを追加
                    self.last_day = exec_date.day

        ws = websocket.WebSocketApp(self._url, on_open=on_open, on_message=on_message, on_error=on_error,
                                    on_close=on_close)
        websocketThread = Thread(target=run, args=(ws,))
        websocketThread.start()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, quit_loop)

    ws = Websocketexecutions(url='wss://api.bitfinex.com/ws/2', product='tBTCUSD')
    ws.startWebsocket()

    while True:
        time.sleep(1)
