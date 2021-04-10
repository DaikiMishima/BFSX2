# coding: utf-8
#!/usr/bin/python3

from threading import Thread
import json
import time
import traceback
import websocket

# Websocketを管理するクラス（基底クラス）
class WebsocketConnection(object):

    def __init__(self, logger):
        self._logger = logger
        self._connected = False
        self._stop = False
        self.running = False
        self._start()

    def _start(self):
        def _on_open(ws):
            self._logger.info(self.__class__.__name__ + ": websocket connected to '" + self._endpoint + "'")
            self._connected = True
            try:
                self._on_connect()
            except Exception as e:
                self._logger.error( self.__class__.__name__ + ": error while calling _on_connect" )
                self._logger.error( e )
                self._logger.info(traceback.format_exc())

        def _on_error(ws, error):
            self._logger.error(self.__class__.__name__ + ": Error message received")
            self._logger.error(error)
            ws.close()

        def _on_close(ws):
            self._logger.error(self.__class__.__name__ + ": websocket closed")
            self._connected = False
            if self._auth and not hasattr(self,'_private_ws') : # GMOのように Private ws が別接続の場合には Public ws の切断でもPrivate ws の認証は切れていない
                self._auth.auth_completed = False
                self._auth.auth_retry = 1
                self._auth.auth_retry_time = 0
            try:
                self._on_disconnect()
            except Exception as e:
                self._logger.error( self.__class__.__name__ + ": error while calling _on_disconnect" )
                self._logger.error( e )
                self._logger.info(traceback.format_exc())
        def _run(ws):
            self.running = True
            while not self._stop:
                self._logger.debug( self.__class__.__name__ + ": enter to run_forever()" )
                ws.run_forever()
                self._logger.error( self.__class__.__name__ + ": exit from run_forever()" )
                time.sleep(1)
            self.running = False

        def _on_message(ws, message):
            try:
                self._recv_message(message)
            except Exception as e:
                self._logger.error( self.__class__.__name__ + ": error while calling _recv_message" )
                self._logger.error( e )
                self._logger.info(traceback.format_exc())

        self.ws = websocket.WebSocketApp( self._endpoint, on_open=_on_open, on_message=_on_message, on_error=_on_error, on_close=_on_close )
        self._thread = Thread(target=_run, args=(self.ws, ))
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        self._logger.debug( "Stop thread {}".format(self) )
        self._stop = True
        self.ws.close()

    def _recv_message(self, message):
        msg = json.loads(message)
        self._message( msg )

    # 接続後の処理が必要な場合にはサブクラスでオーバーライドを
    def _on_connect(self):
        pass

    # 切断後の処理が必要な場合にはサブクラスでオーバーライドを
    def _on_disconnect(self):
        pass


# 1つのコネクションで複数のチャンネル購読をサポートするクラス
class WebsocketMultiChannel(WebsocketConnection):
    def __init__(self, logger):
        self._handler = {}
        super().__init__(logger)

    def _subscribe(self, channel, event, handler):
        while not self._connected:
            time.sleep(1)
        self._handler[event]=handler
        self.ws.send(json.dumps(channel))
        self._logger.debug(self.__class__.__name__ + ": subscribe '"+ event + "'")
        self._event = event

    def _recv_message(self, message):
        try:
            msg = self._message_dump(message)
            if isinstance(msg, list):
                msg = self._edit_message(msg)
            if msg == '' : return   # 各取引所個別のクラスでハンドリング済みの場合には何もしない
            event = msg.get(self._channel_str)
            channel_handler = self._handler.get(event)
            if channel_handler != None:
                channel_handler(msg)
        except Exception as e:
            self._logger.error( self.__class__.__name__ + ": error while calling _recv_message" )
            self._logger.error( e )
            self._logger.info(traceback.format_exc())

    def _message_dump(self, message):
        msg =json.loads(message)
        return msg

    def _edit_message(self, msg):
        if self._event == 'trades' and msg[1] == 'te':
            message = {'chanel': 'trades', 'trade': msg[-1]}
        elif self._event == 'book' and isinstance(msg[1], list):
            data_list = []
            if isinstance(msg[1][0], list) and len(msg[1][0]) == 3:
                for i in msg[1]:
                    side = 'Sell' if i[2] > 0 else 'Buy'
                    data_list.append({'id': i[0], 'price': i[1], 'size': abs(i[2]), 'side': side, })
            elif isinstance(msg[1][0], list) and len(msg[1][0]) == 4:
                return ''
            else:
                side = 'Sell' if msg[1][2] > 0 else 'Buy'
                data_list.append({'id': msg[1][0], 'price': msg[1][1], 'size': abs(msg[1][2]), 'side': side})
            message = {'chanel': 'book', "data": data_list}
        else:
            message = ''
        return message

