# coding: utf-8
#!/usr/bin/python3

from collections import deque
import requests
import time

# Discordへの送信を行うクラス
class NotifyDiscord(object):
    def __init__(self, logger, webhook=''):
        self._logger = logger
        self.webhook = webhook
        self._message = deque()

    def send(self, message, image_file=None):
        try:
            if self.webhook != '':
                payload = {'content': ' {} '.format(message)}
                if image_file == None:
                    r = requests.post(self.webhook, data=payload, timeout=10)
                else:
                    try:
                        file = {'imageFile': open(image_file, "rb")}
                        r = requests.post(self.webhook, data=payload, files=file, timeout=10)
                    except:
                        r = requests.post(self.webhook, data=payload, timeout=10)
                if r.status_code == 204:
                    # 正常終了
                    return
                elif r.status_code == 404:
                    self._logger.error('Discord URL is not exist')
        except Exception as e:
            self._logger.error('Failed sending image to Discord: {}'.format(e))
            time.sleep(1)

    def add_message(self, msg):
        self._message.append(msg)

    def flush_message(self):
        str = ""
        while len(self._message)!=0 :
            mes = self._message.popleft()
            if len(str)+len(mes)>1900 :
                self.send(str)
                str = mes
            else:
                str = str + '\n' + mes
        if len(str)!=0:
            self.send(str)



