# coding: utf-8
#!/usr/bin/python3

import time
from libs.utils.jsonfile import JsonFile

# 建玉リスト管理クラス (部分クローズ時平均単価維持タイプ bybit)
class OpenPositionKeepAve(object):

    def __init__(self, logger, update_profitfile):
        self._logger = logger
        self._update_profitfile = update_profitfile

        self.average_price = 0
        self.size = 0
        self.realized = 0   # 確定済み損益
        self.commission = 0 # コミッション(makerコミッション-takerコミッション, SFDなど)
        self.ref_ltp = 0    # 含み損益計算用
        self.base_position = 0
        self.file = JsonFile(self._logger)

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = value

    def renew_posfile(self, filename):
        pos_list = self.file.reload_file(filename)
        for data in pos_list:
            self.size = data.get('size',self.size)
            self.average_price = data.get('average_price',self.average_price)

        self._logger.info( '-'*100 )
        self._logger.info( " pos_size = {} / average_price = {}".format(self.size, self.average_price)) 
        self._logger.info( '-'*100 )

    def _update_posfile(self):
        self.file.add_data({'timestamp':time.time(), 'size':self.size, 'average_price':self.average_price} )

    def execution(self, id, side='', price=0, size=0, commission=0):

#        self._logger.info( "EXECUTION: side={}, price={}, size={}, commission={}".format(side,price,size,commission) )

        self.commission = round(self.commission+commission, 8)
        if size==0 : # コミッションだけを積算させる場合
            self._update_profitfile()
            return

        exec_qty = size * (1 if side=='BUY' else -1)

        # 全クローズの場合
        if round(self.size+exec_qty,8)==0 :

            profit = self.size/self.average_price-self.size/price-0.000000005
#            self._logger.info( "EXECUTION Profit1 ={}: self.size={}, self.average_price={}, price={}".format(profit,self.size,self.average_price,price) )

            self.realized = round(self.realized+profit, 8)

            self.average_price = 0
            self.size = 0

        # 同方向のポジ増加の場合 (self.average_price は平均額に)
        elif self.size*exec_qty>=0 :
            self.average_price = (self.size*self.average_price + exec_qty*price)/(self.size+exec_qty)
            self.size += exec_qty

        # 部分約定の場合 (self.average_price は変わらない)
        elif abs(self.size)>abs(exec_qty) :

            profit = exec_qty/price-exec_qty/self.average_price-0.000000005
#            self._logger.info( "EXECUTION Profit2 ={}: exec_qty={}, price={}, self.average_price={}".format(profit,exec_qty,price,self.average_price) )
            self.realized = round(self.realized+profit, 8)

            self.size += exec_qty

        # 全クローズ＆ドテンの場合 (self.average_price は price に)
        else:
            profit = self.size/self.average_price-self.size/price-0.000000005
#            self._logger.info( "EXECUTION Profit3 ={}: self.size={}, self.average_price={}, price={}".format(profit,self.size,self.average_price,price) )
            self.realized = round(self.realized+profit, 8)

            self.average_price = price
            self.size += exec_qty

        self._update_posfile()

    @property
    def side(self):
        if round(self.size,8)==0 :
            return 'NONE'
        return 'BUY' if self.size>0 else 'SELL'
        
    # インバースタイプの損益計算 (BTC建て)
    @property
    def unreal(self):
        return round(self.size/self.average_price-self.size/self.ref_ltp, 8) if self.ref_ltp!=0 and self.size!=0 else 0

    @property
    def profit(self):
        return self.realized+self.commission+self.unreal

    @property
    def fixed_profit(self):
        return self.realized+self.commission
