import requests as r
import time

API_KEY = {'X-API-key': 'C98IF93B'}

# globals

case = 'http://localhost:9999/v1/case'
order = "http://localhost:9999/v1/orders"
orderLimt = 5
numberOfOrders = 0
totalSpeedBumps = 0


class ApiException(Exception):
    pass

# Get case status


def caseStatus(session):
    caseInfo = session.get(case)
    rDic = caseInfo.json()
    status = rDic['status']
    tick = rDic['tick']
    if status == 'ACTIVE' and tick != 298:
        return True

    else:
        time.sleep(2)
        print('Waiting')
        return caseStatus(session)


def speedBump(transactionTime):
    global totalSpeedBumps
    global numberOfOrders

    orderSpeedBump = -transactionTime + 1/orderLimt

    totalSpeedBumps += orderSpeedBump

    numberOfOrders += 1
    sleep = totalSpeedBumps / numberOfOrders
    print(sleep)
    time.sleep(sleep)


def deleteOrderBook(session, ticker):
    pass

# Get security order book


def getOrderBook(session, ticker, book):
    payload = {'ticker': ticker}
    resp = session.get(book, params=payload)
    try:
        if resp.ok:
            book = resp.json()
            return book['bids'][0], book['asks'][0]
        raise ApiException('Auth error, please check API key')
    except:
        caseStatus(session)

# Test for market crossing opportunities


def arbitrageTest(bidDic, askDic, s, minSpread):
    start = time.time()
    bid = bidDic['price']
    ask = askDic['price']
    bidQ = bidDic['quantity']
    askQ = askDic['quantity']
    bidN = bidDic['ticker']
    askN = askDic['ticker']
    q = min(bidQ, askQ, 5000)
    if bid-ask > minSpread:
        temp = s.post(order, params={
            'ticker': askN, 'type': 'LIMIT', 'quantity': q, 'action': 'BUY', 'price': ask+0.01})
        s.post(order, params={
            'ticker': bidN, 'type': 'MARKET', 'quantity': q, 'action': 'SELL'})
        print('Orders executed')
        if temp.ok:
            transactionTime = time.time() - start
            speedBump(transactionTime)


def main():
    with r.Session() as s:
        flag = True
        s.headers.update(API_KEY)
        book = 'http://localhost:9999/v1/securities/book'
        minSpread = 0.03
        while flag:
            flag = caseStatus(s)
            crzyMBid, crzyMAsk = getOrderBook(s, 'CRZY_M', book)
            crzyABid, crzyAAsk = getOrderBook(s, 'CRZY_A', book)
            # Test for cross profitability
            arbitrageTest(crzyMBid, crzyAAsk, s, minSpread)
            # Test for cross profitability
            arbitrageTest(crzyABid, crzyMAsk, s, minSpread)
            print('monitoring')


main()
