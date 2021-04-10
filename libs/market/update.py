# coding: utf-8
#!/usr/bin/python3

import time
import traceback

# 指定間隔アップデートされていなければ登録された update_handler を使って取得する基底クラス
class market_info():
    def __init__(self, logger, interval):
        self._logger = logger
        self._interval = interval

    def _update(self, target):
        while target['update_time']+self._interval<time.time() :
            try:
                target['update_handler']()
            except Exception as e:
                self._logger.error("Error while getting {} : {}, {}".format(target['name'], e, traceback.print_exc()))
                if target['price'] != 0:
                    break
                time.sleep(10)

    def _get_price(self, target):
        self._update(target)
        return target['price']

