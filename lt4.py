import requests as r
import time

API_KEY = {'X-API-key': 'C98IF93B'}

case = 'http://localhost:9999/v1/case'
order = "http://localhost:9999/v1/orders"


class ApiException(Exception):
    pass


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
        return caseStatus(session)


def deleteOrderBook(session, ticker):
    pass


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


def arbitrageTest(bidDic, askDic, s, minSpread):
    bid = bidDic['price']
    ask = askDic['price']
    bidQ = bidDic['quantity']
    askQ = askDic['quantity']
    bidN = bidDic['ticker']
    askN = askDic['ticker']
    q = min(bidQ, askQ, 10000)
    if bid-ask > minSpread:
        print(f"Buy {bidN} @ {ask}\n sell {askN} @ {bid}")
        time.sleep(4)


def main():
    with r.Session() as s:
        flag = True
        s.headers.update(API_KEY)
        minSpread = 0.05
        book = 'http://localhost:9999/v1/securities/book'
        while flag:
            flag = caseStatus(s)
            crzyMBid, crzyMAsk = getOrderBook(s, 'CRZY_M', book)
            crzyABid, crzyAAsk = getOrderBook(s, 'CRZY_A', book)
            tameMBid, tameMAsk = getOrderBook(s, 'TAME_M', book)
            tameABid, tameAAsk = getOrderBook(s, 'TAME_A', book)
            # Test for cross profitability
            arbitrageTest(crzyABid, crzyMAsk, s, minSpread)
            # Test for cross profitability
            # arbitrageTest(crzyABid, crzyMAsk, s, minSpread)
            # # Test for cross profitability
            # arbitrageTest(tameMAsk, tameABid, s, minSpread)
            # # Test for cross profitability
            # arbitrageTest(tameAAsk, tameMBid, s, minSpread)
            print('monitoring')


main()
