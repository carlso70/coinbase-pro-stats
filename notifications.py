from plyer import notification
import utils


def generate_product_stats_notification_message(product_stat: dict):
    utils.check_product_stat_dict(product_stat)
    return f"""
    over all cost: {product_stat["over_all_cost"]}
    total returns: {product_stat["total_returns"]}
    balance: {product_stat["balance"]}
    current price: {product_stat["current_price"]}
    """


def create_stat_notification(product_stat: dict):
    if "product" not in product_stat:
        raise "Missing key product in product stat"

    notification.notify(
        title=f"{product_stat['product']}",
        message=generate_product_stats_notification_message(product_stat),
        app_icon=None,  # e.g. 'C:\\icon_32x32.ico'
        timeout=30,  # seconds
    )
