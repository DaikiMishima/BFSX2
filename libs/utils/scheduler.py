# coding: utf-8
#!/usr/bin/python3

import time
from threading import Thread, Event
import traceback

# 定期的なイベントの呼び出しを行うクラス
class Scheduler(object):
    def __init__(self, logger, interval=1, basetime=None, callback=None, args=()):
        self._logger = logger
        self._callback = callback
        self._interval = interval
        self._args = args
        self._basetime = time.time()+9*3600 if basetime==None else basetime
        self._stop = False
        self._event = Event()
        loop_thread = Thread(target=self._main_loop)
        loop_thread.daemon = True
        loop_thread.start()
        self._logger.stop_list.append([self.stop,self._callback])

    def _main_loop(self):
        while not self._stop:
            next_time = (self._basetime-time.time()-9*3600) % self._interval
            self._event.clear()
            if self._event.wait(timeout=next_time) :
                continue
            try:
                self._callback(*self._args)
            except Exception as e:
                self._logger.error( self._callback.__name__ + ": error in scheduled job" )
                self._logger.error( e )
                self._logger.info(traceback.format_exc())

    def stop(self):
        self._stop = True

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, value):
        self._interval = value
        self._event.set()
