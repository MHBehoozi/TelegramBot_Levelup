import logging
import requests

logger = logging.getLogger()

def get_all_currencies(URL, API) -> list:
    logger.info("request to get all currencies")
    url = f'{URL}/'
    headers = {"Authorization": API}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        try:
            currency_list = data["data"]
            return currency_list
        except KeyError:
            logger.error("response for request get all currencies has no data key")
            return list()
    else:
        logger.error("status code for request get all currencies is not 200")
        return list()


def convert_currency_price_to_irr(base: str, URL: str, API: str) -> str:
    currency_list = get_all_currencies(URL, API)
    if not currency_list:
        return ""
    for currency in currency_list:
        if (currency["ID"]).lower() == base.lower():
            return str(currency["price"])
    return ""
