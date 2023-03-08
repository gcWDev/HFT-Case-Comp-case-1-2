import requests
import time

API_KEY = {'X-API-key': 'VODJA2CQ'}

# Retrieves Session Status Of Trading Simulation
def get_status(s):
    resp = s.get('http://localhost:9999/v1/case')
    if resp.ok:
        case = resp.json()
        if case['status'] == 'ACTIVE':
            return True
        else:
            return False

# Retrieves List Of Tender And Returns JSON Object Containing A List Of All Tenders
def get_tender(s):
    resp = s.get('http://localhost:9999/v1/tenders')
    if resp.ok:
        tenders = resp.json()
        return tenders

# Retrieves Book Orders And Returns JSON Object Containing Bids and Asks On A Given Ticker
def get_book(s, ticker):
    payload = {'ticker': ticker}
    resp = s.get('http://localhost:9999/v1/securities/book',params=payload)
    if resp.ok:
        return resp.json()

# Retrieves Of Portfolio Securities and Return JSON Object Containing All Different Securities
def get_securities(s):
    resp = s.get('http://localhost:9999/v1/securities')
    if resp.ok:
        return resp.json()

def tender_logic(s,action,book):
    

    
    return

# Reads A Tender Offer And Logically Decides If Trade Should be Executed
def execute_tender(s, tender):
    book = get_book(s,tender['ticker'])
    match tender['action']:
        case 'BUY':
            if tender['price'] < book['asks'][0]['price']:
                resp = s.post('http://localhost:9999/v1/tenders/'+str(tender['tender_id']))
                
        case 'SELL':
            if tender['price'] > book['bids'][0]['price']:
                resp = s.post('http://localhost:9999/v1/tenders/'+str(tender['tender_id']))
    if resp.ok:
        return resp.json()['quantity']

# Takes Ticker and Current Position Data To Unload A Security Based On Criteria
def exit_position(s,ticker,position):
    while position != 0:
        trade_quantity = 0
        if position < 0:
            bidask = 'asks'
            action = 'BUY'
            if trade_quantity < position:
                trade_quantity = position * -1
        else:  
            bidask = 'bids' 
            action = 'SELL'
            if trade_quantity > position:
                trade_quantity = position

        book = get_book(s, ticker)
        trade_quantity = book[bidask][0]['quantity']*0.5


        payload = {'ticker': ticker,'type': 'LIMIT','quantity': trade_quantity,'action': action,'price': book[bidask][0]['price']}
        s.post('http://localhost:9999/v1/orders',params=payload)
        # Update 
        position = position - trade_quantity

def tender_process(s):
    tender = get_tender(s)
    if tender:  # if tender offer contains orders operate on those orders
        for i in tender:  # Operate on each dictionary
            execute_tender(s,i)
            time.sleep(1)
                    
        portfolio = get_securities(s)
        for i in portfolio:
            if i['position'] != 0:
                exit_position(s, i['ticker'],i['position'])

# Generic Buy Order Submission Helper Method
def buy_security(s,ticker,price):
    payload = {'ticker': ticker,'type': 'LIMIT','quantity': 1000,'action': 'BUY','price': price}
    s.post('http://localhost:9999/v1/orders',params=payload)

# Generic Sell Order Submission Helper Method
def sell_security(s,ticker,price):
    payload = {'ticker': ticker,'type': 'LIMIT','quantity': 1000,'action': 'SELL','price': price}
    s.post('http://localhost:9999/v1/orders',params=payload)

# Arbitrage Logic And Execution
def arb_process(s,ticker1,ticker2):
    book1 = get_book(s,ticker1)
    book2 = get_book(s,ticker2)
    if book1['bids'][0]['price'] > book2['asks'][0]['price']:
        buy_security(s,ticker1,book1['bids'][0]['price'])
        sell_security(s,ticker2,book2['asks'][0]['price'])
    if book2['bids'][0]['price'] > book2['asks'][0]['price']:
        buy_security(s,ticker1,book2['bids'][0]['price'])
        sell_security(s,ticker2,book1['asks'][0]['price'])


def main():
    # Initiates A Session To Be Used For Duration Of Trading Period
    with requests.Session() as s:

        s.headers.update(API_KEY)
        # Runs Loop Until Status Of Session Is No Longer Active
        status = get_status(s)
        while status:
            # Runs Tender Trading (ie Accept Tender Orders And Exit Position Over Time)
            tender_process(s)
            # Constantly Checks Status Of Simulation
            status = get_status(s)
                    


if __name__ == '__main__':
    main()