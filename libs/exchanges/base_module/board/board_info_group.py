# coding: utf-8
#!/usr/bin/python3

from itertools import groupby
from libs.exchanges.base_module.board.board_info import BoardInfo

# BoardInfoにサイズごとのグルーピング機能を追加した拡張クラス
class BoardInfoGroup(BoardInfo):

    # splitsizeごとに板を分割して値段リストを算出
    def get_size_group(self, splitsize, limitprice=1000000, limitnum=5, startprice=0):

        try:
            with self._lock:
                total = 0
                asks_pos = []
                for price, size in self.asks:
                    if price > startprice or startprice == 0:
                        if startprice == 0:
                            startprice = price
                        total += size
                        if total > splitsize :
                            asks_pos.append( price )
                            if len(asks_pos)>=limitnum :
                                break
                            total -= splitsize
                        if price > startprice+limitprice:
                            break
                total = 0
                bids_pos = []
                for price, size in self.bids:
                    if price < startprice or startprice == 0:
                        if startprice == 0:
                            startprice = price
                        total += size
                        if total > splitsize :
                            bids_pos.append( price )
                            if len(bids_pos)>=limitnum :
                                break
                            total -= splitsize
                        if price < startprice-limitprice:
                            break
        except Exception as e:
            return {'ask': [self.mid]*limitnum, 'bid': [self.mid]*limitnum}

        if len(bids_pos)==0 : bids_pos = [self.mid]*limitnum
        if len(asks_pos)==0 : asks_pos = [self.mid]*limitnum

        return {'ask': asks_pos, 'bid': bids_pos}

    # splitsizeごとに板を分割して値段リストを算出
    def get_price_group(self, splitprice):

        mid = self.mid
        with self._lock:
            asks_group = [sum([i['size'] for i in items]) for index, items in groupby([{'group':int((b[0]-mid)/splitprice), 'size':b[1]} for b in self.asks], key=lambda x: x['group'])]
            bids_group = [sum([i['size'] for i in items]) for index, items in groupby([{'group':int((b[0]-mid)/splitprice), 'size':b[1]} for b in self.bids], key=lambda x: x['group'])]
        if len(asks_group)==0 : asks_group=[0]
        if len(bids_group)==0 : bids_group=[0]

        return {'ask': asks_group, 'bid': bids_group}

