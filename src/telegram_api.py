from src.bank_api import sber, vtb, sravni_ru
from src.bank_api.common import logger, calculate_average_rate, gather_tasks, query_url
from src.config import bot_id
import asyncio

url = f'https://api.telegram.org/bot{bot_id}/sendMessage'
msg_template = {"chat_id": "@mortgage_pulse_rus", "parse_mode": "html"}


def make_message(rates: list) -> dict:
    return {
        **msg_template,
        "text": format_mortgage_message(rates).encode('utf-8')
    }


def make_summary_message(rate: list, market) -> dict:
    return {
        **msg_template,
        "text": f'<b>Среднерыночная Ставка: {str(rate)}</b>'.encode("utf-8")
    }


def make_header_message(market) -> dict:
    return {
        **msg_template,
        "text": f'<b>{str(market).capitalize():}</b>'.encode("utf-8")
    }


def format_mortgage_message(rates: list) -> str:
    msg = ''
    for rate in rates:
        if rate:
            bank_name = rate['bank_name']
            median_rate = rate['rate']['median']
            from_rate = rate['rate']['from']
            to_rate = rate['rate']['to']
            source = rate['source']
            msg += f'{bank_name} ({source}): от {from_rate}, до {to_rate};   '

    return msg


async def get_rates(market):
    sber_rates_c = sber.get_mortgage_data(sber.market_index[market])
    vtb_rates_c = vtb.get_mortgage_data(vtb.market_index[market])
    sravni_ru_rates_c = sravni_ru.get_mortgage_data(sravni_ru.market_index[market])

    rates = await gather_tasks({
        'sber_rates': sber_rates_c,
        'vtb_rates': vtb_rates_c,
        'sravni_ru_rates': sravni_ru_rates_c
    }, _extract_rates)

    return rates


async def send_messages_for(market: str):
    try:
        logger.info(f'Sending messages for {market}')
        rates = await get_rates(market)

        data = make_message(rates)
        market_desc = market
        avg_rate = calculate_average_rate(rates)

        res = await query_url(
            url=url, data=make_header_message(market_desc), method='post'
        )
        logger.info(f'header message response={res}')
        res = await query_url(url=url, data=data, method='post')
        logger.info(f'main message response={res}')
        res = await query_url(
            url=url,
            data=make_summary_message(avg_rate, market_desc),
            method='post'
        )

        logger.info(f'sum message response={res}')

    except Exception as e:
        logger.error(e, exc_info=True)



def _extract_rates(rate_tasks: dict) -> list:
    rates = []
    rates += [rate_tasks['sber_rates']]
    rates += [rate_tasks['vtb_rates']]
    rates += rate_tasks['sravni_ru_rates']

    return rates


async def main():
    await send_messages_for('первичный рынок')
    await send_messages_for('вторичный рынок')


if __name__ == '__main__':
    asyncio.run(main())
