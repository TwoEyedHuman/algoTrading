from ib.opt import Connection, message
from ib.ext.Contract import Contract
from ib.ext.Order import Order
import time
from ib.opt import ibConnection
import psycopg2 as psql
from yahoo_fin import stock_info as si
import numpy as np
import datetime as dt
import collections
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger('requests').setLevel(logging.ERROR)

MARKET_OPEN = dt.time(9,30)
MARKET_CLOSE = dt.time(16,00)

StockPrice = collections.namedtuple('StockPrice', 'ticker price')

def is_time_between(begin_time, end_time, check_time=None):
    # checks if the check_time is between two times
    # begin_time : starting period of time check
    # end_time : ending period of time check
    # check_time : time that we are checking

    # if check time is not given, default to current time
    check_time = check_time or dt.datetime.now()
    if begin_time < end_time:
        return check_time >= begin_time and check_time <= end_time
    else: # crosses midnight
        return check_time >= begin_time or check_time <= end_time

def connect():
    # connect to the database and build a cursor and connection

    # build the connection and cursor objects
    conn = psql.connect(user="user", password="", host="localhost", port="5432", database="trading")
    cur = conn.cursor()
    
    return cur, conn


def get_volatile_stocks(cur, conn, cnt=1):
    # pulls the top cnt most volatile stocks from last trading day
    # cur : cursor
    # conn : connection
    # cnt : number of tickers to pull

    sqlStrParam = """
        select sl.symb
        from (
            select symb,
                stddev_pop(price)/avg(price) as cov
            from prices
            --where date(ts) = %s
            where date(ts) = '2019-07-02'
            group by 1
        ) as sl
        order by sl.cov desc
        --limit %s
        limit 3
    """
    yesterday = dt.datetime.now() - dt.timedelta(days=1)
    
    cur.execute(sqlStrParam, (yesterday.strftime('%Y-%m-%d'), cnt))
    
    return [symb[0] for symb in cur.fetchall()]


def make_contract(ticker, sec_tp, exch, prim_exch, curr):
    Contract.m_symbol = ticker
    Contract.m_secType = sec_tp
    Contract.m_exchange = exch
    Contract.m_primaryExch = prim_exch
    Contract.m_currency = curr
    return Contract


def make_order(action, quantity, price = None):
    if price is not None:
        order = Order()
        order.m_orderType = 'LMT'
        order.m_totalQuantity = quantity
        order.m_action = action
        order.m_lmtPrice = price

    else:
        order = Order()
        order.m_ordertype = 'MKT'
        order.m_totalQuantity = quantity
        order.m_action = action

    return order

