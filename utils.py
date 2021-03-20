

def check_product_stat_dict(product_stat: dict):
    product_stat_dict_keys = ["product", "over_all_cost", "total_returns", "balance", "current_price", "average_price", "average_price_sold_at", "average_price_bought_at"] 
    for key in product_stat_dict_keys:
        if key not in product_stat:
            raise f"Missing key {key}"
        
