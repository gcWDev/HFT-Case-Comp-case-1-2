import requests as r
import time
import re
from dotenv import load_dotenv
import os

load_dotenv()

ritKey = os.getenv('RITKEY')

API_KEY = {'X-API-key': ritKey}

case = 'http://localhost:9999/v1/case'
order = "http://localhost:9999/v1/orders"
news = "http://localhost:9999/v1/news"
orderLimt = 5


##########String interpelation version#############


class ApiException(Exception):
    pass


# Get case status
def caseStatus(session):
    caseInfo = session.get(case)
    rDic = caseInfo.json()
    status = rDic['status']
    tick = rDic['tick']
    if status == 'ACTIVE' and tick > 1:
        return True
    else:
        time.sleep(2)
        print('Waiting')
        global totalSpeedBumps
        global numberOfOrders
        totalSpeedBumps = 0
        numberOfOrders = 0
        return caseStatus(session)


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


def getNews(session, since):
    payload = {'since': since}
    request = session.get(news, params=payload)
    if request.ok:
        return request.json()


def drawSame(actual, expected):
    length = len(actual)
    if length == 32:
        actualQuant = int(actual[20:22])*-1
    else:
        actualQuant = int(actual[22:24])*-1
    # Expected is draw
    length = len(expected)
    if length == 25:
        expectedQuant = int(expected[15:17])*-1
    else:
        expectedQuant = int(expected[15:17])*-1
    if abs(actualQuant-expectedQuant) < 5:

        print('too low')
        return False, False
    action = 'Buy' if actualQuant < expectedQuant else 'Sell'
    eiaDic = [actualQuant, expectedQuant]
    return action, eiaDic


def buildSame(actual, expected):
    # Actual is build
    length = len(actual)
    if length == 33:
        actualQuant = int(actual[21:23])
    else:
        actualQuant = int(actual[23:25])
    length = len(expected)
    # Expected is build
    if length == 25:
        expectedQuant = int(expected[15:17])
    else:
        expectedQuant = int(expected[15:18])
    if abs(actualQuant-expectedQuant) < 5:
        print('too low')
        time.sleep(1)
        return False, False
    action = 'Buy' if actualQuant < expectedQuant else 'Sell'
    eiaDic = [actualQuant, expectedQuant]
    return action, eiaDic


def eiaNews(news):
    # Extract information from EIA reports
    [actual, expected] = news.split('VS')
    dPattern = re.compile(r'DRAW')
    bPattern = re.compile(r'BUILD')
    if dPattern.search(actual) and dPattern.search(expected):
        return drawSame(actual, expected)
    if bPattern.search(actual) and bPattern.search(expected):
        return buildSame(actual, expected)
    # Handle expected EIA
    if dPattern.search(actual):
        # Actual is draw
        length = len(actual)
        if length == 33:
            actualQuant = int(actual[21:23])*-1
        else:
            actualQuant = int(actual[21:24])*-1
    else:
        # Actual is build
        length = len(actual)
        if length == 35:
            actualQuant = int(actual[22:25])
        else:
            actualQuant = int(actual[22:24])
    # Handle expected EIA
    if dPattern.search(expected):
        # Excpected is draw
        length = len(expected)
        if length == 25:
            expectedQuant = int(expected[15:17])*-1
        else:
            expectedQuant = int(expected[15:18])*-1
    else:
        # Expected is build
        length = len(expected)
        if length == 26:
            expectedQuant = int(expected[16:18])
        else:
            expectedQuant = int(expected[16:19])
    eiaDic = [actualQuant, expectedQuant]
    # print(eiaDic)
    if abs(actualQuant-expectedQuant) < 5:
        print('too low')
        time.sleep(1)
        return False, False
    action = 'Buy' if eiaDic[0] < 0 and eiaDic[1] > 0 else 'Sell'
    return action, eiaDic


def newsFilter(news, dic):
    # Filter news reports to EIA
    wPattern = re.compile(r'WEEK')
    if wPattern.search(news['headline']):
        if dic.get(news['news_id']) is None:
            return eiaNews(news['body'])
        else:
            print('Key already exists')
            time.sleep(1)
            return False, False
    else:
        print('----')
        print('non-eia')
        print('----')
        time.sleep(1)
        return False, False
        # return globalNews(s, news['body'], news['news_id'])


def getTime(s, info):
    caseInfo = s.get(case)
    rDic = caseInfo.json()
    return rDic[info]


