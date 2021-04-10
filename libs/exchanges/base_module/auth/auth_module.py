# coding: utf-8
#!/usr/bin/python3

from hashlib import sha256
import hmac
import time
from threading import Thread

# 認証関係のクラス
class Auth(object):
    def __init__(self, logger, apikey, secret):
        self._logger = logger
        self.apikey = apikey
        self.secret = secret

        self.auth_retry = 1
        self.auth_retry_time = 0
        self.auth_completed = False
        self.auth_handler = None

    def generate_sign(self, secret, param_str):
        return hmac.new(secret.encode('utf-8'), param_str.encode('utf-8'), sha256).hexdigest()

    def start_auth(self, handler):
        self._stop = False
        self.auth_handler = handler
        self._logger.info( self.auth_handler.__self__.__class__.__name__ + ": Auth process started")
        self._auth_check_th = Thread(target=self._auth_check)
        self._auth_check_th.daemon = True
        self._auth_check_th.start()
        self._logger.stop_list.append([self.stop,self._auth_check])

    def auth_complete(self):
        if self.auth_handler :
            self._logger.info( self.auth_handler.__self__.__class__.__name__ + ": Websocket auth successed")
        self.auth_retry = 1
        self.auth_completed = True

    def retry_auth(self,msg):
        self._logger.error( self.auth_handler.__self__.__class__.__name__ + ": auth error: {}  retry({}/3)".format(msg, self.auth_retry))
        if self.auth_retry  < 3:
            self.auth_retry += 1
            self.auth_retry_time = time.time()
            self.auth_handler()

    def _auth_check(self):
        while not self._stop:
            # Private channelの認証が完了していない　& 前回のチャレンジから1分以上経過で再トライ
            if self.auth_retry_time+60 < time.time() and not self.auth_completed:
                self.auth_retry = 1
                self.auth_retry_time = time.time()
                self.auth_handler()
            time.sleep(10)

    def stop(self):
        self._stop = True