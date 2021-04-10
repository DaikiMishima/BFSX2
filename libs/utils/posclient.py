# coding: utf-8
#!/usr/bin/python3

from threading import Thread
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM

# ポジションサーバーに接続して損益を送るクラス
class PositionClient(object):
    def __init__(self, logger, exchange, strategy, pos_server=None):
        if not pos_server:
            return

        self._logger = logger
        self._pos_server = pos_server
        self._ws, self._api = (exchange)
        self._strategy=strategy

        # ポジションをUDPで送信するスレッドを起動
        self._stop = False
        self.position_thread = Thread(target=self.send_position)
        self.position_thread.daemon = True
        self.position_thread.start()
        self._logger.stop_list.append([self.stop,self.send_position])

    def stop(self):
        self._stop = True

    def send_position(self):
        self._logger.info("Start position thread (connected to {})".format(self._pos_server) )
        self.socket = socket(AF_INET, SOCK_DGRAM)
        while not self._stop:
            self._ws.my.update.wait(10)
            self._ws.my.update.clear()
            message = "{:>10} : {:>15.8f} : {:>15.8f} :{:>11g}: {:>3} : {:>3} : {}".format(
                self._api.symbol[:10],
                self._ws.my.position.size,
                self._ws.my.position.base_position,
                self._ws.my.position.profit,
                self._api.api_remain1 if hasattr(self._api,'api_remain1') else 300 ,
                self._api.api_remain2 if hasattr(self._api,'api_remain2') else 300 ,
                self._strategy)
            self.socket.sendto(message.encode('utf-8'), (self._pos_server[0], self._pos_server[1]))

