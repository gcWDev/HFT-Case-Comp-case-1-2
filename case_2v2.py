import requests as r
import time
import re
import openai
from dotenv import load_dotenv
import os

load_dotenv()

ritKey = os.getenv('RITKEY')
openAiKey = os.getenv("OPENAIKEY")

API_KEY = {'X-API-key': ritKey}

case = 'http://localhost:9999/v1/case'
order = "http://localhost:9999/v1/orders"
news = "http://localhost:9999/v1/news"
orderLimt = 5

##########Openai version#############


openai.api_key = openAiKey


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


def eiaNews(news, dic):
    # Use chat gpt to determine wether news will positivly impact oil prices or not
    body = news['body']
    id = news['news_id']
    if id not in dic:
        messageHistory = [
            {
                "role": "system",
                "content": "For the given news, respond with the string 'meh' if the absolute difference between the expected and actual value is less than 5. Otherwise reply 1 for CL oil price increase, 0 for decrease. Only reply with a number, no text."
            },
            {
                "role": "user",
                "content": body
            }
        ]
        completion = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messageHistory
        )
        answer = {id: completion.choices[0].message.content}
        return answer
    print('item already exists')
    time.sleep(4)
    return False


def newsFilter(news, dic):
    wPattern = re.compile(r'WEEK')
    if wPattern.search(news['headline']):
        return eiaNews(news, dic)
    else:
        print('non-eia')
        time.sleep(1)
        return False
        # return globalNews(s, news['body'], news['news_id'])


def main():
    with r.Session() as s:
        dic = {}
        flag = True
        s.headers.update(API_KEY)
        while flag:
            flag = caseStatus(s)
            news = getNews(s, 0)
            temp = newsFilter(news[0], dic)
            if temp:
                dic[news[0]["news_id"]] = temp
                print(dic)
                time.sleep(10)


num_processes = 8
if __name__ == '__main__':
    main()
