"""Main module."""
import hashlib
import hmac
import json
import time, datetime
import urllib
import requests
import os
from traceback import format_exc

from urllib.parse import urlencode
try:
    access_key = os.environ.get('access_key')
    secret_key = 'get you secret code here'

except:
    f = open("log.txt", "w")
    f.write('Error key on ' + str(time.ctime()) + str(format_exc()))
    print('ошибка ключа , проверьте заполненность переменыой access_key '
          '.получить ключи API можно зарегистрировавшись на сайте kuna.io ')
    f.close()

API_VERSION = '2'
KUNA_API_URL_PREFIX = 'api/v{}'.format(API_VERSION)
KUNA_API_BASEURL = 'https://kuna.io/{}/'.format(KUNA_API_URL_PREFIX)

MARKET_PAIRS_TO_GRYVNA = ['btcuah', 'ethuah', 'xrpuah', 'ltcuah', 'dashuah', 'bchuah', 'xlmuah',
                          'eosuah', 'usdtuah', 'wavesuah']

VALID_MARKET_DATA_PAIRS = [ 'rmcbtc', 'rbtc', 'evrbtc', 'foodbtc', 'hknbtc'] + \
                          MARKET_PAIRS_TO_GRYVNA


class KunaAPI(object):
    def __init__(self, access_key=None, secret_key=None):

        self.access_key = access_key
        self.secret_key = secret_key

    def get_server_time(self):
        """
        Get the server time from server.
        :return: unix timestamp
        """
        return self.request('timestamp')

    def get_recent_market_data(self, market):
        """
        Get recent market data from server.
        :param market:
        :return:
        """
        return self.request('tickers' + '/' + market)

    def get_order_book(self, market):
        """
        Get order book data from server.
        :param market:
        :return:
        """
        args = {
            'market': market
        }
        return self.request('order_book', args=args)

    def get_trades_history(self, market):
        """
        Get trades history data from server.
        :param market:
        :return:
        """
        args = {
            'market': market
        }
        return self.request('trades', args=args)

    def get_user_account_info(self):
        """
        Information about the User and Assets.
        This is a User method.
        :return:
        """
        return self.request('members/me', is_user_method=True)

    def get_orders(self, market):
        """
        Active User Orders.
        This is a User method.
        :return:
        """
        args = {
            'market': market
        }
        return self.request('orders', args=args, is_user_method=True)

    def put_order(self, side, volume, market, price):
        """
        Order placing.
        This is a User method.
        :param side: 'buy' or 'sell'
        :param volume: volume in BTC
        :param market: option from VALID_MARKET_DATA_PAIRS
        :param price: price for 1 BTC
        :return:
        """
        args = {
            'side': side,
            'volume': volume,
            'market': market,
            'price': price
        }
        return self.request('orders', args=args, method='POST', is_user_method=True)

    def cancel_order(self, order_id):
        """
        Cancel order.
        This is a User method.
        :param order_id:
        :return:
        """
        args = {
            'id': order_id
        }
        return self.request('order/delete', args=args, method='POST', is_user_method=True)

    def get_trade_history(self, market):
        """
        User trade history
        This is a User method.
        :param market:
        :return:
        """
        args = {
            'market': market
        }
        return self.request('trades/my', args=args, is_user_method=True)

    def request(self, path, args=None, method='GET', is_user_method=False):
        """
        Fetches the given path in the Kuna API.
        We translate args to a valid query string. If post_args is
        given, we send a POST request to the given path with the given
        arguments.
        :param path:
        :param args:
        :param method:
        :param is_user_method:
        :return:
        """
        if args is None:
            args = dict()

        if is_user_method:
            args['access_key'] = self.access_key
            args['tonce'] = int(time.time() * 1000)
            args['signature'] = self._generate_signature(method, path, args)

        try:
            response = requests.request(
                method,
                KUNA_API_BASEURL + path,
                params=args)
        except requests.RequestException as e:
            response = json.loads(e.read())
            raise APIError(response)

        result = response.json()

        if result and isinstance(result, dict) and result.get('error'):
            raise APIError(result)
        elif response.status_code not in [200, 201, 202]:
            raise APIError(response.reason)
        return result

    def _generate_signature(self, method, path, args):
        """
        Signature is generated by an algorithm HEX(HMAC-SHA256("HTTP-verb|URI|params", secret_key))
        :param method:
        :param path:
        :param args:
        :return:
        """
        uri = '/' + KUNA_API_URL_PREFIX + '/' + path
        sorted_values = sorted(args.items(), key=lambda val: val[0])
        msg = method + '|' + uri + '|' + urllib.parse.urlencode(sorted_values)  # "HTTP-verb|URI|params"

        # HMAC can only handle ascii (byte) strings
        # https://bugs.python.org/issue5285
        key = self.secret_key.encode('ascii')
        msg = msg.encode('ascii')
        return hmac.new(key, msg, hashlib.sha256).hexdigest()


class APIError(Exception):
    def __init__(self, result):

        try:
            self.message = result["error"]["message"]
            self.code = result["error"].get("code")
        except:
            self.message = result

        Exception.__init__(self, self.message)





