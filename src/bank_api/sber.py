import asyncio
from src.bank_api.common import logger, credit_params, query_url, gather_tasks


headers = {'Api-Key': '728a2644-fefc-43c1-9054-5806c8fda7ef'}
market_index = {"первичный рынок": 4, "вторичный рынок": 3}
min_rate_url = 'https://api.domclick.ru/calc/api/v2/mortgages/calculate?isIncomeSberbankCard=yes&isConfirmIncome=true&productId={mortgage_goal}&estateCost={full_price}&deposit={prepaid}&term=120&age=420&isInsured=true&isMarried=true&isHusbandWifeLess35Years=true&childrens=0&useOnRegDiscount=yes&useDeveloperDiscount=true&useRealtyDiscount=true&kladrId=7700000000000'
max_rate_url = 'https://api.domclick.ru/calc/api/v2/mortgages/calculate?isIncomeSberbankCard=no&isConfirmIncome=true&productId={mortgage_goal}&estateCost={full_price}&deposit={prepaid}&term=120&age=420&isInsured=true&isMarried=false&isHusbandWifeLess35Years=false&childrens=0&useOnRegDiscount=no&useDeveloperDiscount=false&useRealtyDiscount=false&kladrId=7700000000000'


async def get_mortgage_data(mortgage_goal: str) -> dict:
    try:
        min_rate_url_f, max_rate_url_f = _prepare_url(mortgage_goal)
        min_rate_c = query_url(min_rate_url_f, headers, 'get')
        max_rate_c = query_url(max_rate_url_f, headers, 'get')
        rates = await gather_tasks({
            'min_rate_data': min_rate_c,
            'max_rate_data': max_rate_c
        }, _extract_mortgage_data)
        logger.debug(f'Sber rates={rates}')

        return rates

    except Exception as e:
        logger.exception(e)
        return {}


def _extract_mortgage_data(mortgage_info: dict) -> dict:
    short_bank_data = {}

    if mortgage_info:
        short_bank_data['rate'] = {}
        short_bank_data['bank_name'] = '<b>Сбербанк</b>'
        min_rate = mortgage_info['min_rate_data']['data']['calculation']['rate']
        max_rate = mortgage_info['max_rate_data']['data']['calculation']['rate']
        short_bank_data['rate']['median'] = round((min_rate + max_rate) / 2, 2)
        short_bank_data['rate']['to'] = max_rate
        short_bank_data['rate']['from'] = min_rate
        short_bank_data['source'] = 'domclick.ru'

    return short_bank_data


def _prepare_url(mortgage_goal: str):
    min_rate_url_f = min_rate_url.format(
        prepaid=credit_params['prepaid'],
        full_price=credit_params['full_price'],
        mortgage_goal=mortgage_goal
    )
    max_rate_url_f = max_rate_url.format(
        prepaid=credit_params['prepaid'],
        full_price=credit_params['full_price'],
        mortgage_goal=mortgage_goal
    )

    return min_rate_url_f, max_rate_url_f
