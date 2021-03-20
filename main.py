import os
import datetime as dt
import coinbase_pro_stats
import notifications

if __name__ == "__main__":
    statTracker = coinbase_pro_stats.CoinbaseProStats(
        key=os.environ["COINBASE_KEY"], passphrase=os.environ["COINBASE_PASSPHRASE"], b64secret=os.environ["COINBASE_SECRET"])

    product_stats = statTracker.get_account_stats_in_range(
        start_range=dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=365),
        end_range=dt.datetime.now(dt.timezone.utc),
        products=["BTC-USD", "ETH-USD", "LTC-USD"]
    )

    for product_stat in product_stats:
        notifications.create_stat_notification(product_stat)
