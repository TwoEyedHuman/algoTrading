from ib.opt import Connection, message
from ib.ext.Contract import Contract
from ib.ext.Order import Order
import time
import psycopg2
import datetime

def make_contract(symbol, sec_type, exch, prim_exchange, curr):
    Contract.m_symbol = symbol
    Contract.m_secType = sec_type
    Contract.m_exchange = exch
    Contract.m_primaryExch = prim_exchange
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

def placeOrder(oid, cont, offer, conn, dbConn, db_conn):
    sqlStrParam = """
        insert into orders (orderId, symb, oDate, vol, avgPrice, status, filled) values (%s, %s, CURRENT_TIMESTAMP, %s, %s, 'Submitted', false);
    """

    db_conn.execute(sqlStrParam, (oid, cont.m_symbol, offer.m_totalQuantity, offer.m_lmtPrice))
    dbConn.commit()

    conn.placeOrder(oid, cont, offer)

def main():

    # establish connection to the trades database
    print("Establishing connection to database.")
    dbConn, db_conn = establishConnectionDB()

    # establish connection to TWS API
    print("Establishing connection to TWS.")
    conn = Connection.create(port=7496, clientId=999)
    conn.connect()
#    conn.register(print_open_order_message, message.openOrder)
#    conn.registerAll(error_handler)
    conn.register(error_handler, 'OrderStatus')

    # determine what stocks  to trade and at what prices/volume
    print("Building offers.")
#    cont = make_contract("AAPL", "STK", "SMART", "SMART", "USD")
#    offer = make_order("BUY", 1, 5)

    # place orders
    print("Placing orders.")
#    oid = getNewOrderId(dbConn, db_conn, 1)
#    placeOrder(oid, cont, offer, conn, dbConn, db_conn)

    # update db with the new orders

    time.sleep(1)  # allow time to display error messages

    # remove connections
    print("Closing connections.")
    conn.disconnect()  # disconnect from TWS API
    dbConn.close()  # disconnect from trading database

def error_handler(msg):
    print(msg.status)

def establishConnectionDB(dbname = "trading", user = "blocke", pword="", host = "localhost"):
    try:
        conn = psycopg2.connect(host=host,database=dbname, user=user, password=pword)
    except:
        print("Error connecting to database.")

    cur = conn.cursor()

    return conn, cur

def getNewOrderId(conn, cur, vol=1):
    sqlStr = """
        select max(orderId) as maxOrderID
        from orders
    """
    cur.execute(sqlStr)

    row = cur.fetchone()
    if row is not None:
        return row[0] + 1
    else:
        print("Error pulling new order ID.")
        return None

def print_open_order_message(msg):
    print("open_order: " + str(msg.orderId) + "::" + str(msg.contract) + "::" + str(msg.order) + "::" + str(msg.orderState))

def handleAll(msg):
    print(msg)

if __name__ == "__main__":
    print("Running main.")
    main()