class Downloader(object):

    def __init__(self, v = False):
        # initialize the Downloader object
        # v : boolean indicating if functions should be verbose

        self.tws = ibConnection('localhost', 7496, 999)  # object containing connection to API
        self.tws.register(self.tick_price_handler, 'TickPrice')  # dictates what return messages shold be processed
        self.tws.connect()  # initiates connection to API
        self._reqId = 1  # request ID
        self._oid = 1  # order ID
        self._tick_field_tp = 0
        self.stay_connect = True
        self.field_price = None
        self._verbose = v
        self.vs = None

    def tick_price_handler(self, msg):
        # extracts the price from message
        # msg : information returned form the TWS API

        if self._verbose:
            print("[debug] [tick_price_handler]: Received %s" % str(msg))
        if msg.field == self._tick_field_tp:  # https://interactivebrokers.github.io/tws-api/tick_types.html
            self.field_price = msg.price
        elif msg.field == 66:
            self.field_price = msg.price

    def request_price(self, contract, mkt_data_tp=1, tick_field_tp = 68):
        # request price information for a security
        # contract : contract of the order, containsss ticker and exchange information
        # tick_field_tp : field number of the ticker price that we want to pull
        # mkt_data_tp: determines the type of price data to return. For more information, 1 (real-time), 2 (frozen), 3 (delayed), 4 (delayed, frozen)  https://interactivebrokers.github.io/tws-api/classIBApi_1_1EClient.html#ae03b31bb2702ba519ed63c46455872b6

        self.tws.reqMarketDataType(mkt_data_tp)
        self.tws.reqMktData(self._reqId, contract, '', 0)
        self._reqId += 1    
        self._tick_field_tp = tick_field_tp

    def debugHandler(self, msg):
        # debug the returned values from the TWS API
        # msg : information returned from the TWS API

        print("[debug]", msg)

    def placeOrder(self, oid, cont, offer):
        # place an order to buy or sell a security
        # oid : order ID
        # cont : contract of the order, contains ticker and exchange information
        # offer : offer of the order, contains price and volume information

        self.tws.placeOrder(oid, cont, offer)

    def disconnect(self):
        # remove connection to the TWS API
        self.tws.disconnect()
        self.stay_connect = False

    def set_volatile_stocks(self, cnt=1):
        cur, conn = connect()

        sqlStrParam = """
            select sl.symb
            from (
                select symb,
                    stddev_pop(price)/avg(price) as cov
                from prices
                --where date(ts) = %s
                where date(ts) = '2019-07-02'
                group by 1
            ) as sl
            order by sl.cov desc
            --limit %s
            limit 3
        """
        yesterday = dt.datetime.now() - dt.timedelta(days=1)
        
        cur.execute(sqlStrParam, (yesterday.strftime('%Y-%m-%d'), cnt))
        
        vol_symbs = [symb[0] for symb in cur.fetchall()]

        self.vs = []
        for symb in vol_symbs: 
            self.vs.append(StockPrice(ticker = symb, price = si.get_live_price(symb)))
            

    def threshold_trade(self, ticker, min_val, max_val, vol, sec_tp = "STK", exch = "SMART", prim_exch = "SMART", curr = "USD"):
        # buy and sell a stock anytime it goes under a price or above a different price, respectively
        # ticker : ticker symbol of the security
        # min_val : lower bound on the threshold
        # max_val : higher bound on the threshold
        # vol : number of shares to exchange
        # sec_tp : security type (stock, bond, etc.)
        # exch : exchange
        # prim_exch : primary exchange
        # curr : currency of the order

        contract = make_contract(ticker, sec_tp, exch, prim_exch, curr)

        try:
            self.request_price(contract, mkt_data_tp = 3)  # set the variable self.field_price equal to the current quote price
            time.sleep(2)  # allow time for the server to respond

            # if the stock is less than some quality threshold, do nothing
            if self.field_price < 1:
                print("[info] [%s] [$%.2f] Price for %s below data quality threshold. No action." % (time.strftime("%H:%M"), self.field_price, contract.m_symbol))

            # if the stock price is less than our threshold, buy
            elif self.field_price < min_val:
                print("[info] [%s] [$%.2f] Price for %s below threshold. Buying." % (time.strftime("%H:%M"), self.field_price, contract.m_symbol))
                offer = make_order("BUY", vol, min_val)
                self.placeOrder(self._oid, contract, offer)
                self._oid += 1

            # if the stock price is greater than our threshold, sell
            elif self.field_price > max_val:
                print("[info] [%s] [$%.2f] Price for %s above threshold. Selling." % (time.strftime("%H:%M"), self.field_price, contract.m_symbol))
                offer = make_order("SELL", vol, max_val)
                self.placeOrder(oid, contract, offer)
                oid += 1

            else:
                print("[info] [%s] [$%.2f] Price for %s inside threshold. Holding." % (time.strftime("%H:%M"), self.field_price, contract.m_symbol))

        except Exception as e:
            print("[debug] Issue requesting price.")
            print(e)
            self.disconnect()
            self.stay_connect = False

            

if __name__ == "__main__":
    dl = Downloader()

    stock_set = False
    while not stock_set:
        if is_time_between(MARKET_OPEN, MARKET_CLOSE, dt.datetime.now().time()):
            dl.set_volatile_stocks(1)
            stock_set = True
        time.sleep(600)

    while dl.stay_connect:
        if is_time_between(MARKET_OPEN, MARKET_CLOSE, dt.datetime.now().time()):
            for vs in dl.vs:
                dl.threshold_trade(vs.ticker, vs.price*0.98, vs.price/0.98, 1)
            time.sleep(600)
