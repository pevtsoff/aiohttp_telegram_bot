import pytest
import logging
from src.bank_api.common import logger, calculate_average_rate, calculate_weighted_average_rate
from src.telegram_api import get_rates, make_message, make_header_message, make_summary_message


@pytest.mark.asyncio
async def test_rates_api():
    initial_rates = await get_rates('первичный рынок')
    logger.info(f'первичный рынок {initial_rates=}')
    secondary_rates = await get_rates('вторичный рынок')
    logger.info(f'вторичный рынок {secondary_rates=}')
    assert_rates(initial_rates)
    assert_rates(secondary_rates)


@pytest.mark.asyncio
async def test_telegram_messages_manual(caplog):
    with caplog.at_level(logging.INFO, logger='src.bank_api.common'):
        await _messages_for('первичный рынок')
        await _messages_for('вторичный рынок')


async def _messages_for(market: str):
    rates = await get_rates(market)
    rate_message = make_message(rates)['text'].decode('utf-8')
    market_desc = market
    avg_rate = calculate_average_rate(rates)
    weighted_avg = calculate_weighted_average_rate(rates)
    logger.info(f'{weighted_avg=}')
    logger.info(make_header_message(market_desc)['text'].decode('utf-8'))
    logger.info(rate_message)
    logger.info(make_summary_message(avg_rate, market_desc)['text'].decode('utf-8'))
    assert_rates(rates)


def assert_rates(rates):
    assert 'Сбербанк' in rates[0]['bank_name']
    assert 'ВТБ' in rates[1]['bank_name']

    for rate in rates:
        assert rate['rate']['to'] > 0
        assert rate['rate']['from'] > 0
