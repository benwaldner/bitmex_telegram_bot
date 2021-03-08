import requests
import pandas as pd
import json
from bitmex_websocket import BitMEXWebsocket
from time import sleep

pd.set_option('display.max_columns', None)


def funding_rate_sma(base_ticker, period):
    url = f'https://www.bitmex.com/api/v1/funding'
    params = {'symbol': f'{base_ticker}:nearest',
              'count': f'{period}',
              'reverse': 'true'}
    response = requests.get(url, params=params)
    df = pd.DataFrame(json.loads(response.text))
    # print(json.loads(response.text))
    print(df)


def websocket_trigger(base_ticker, ticker, sma_period):
    ws = BitMEXWebsocket(endpoint=f'wss://www.bitmex.com/realtime', symbol=f'{ticker}')

    while ws.ws.sock.connected:
        # print(ws.get_instrument())
        snapshot = ws.get_instrument()
        data = {'fundingRate': snapshot['fundingRate'],
                'fundingTimestamp': snapshot['fundingTimestamp'],
                'fundingInterval': snapshot['fundingInterval'],
                'indicativeFundingRate': snapshot['indicativeFundingRate']}
        funding_rate_sma(base_ticker, sma_period)
        print(data)
        sleep(2)


if __name__ == '__main__':
    websocket_trigger('ETH', 'ETHUSD', 21)


