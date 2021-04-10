# coding: utf-8
#!/usr/bin/python3

# 板情報を管理するクラス
class BoardInfoTypeA(object):
    def _update_bids(self, d):
        with self._lock:
            board_list = self._update(self._bids, d, -1)
        return board_list

    def _update_asks(self, d):
        with self._lock:
            board_list = self._update(self._asks, d, 1)
        return board_list

    def _update(self, sd, d, sign):
        board_list = []
        for i in d:
            if type(i)==dict :
                p, s = float(i['price']), float(i['size']) # binance/GMO
            else:
                p, s = float(i[0]), float(i[1])          # bitflyer/FTX/Coinbase/Kraken/Phemex
            if s == 0:
                s = sd.pop(p * sign, [0,0])[1]
            else:
                sd[p * sign] = [p, s]
            side = 'BUY' if sign == -1 else 'SELL'
            board_list.append({'price':p, 'size':s, 'side':side})
        return board_list
