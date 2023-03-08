import requests as r
import time

# Checklist:
# 1. Add max value for position size to be 10k
# 2. Add support to currentSize
# 3. Mass order delete -> create a dictionary of all outstanding orders and the tick they were placed on, if orders are active for longer then 10 seconds, delete, track orders using order id
# 4. Test monitor speed

API_KEY = {'X-API-key': 'C98IF93B'}

case = 'http://localhost:9999/v1/case'
order = "http://localhost:9999/v1/orders"


# orderSize = input('Enter order size: ')
# orderType = input('Enter type (MARKET/LIMIT): ')
# tradingCosts = input('Enter trading costs: ')
# riskTolerance = input('Enter risk tolerance')
# orderPrice = None


# def orderChecker(order_type):
#     if orderType == 'LIMIT':
#         orderPrice = input('Enter execution price: ')
#     return orderPrice

class ApiException(Exception):
    pass


def caseStatus(session):
    caseInfo = session.get(case)
    rDic = caseInfo.json()
    status = rDic['status']
    tick = rDic['tick']
    if status == 'STOPPED':
        print('Waiting for session to begin')
        time.sleep(2)
        return caseStatus(session)
    elif status == 'PAUSE':
        print('Waiting for session to resume')
        time.sleep(2)
        return caseStatus(session)
    elif tick == 299:
        return False, rDic
    else:
        return True, rDic


def deleteOrderBook(session, ticker):
    pass


def getOrderBook(session, ticker):
    book = 'http://localhost:9999/v1/securities/book'
    payload = {'ticker': ticker}
    resp = session.get(book, params=payload)
    try:
        if resp.ok:
            book = resp.json()
            return book['bids'][0]['price'], book['asks'][0]['price'], book['bids'][0]['quantity'], book['asks'][0]['quantity']
        raise ApiException('Auth error, please check API key')
    except:
        caseStatus(session)


def marketMaker(bidDic, askDic, s, minSpread):
    bid = bidDic['price']
    ask = askDic['price']
    bidQ = bidDic['quantity']
    askQ = askDic['quantity']
    bidN = bidDic['ticker']
    askN = askDic['ticker']
    q = min(bidQ, askQ, 10000)
    if ask-bid > minSpread:
        s.post(order, params={
            'ticker': askN, 'type': 'LIMIT', 'quantity': q, 'action': 'BUY', 'price': bid})
        s.post(order, params={
            'ticker': bidN, 'type': 'LIMIT', 'quantity': q, 'action': 'SELL', 'price': ask})
        print('Orders executed')
        time.sleep(3)


def arbitrageTest(crzyMBid, crzyMAsk, crzyABid, crzyAAsk, s, currentSize):
    if crzyMBid > crzyAAsk:
        # if bid price in exchange A is higher then the ask in exchange M, arbitrage is present by buying security in exchange A and selling it in exchange M
        spread = crzyMBid-crzyAAsk
        if spread >= 0.04:
            buyResp1 = s.post(order, params={
                'ticker': 'CRZY_A', 'type': 'MARKET', 'quantity': 10000, 'action': 'BUY'})
            s.post(order, params={
                'ticker': 'CRZY_M', 'type': 'MARKET', 'quantity': 10000, 'action': 'SELL'})
            currentSize += buyResp1.json()['quantity']
        time.sleep(1)
    if crzyABid > crzyMAsk:
        # if bid price in exchange A is higher then the ask in exchange M, arbitrage is present by buying security in exchange M and selling it in exchange A
        spread = crzyABid-crzyMAsk
        if spread >= 0.04:
            buyResp2 = s.post(order, params={
                'ticker': 'CRZY_M', 'type': 'MARKET', 'quantity': 10000, 'action': 'BUY'})
            s.post(order, params={
                'ticker': 'CRZY_A', 'type': 'MARKET', 'quantity': 10000, 'action': 'SELL'})
            currentSize += buyResp2.json()['quantity']
            time.sleep(1)
    return currentSize


def orderDelete(s, dic):
    tick = dic['tick']


def main():
    with r.Session() as s:
        flag = True
        maxSize = 25000
        currentSize = 0
        s.headers.update(API_KEY)
        while flag and currentSize < maxSize:
            flag, dic = caseStatus(s)
            crzyMBid, crzyMAsk, crzyMBidQ, crzyMAskQ = getOrderBook(
                s, 'CRZY_M')
            crzyABid, crzyAAsk, crzyABidQ, crzyAAskQ = getOrderBook(
                s, 'CRZY_A')
            # print('crzy a: ', crzyABid, crzyAAsk)
            # print('crzy m: ', crzyMBid, crzyMAsk)
            currentSize = arbitrageTest(crzyMBid, crzyMAsk, crzyABid,
                                        crzyAAsk, s, currentSize)
            orderDelete(s, dic)

        print('Session is over or max volume reached')


main()
