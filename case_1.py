import requests as r
import time
import multiprocessing

from dotenv import load_dotenv
import os

load_dotenv()

ritKey = os.getenv('RITKEY')
API_KEY = {'X-API-key': ritKey}


case = 'http://localhost:9999/v1/case'
order = "http://localhost:9999/v1/orders"
orderLimt = 5


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


numberOfOrders = 0
totalSpeedBumps = 0
# Speedbump function


def speedBump(transactionTime):
    global totalSpeedBumps
    global numberOfOrders

    orderSpeedBump = -transactionTime + 1/orderLimt

    totalSpeedBumps += orderSpeedBump

    numberOfOrders += 1
    sleep = totalSpeedBumps / numberOfOrders
    time.sleep(sleep)


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


# Test for market crossing opportunities
def arbitrageTest(bidDic, askDic, s, maxQuant, minSpread, tCosts, orderType):
    start = time.time()
    bid = bidDic['price']
    ask = askDic['price']
    bidQ = bidDic['quantity']
    askQ = askDic['quantity']
    bidN = bidDic['ticker']
    askN = askDic['ticker']
    # Dynamnic order size logic
    q = min(bidQ, askQ, maxQuant)
    if bid-ask-(tCosts*2) > minSpread:
        temp = s.post(order, params={
            'ticker': askN, 'type': orderType, 'quantity': q, 'action': 'BUY'})
        s.post(order, params={
            'ticker': bidN, 'type': orderType, 'quantity': q, 'action': 'SELL'})
        print('order executed')
        if temp.ok:
            transactionTime = time.time() - start
            speedBump(transactionTime)


# Main function
def main():
    with r.Session() as s:
        flag = True
        s.headers.update(API_KEY)
        maxQuant = 2000
        minSpread = 0.01
        tCosts = 0
        orderType = 'MARKET'
        # minSpread = 0.01
        while flag:
            flag = caseStatus(s)
            crzyMBid, crzyMAsk = getOrderBook(s, 'CRZY_M')
            crzyABid, crzyAAsk = getOrderBook(s, 'CRZY_A')
            # Test for cross profitability
            arbitrageTest(crzyMBid, crzyAAsk, s, maxQuant,
                          minSpread, tCosts, orderType)
            # Test for cross profitability
            arbitrageTest(crzyABid, crzyMAsk, s, maxQuant,
                          minSpread, tCosts, orderType)
            print('monitoring')


num_processes = 8
if __name__ == '__main__':
    # Start 10 instances of the script
    processes = []
    for i in range(num_processes):
        p = multiprocessing.Process(target=main)
        processes.append(p)
        p.start()

    # Wait for all processes to finish
    for p in processes:
        p.join()
