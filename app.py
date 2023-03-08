import requests as r
import time
import multiprocessing

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
    if status == 'ACTIVE' and tick != 299:
        return True

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
            arbitrageTest(crzyMBid, crzyAAsk, crzyABid, s, minSpread)
            # Test for cross profitability
            arbitrageTest(crzyABid, crzyMAsk, crzyMBid, s, minSpread)
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
