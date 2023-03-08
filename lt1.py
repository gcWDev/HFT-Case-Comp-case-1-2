import requests as r
import time

# Checklist:
# 3. Mass order delete -> create a dictionary of all outstanding orders and the tick they were placed on, if orders are active for longer then 10 seconds, delete, track orders using order id

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
    if status == 'STOPPED':
        print('Waiting for session to begin')
        time.sleep(2)
        return caseStatus(session)
    elif status == 'PAUSE':
        print('Waiting for session to resume')
        time.sleep(2)
        return caseStatus(session)
    elif tick == 299:
        return False, tick
    else:
        return True, tick


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


def arbitrageLogic(session, spread, bid, ask, ticker, quantity):
    if spread >= 0.04:
        temp1 = session.post(order, params={'ticker': ticker, 'type': 'LIMIT',
                                            'quantity': quantity, 'action': 'BUY', 'price': bid+0.01})
        print('Buy order executed')
        session.post(order, params={'ticker': ticker, 'type': 'LIMIT',
                                    'quantity': quantity, 'action': 'SELL', 'price': ask-0.01})
        print('Sell order executed')
        print(temp1.json())
        time.sleep(1)


def clearOrders(session, orderDic, currentTick):
    if currentTick-orderDic['Tick'] > 10:
        payload = {'id': orderDic['ID']}
        temp = session.Delete(params=payload)
        if temp.ok:
            print('Order ', orderDic['ID'], ' deleted')


def main():
    with r.Session() as s:
        flag = True
        ticker = 'HAR'
        s.headers.update(API_KEY)
        while flag:
            # Get case status
            flag, tick = caseStatus(s)
            # Get orderbooks
            bid, ask, bidQ, askQ = getOrderBook(s, ticker)
            # Check for arbitrage, store orders ids as a dictionary containing time placed and ID
            arbitrageLogic(
                s, ask-bid, bid, ask, ticker, min(bidQ, askQ, 1000))
            print('monitoring')
        print('Session is over or max volume reached')


if __name__ == "__main__":
    main()
