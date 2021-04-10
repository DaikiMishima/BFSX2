# coding: utf-8
#!/usr/bin/python3

# 板情報を管理するクラス
# bitmex / Btcmex / bybit(sign=-1)
class BoardInfoTypeB(object):

    def _insert(self, data, sign=1):
        board_list = []
        with self._lock:
            for d in data:
                sd, key, side = self._sd_and_key(d)
                price, size = d['price'], d['size']
                sd[key*sign] = [float(price), float(size)/float(price)]
                board_list.append({'price':float(price), 'size':float(size)/float(price), 'side':side})
        return board_list

    def _insert_usd(self, data, sign=1):
        board_list = []
        with self._lock:
            for d in data:
                sd, key, side = self._sd_and_key(d)
                price, size = d['price'], d['size']
                sd[key*sign] = [float(price), float(size)]
                board_list.append({'price':float(price), 'size':float(size), 'side':side})
        return board_list

    def _change(self, data, sign=1):
        board_list = []
        with self._lock:
            for d in data:
                sd, key, side = self._sd_and_key(d)
                e = sd.get(key*sign,[0,0])
                e[1] = float(d['size']) / e[0] if e[0]!=0 else d['price']
                board_list.append({'price':e[0], 'size':e[1], 'side':side})
        return board_list

    def _change_usd(self, data, sign=1):
        board_list = []
        with self._lock:
            for d in data:
                sd, key, side = self._sd_and_key(d)
                e = sd.get(key*sign,[0,0])
                e[1] = float(d['size'])
                board_list.append({'price':e[0], 'size':e[1], 'side':side})
        return board_list

    def _delete(self, data, sign=1):
        board_list = []
        with self._lock:
            for d in data:
                sd, key, side = self._sd_and_key(d)
                del_pop = sd.pop(key*sign, None)
                if del_pop:
                    board_list.append({'price': del_pop[0], 'size': 0, 'side': side})
        return board_list

    def _sd_and_key(self, data):
        if data['side'] == 'Buy':
            return self._bids, data['id'], 'BUY'
        else:
            return self._asks, -data['id'], 'SELL'

