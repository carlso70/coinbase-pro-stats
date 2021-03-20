import cbpro
import datetime as dt
import iso8601
from typing import List


class CoinbaseProStats:

    last_calculated: dt.datetime = None  # Used to prevent rate limit issues with the coinbase pro api
    last_stats: List[dict] = []
    stats_refresh_ttl: dt.timedelta = dt.timedelta(seconds=30)  # the time until we are allowed to fetch new stats

    def __init__(self, key: str, passphrase: str, b64secret: str):
        '''
            init CoinbaseProStats by using an api key, passphrase, and secret which can be created 
            at this link -> https://pro.coinbase.com/profile/api 
        '''
        self.auth_client = cbpro.AuthenticatedClient(key, b64secret, passphrase)

    def is_it_time_to_calculate_stats_again(self) -> bool:
        if self.last_calculated is None:
            return True

        return dt.datetime.now() - self.last_calculated < self.stats_refresh_ttl

    def calculate_cost_basis(self, fill: dict) -> float:
        '''
        given a order fill dictionary containing the keys
        {
            'price': float,
            'size': float,
            'fee': float
        }

        return the cost basis for this fill
        '''
        if "price" in fill:
            price = float(fill["price"])
        else:
            raise "Missing price in fill"

        if "size" in fill:
            size = float(fill["size"])
        else:
            raise "Missing size in fill"

        if "fee" in fill:
            fee = float(fill["fee"])
        else:
            raise "Missing fee inside fill"

        return price * size - fee

    def get_current_price_of_product(self, product) -> float:
        return float(self.auth_client.get_product_ticker(product_id=product)["price"])

    def get_balance_of_product(self, product: str) -> float:
        '''
            returns the account balance of a certain crypto product
            example products returned from api call get accounts are BTC-USD, LTC-USD, USD

            but the balance on this api returns it as BTC, LTC, USD
            so need to strip -USD
        '''

        # crypto product names have the this suffix in it
        if "-USD" in product:
            product = product.replace("-USD", "")

        for a in self.auth_client.get_accounts():
            if a["currency"] == product:
                return float(a["balance"])

        return 0.0

    def get_account_stats_in_range(self, products: List[str], start_range: dt.datetime, end_range: dt.datetime) -> List[dict]:
        '''
            returns a list of the current stats for each product passed in
            example products: ["BTC-USD", "LTC-USD", "ETH-USD"]
            example start_range = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=365)
            example end_range = dt.datetime.now(dt.timezone.utc)

            result ::
                [
                    {
                        "product": "BTC-USD",
                        "over_all_cost": 100.00,
                        "total_returns": 100000.000,
                        "balance": 0.5,
                        "current_price": 4000.00,
                        "average_price": 12345.00,
                        "average_price_sold_at": 1234.00,
                        "average_price_bought_at": 123.00
                    },
                    {
                        ...
                    }
                ]

        '''

        if not self.is_it_time_to_calculate_stats_again():
            return self.last_stats

        new_stats = []
        for product in products:
            # will make multiple http calls if necessary since paginated
            fills_gen = self.auth_client.get_fills(product_id=product)
            fills = list(fills_gen)

            '''
                fills ::
                    [
                        {
                            "trade_id": 74,
                            "product_id": "BTC-USD",
                            "price": "10.00",
                            "size": "0.01",
                            "order_id": "d50ec984-77a8-460a-b958-66f114b0de9b",
                            "created_at": "2014-11-07T22:19:28.578544Z",
                            "liquidity": "T",
                            "fee": "0.00025",
                            "settled": true,
                            "side": "buy"
                        },
                        {
                            ...
                        }
                    ]
            '''

            over_all_cost = 0.0
            total_price = 0.0
            total_price_sold_at = 0.0
            total_price_bought_at = 0.0
            fills_ct = 0  # need this since len(fills) includes open,
            buys_ct = 0
            sells_ct = 0

            for fill in fills:
                # check if fill is outside the time range
                fill_time = iso8601.parse_date(fill["created_at"])
                if fill_time > end_range or fill_time < start_range:
                    print("time out of range", fill_time)
                    pass

                # fill needs to be buy or sell for us to get stats on
                fill_side = fill["side"]
                if fill_side != "buy" or fill_side != "sell":
                    pass

                is_buy = fill_side == "buy"

                # Cost basis of fill
                cost_basis = self.calculate_cost_basis(fill)
                over_all_cost += cost_basis if is_buy else cost_basis * -1

                # fill price
                total_price += float(fill["price"]) if is_buy else float(fill["price"]) * -1
                fills_ct += 1

                # track sell price info
                total_price_sold_at += float(fill["price"]) if not is_buy else 0
                sells_ct += not is_buy

                # track buy price info
                total_price_bought_at += float(fill["price"]) if is_buy else 0
                buys_ct += is_buy

            # Get final information to build stats
            balance = self.get_balance_of_product(product)
            current_price = self.get_current_price_of_product(product)
            new_stats.append(
                {
                    "product": product,
                    "over_all_cost": over_all_cost,
                    "total_returns": current_price*balance - over_all_cost if fills_ct > 0 else 0,
                    "balance": balance,
                    "current_price": current_price,
                    "average_price": 0 if fills_ct == 0 else total_price/fills_ct,
                    "average_price_sold_at": 0 if sells_ct == 0 else total_price_sold_at / sells_ct,
                    "average_price_bought_at": 0 if buys_ct == 0 else total_price_bought_at / buys_ct
                }
            )

        # Update class variables so we don't blow our rate limit
        self.last_calculated = dt.datetime.now(dt.timezone.utc)
        self.last_stats = new_stats
        return new_stats
