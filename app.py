import requests as r
import time
import multiprocessing

API_KEY = {'X-API-key': 'C98IF93B'}

# globals
# Add logic to get the average bid/ask size over the past 5 orders

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
    if status == 'ACTIVE' and tick != 299:
        return True, tick

    else:
        time.sleep(2)
        print('Waiting')
        global totalSpeedBumps
        global numberOfOrders
        totalSpeedBumps = 0
        numberOfOrders = 0
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
def getOrderBook(session, ticker):
    book = 'http://localhost:9999/v1/securities/book'
    payload = {'ticker': ticker}
    resp = session.get(book, params=payload)
    try:
        if resp.ok:
            book = resp.json()
            return book['bids'][0], book['asks'][0]
        raise ApiException('Auth error, please check API key')
    except:
        caseStatus(session)


def checkLiquidity(s, bidN, direction, test):
    book = 'http://localhost:9999/v1/securities/book'
    payload = {'ticker': bidN}
    resp = s.get(book, params=payload)
    liquidity = 0
    if resp.ok:
        book = resp.json()
        for i in range(5):
            liquidity += book[direction][i]['quantity']
    if liquidity//5 > test:
        return True
    else:
        return False


# Test for market crossing opportunities
def arbitrageTest(bidDic, askDic, altDic, s, minSpread):
    start = time.time()
    bid = bidDic['price']
    ask = askDic['price']
    bidQ = bidDic['quantity']
    askQ = askDic['quantity']
    bidN = bidDic['ticker']
    askN = askDic['ticker']
    altPrice = altDic['price']
    q = min(bidQ, askQ, 1250)
    # q = min(bidQ, askQ, 1500)
    # q = min(bidQ, askQ, 1000)
    # q = min(bidQ, askQ, 5000)
    # q = min(bidQ, askQ, 2500)
    # q = min(bidQ, askQ, 500)
    flag = checkLiquidity(s, bidN, 'bids', q)
    flag = checkLiquidity(s, askN, 'asks', q)
    if flag:
        if bid-ask > minSpread:
            # temp = s.post(order, params={
            #     'ticker': askN, 'type': 'LIMIT', 'quantity': q, 'action': 'BUY', 'price': altPrice+0.03})
            # s.post(order, params={
            #     'ticker': bidN, 'type': 'MARKET', 'quantity': q, 'action': 'SELL'})
            # print('Orders executed')
            temp = s.post(order, params={
                'ticker': askN, 'type': 'MARKET', 'quantity': q, 'action': 'BUY'})
            s.post(order, params={
                'ticker': bidN, 'type': 'MARKET', 'quantity': q, 'action': 'SELL'})
            print('Orders executed')
            if temp.ok:
                transactionTime = time.time() - start
                speedBump(transactionTime)


def intLogic(s, tick):
    bidDic, askDic = getOrderBook(s, tick)
    bid = bidDic['price']
    ask = askDic['price']
    bidQ = bidDic['quantity']
    askQ = askDic['quantity']
    bidN = bidDic['ticker']
    askN = askDic['ticker']
    temp = s.post(order, params={
        'ticker': askN, 'type': 'LIMIT', 'quantity': 1, 'action': 'BUY', 'price': bid+2})
    time.sleep(1)


def main():
    with r.Session() as s:
        flag = True
        s.headers.update(API_KEY)
        minSpread = 0.02
        while flag:
            flag, tick = caseStatus(s)
            crzyMBid, crzyMAsk = getOrderBook(s, 'CRZY_M')
            crzyABid, crzyAAsk = getOrderBook(s, 'CRZY_A')
            # Test for cross profitability
            arbitrageTest(crzyMBid, crzyAAsk, crzyABid, s, minSpread)
            # Test for cross profitability
            arbitrageTest(crzyABid, crzyMAsk, crzyMBid, s, minSpread)
            # Market destroy
            if tick % 60 == 0:
                intLogic(s, 'CRZY_M')
            print('monitoring')


if __name__ == '__main__':
    # Start 10 instances of the script
    num_processes = 10
    processes = []
    for i in range(num_processes):
        p = multiprocessing.Process(target=main)
        processes.append(p)
        p.start()

    # Wait for all processes to finish
    for p in processes:
        p.join()
