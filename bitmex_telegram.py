import numpy
import requests
from bitmex_websocket import BitMEXWebsocket
from time import sleep


# def get_funding_rates(base_ticker, period):
#     url = f'https://www.bitmex.com/api/v1/funding'
#     params = {'symbol': f'{base_ticker}',
#               # 'count': f'{period}',
#               'reverse': 'true'}
#     response = requests.get(url, params=params)
#     df = pd.DataFrame(json.loads(response.text))
#     print(df)


def send_telegram(token, chat_id, msg):
    url = f'https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={msg}&parse_mode=html'
    requests.get(url)


def bitmex_funding_rate_trigger(ticker, sma_period, anomaly_threshold_percent, telegram_token, telegram_chat_id,
                                bearish_bias_msg, bullish_bias_msg):
    ws = BitMEXWebsocket(endpoint=f'wss://www.bitmex.com/realtime', symbol=f'{ticker}')
    rolling_data_set = []
    i = 0
    messaging = 0
    while ws.ws.sock.connected:
        snapshot = ws.get_instrument()
        data = {'fundingRate': snapshot['fundingRate'],
                'fundingTimestamp': snapshot['fundingTimestamp'],
                'fundingInterval': snapshot['fundingInterval'],
                'indicativeFundingRate': snapshot['indicativeFundingRate'],
                'symbol': snapshot['symbol']}

        if i < sma_period:
            rolling_data_set.append(data['indicativeFundingRate'])
            i = i + 1
        else:
            diff = data['indicativeFundingRate'] - numpy.mean(rolling_data_set)
            # check if rolling average has a negative spike
            if diff < 0 and abs(diff / numpy.mean(rolling_data_set)) > anomaly_threshold_percent / 100:
                # Send Telegram message based Rolling average
                msg = f'Current funding rate: {data["indicativeFundingRate"]}\nMean funding rate: {numpy.mean(rolling_data_set)}\n' \
                      f'Spike %: {abs(diff / numpy.mean(rolling_data_set)) * 100} below average\n<b>{bullish_bias_msg}</b> '
                if messaging == 1:
                    send_telegram(f'{telegram_token}', telegram_chat_id, msg)
                    messaging = 0
            # check if rolling average has a positive spike
            elif diff > 0 and abs(diff / numpy.mean(rolling_data_set)) > anomaly_threshold_percent / 100:
                # Send Telegram message based Rolling average
                msg = f'Current funding rate: {data["indicativeFundingRate"]}\nMean funding rate: {numpy.mean(rolling_data_set)}\n' \
                      f'Spike %: {abs(diff / numpy.mean(rolling_data_set)) * 100} above average\n<b>{bearish_bias_msg}</b> '
                if messaging == 1:
                    send_telegram(f'{telegram_token}', telegram_chat_id, msg)
                    messaging = 0
            else:
                # Rolling data set. Discarding the oldest value and adding new value.
                rolling_data_set = rolling_data_set[1:]
                rolling_data_set.append(data['indicativeFundingRate'])
                messaging = 1
        # print(rolling_data_set)
        # sleep(2)


if __name__ == '__main__':
    bitmex_funding_rate_trigger('ETHUSD', 10000, 500, '1581736303:AAEHCPSXQ_xnEhJezBJEY-knInNrhBkLzFg', -1001346338431,
                                'Bias: Bearish, please avoid longs', 'Bias: Bullish, please avoid shorts')