def calculateDelta(eiaDic, s):
    # Calculate the delta of the futures
    [actual, expected] = eiaDic
    # currentPrice =
    spotDelta = (expected-actual)/10
    period = getTime(s, 'period')
    ticker = getTime(s, 'tick')
    if period == 1:
        exp = 2/12
    else:
        exp = 1/12
    futureDelta = spotDelta*((1+0.015)**exp)
    currentPrice = getOrderBook(s, 'CL-2F')[1]['price']
    return currentPrice+futureDelta

# Main function


def main():
    with r.Session() as s:
        dic = {}
        flag = True
        s.headers.update(API_KEY)
        while flag:
            flag = caseStatus(s)
            news = getNews(s, 0)
            action, eiaDic = newsFilter(news[0], dic)
            if action:
                print(action)
                exitPrice = calculateDelta(eiaDic, s)
                dic[news[0]['news_id']] = [action, f"Exit at {exitPrice}"]
                print(dic[news[0]['news_id']])
                time.sleep(10)


num_processes = 8
if __name__ == '__main__':
    main()


# testArr = ["WEEK 6 CL ACTUAL DRAW 99 MLN BBLS VS FORECAST DRAW 99 MLN BBLS",
#            "WEEK 6 CL ACTUAL DRAW 99 MLN BBLS VS FORECAST DRAW 9 MLN BBLS",
#            "WEEK 6 CL ACTUAL DRAW 99 MLN BBLS VS FORECAST BUILD 99 MLN BBLS",
#            "WEEK 6 CL ACTUAL DRAW 99 MLN BBLS VS FORECAST BUILD 9 MLN BBLS",
#            "WEEK 6 CL ACTUAL DRAW 9 MLN BBLS VS FORECAST DRAW 99 MLN BBLS",
#            "WEEK 6 CL ACTUAL DRAW 9 MLN BBLS VS FORECAST DRAW 9 MLN BBLS",
#            "WEEK 6 CL ACTUAL DRAW 9 MLN BBLS VS FORECAST BUILD 99 MLN BBLS",
#            "WEEK 6 CL ACTUAL DRAW 9 MLN BBLS VS FORECAST BUILD 9 MLN BBLS",
#            "WEEK 6 CL ACTUAL BUILD 99 MLN BBLS VS FORECAST DRAW 99 MLN BBLS",
#            "WEEK 6 CL ACTUAL BUILD 99 MLN BBLS VS FORECAST DRAW 9 MLN BBLS",
#            "WEEK 6 CL ACTUAL BUILD 99 MLN BBLS VS FORECAST BUILD 99 MLN BBLS",
#            "WEEK 6 CL ACTUAL BUILD 99 MLN BBLS VS FORECAST BUILD 9 MLN BBLS",
#            "WEEK 6 CL ACTUAL BUILD 9 MLN BBLS VS FORECAST DRAW 99 MLN BBLS",
#            "WEEK 6 CL ACTUAL BUILD 9 MLN BBLS VS FORECAST DRAW 9 MLN BBLS",
#            "WEEK 6 CL ACTUAL BUILD 9 MLN BBLS VS FORECAST BUILD 99 MLN BBLS",
#            "WEEK 6 CL ACTUAL BUILD 9 MLN BBLS VS FORECAST BUILD 9 MLN BBLS"]

# temp = []

# for i in range(len(testArr)):
#     news = [
#         {
#             "news_id": i,
#             "period": 0,
#             "tick": 0,
#             "ticker": "string",
#             "headline": "WEEK",
#             "body": testArr[i]
#         }
#     ]
#     temp.append(newsFilter(news[0]))


# print(temp)

# [(False, False),
#  ('Buy', [99, 9], 'G'),
#  ('Buy', [-99, 99], 'G'),
#  ('Buy', [-99, 9], 'G'),
#  ('Sell', [9, 99], 'G'),
#  (False, False),
#  ('Buy', [-9, 99]),
#  ('Buy', [-9, 9]),
#  ('Sell', [99, -99]),
#  ('Sell', [99, -9]),
#  (False, False),
#  ('Sell', [-99, -9]),
#  ('Sell', [9, -99]),
#  ('Sell', [9, -9]),
#  ('Buy', [-9, -99]),
#  (False, False)]


# [(False, False),
#  ('Sell', [-99, -9]),
#  ('Buy', [-99, 99]),
#  ('Buy', [-99, 9]),
#  ('Buy', [-9, -99]),
#  (False, False),
#  ('Buy', [-9, 99]),
#  ('Buy', [-9, 9]),
#  ('Sell', [99, -99]),
#  ('Sell', [99, -9]),
#  (False, False),
#  ('Buy', [99, 9]),
#  ('Sell', [9, -99]),
#  ('Sell', [9, -9]),
#  ('Sell', [9, 99]),
#  (False, False)]
