import numpy
import requests
from bitmex_websocket import BitMEXWebsocket
from time import sleep


def send_telegram(token, chat_id, msg):
    url = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={msg}&parse_mode=html'
    requests.get(url)


def bitmex_funding_rate_trigger(ticker, sma_period, anomaly_threshold_percent, telegram_token, telegram_chat_id,
                                bearish_bias_msg, bullish_bias_msg):
    last_anomaly = 0.0
    ws = BitMEXWebsocket(endpoint=f'wss://www.bitmex.com/realtime', symbol=f'{ticker}')
    rolling_data_set = []
    i = 0
    if ws.ws.sock.connected:
        print('Connected to Bitmex Websocket. Starting stream.')
    while ws.ws.sock.connected:
        snapshot = ws.get_instrument()
        data = {'fundingRate': snapshot['fundingRate'],
                'fundingTimestamp': snapshot['fundingTimestamp'],
                'fundingInterval': snapshot['fundingInterval'],
                'indicativeFundingRate': snapshot['indicativeFundingRate'],
                'symbol': snapshot['symbol'],
                'price': snapshot['markPrice']}
        # print(snapshot['indicativeFundingRate'])
        if i < sma_period:
            rolling_data_set.append(data['indicativeFundingRate'])
            i = i + 1
        else:
            diff = data['indicativeFundingRate'] - numpy.mean(rolling_data_set)
            # check if rolling average has a negative spike
            if diff < 0 and abs(diff / numpy.mean(rolling_data_set)) > anomaly_threshold_percent / 100:
                # Send Telegram message based Rolling average
                msg = f'ticker: {ticker}\nprice: {data["price"]}\nCurrent funding rate: {data["indicativeFundingRate"] * 100}%\nMean funding rate: {numpy.mean(rolling_data_set) * 100}%\n' \
                      f'Spike %: {abs(diff / numpy.mean(rolling_data_set)) * 100} below average\n<b>{bullish_bias_msg}</b> '
                if data['indicativeFundingRate'] != last_anomaly:
                    send_telegram(f'{telegram_token}', telegram_chat_id, msg)
                    last_anomaly = data['indicativeFundingRate']
            # check if rolling average has a positive spike
            elif diff > 0 and abs(diff / numpy.mean(rolling_data_set)) > anomaly_threshold_percent / 100:
                # Send Telegram message based Rolling average
                msg = f'ticker: {ticker}\n price: {data["price"]}\nCurrent funding rate: {data["indicativeFundingRate"] * 100}%\nMean funding rate: {numpy.mean(rolling_data_set) * 100}%\n' \
                      f'Spike %: {abs(diff / numpy.mean(rolling_data_set)) * 100} above average\n<b>{bearish_bias_msg}</b> '
                if data['indicativeFundingRate'] != last_anomaly:
                    send_telegram(f'{telegram_token}', telegram_chat_id, msg)
                    last_anomaly = data['indicativeFundingRate']
            else:
                # Rolling data set. Discarding the oldest value and adding new value.
                rolling_data_set = rolling_data_set[1:]
                rolling_data_set.append(data['indicativeFundingRate'])
        # print(rolling_data_set)
        # sleep(2)


if __name__ == '__main__':
    bitmex_funding_rate_trigger('XBTUSD', 10000, 0.1, '<telegram_bot_token>', '<telegram_chat_id>',
                                'Bias: Bearish, please avoid longs', 'Bias: Bullish, please avoid shorts')
