import pytest
import logging
from src.bank_api.common import logger, calculate_average_rate, calculate_weighted_average_rate
from src.telegram_api import get_rates, make_message, make_header_message, make_summary_message, main
from unittest.mock import patch


@pytest.mark.asyncio
async def test_rates_api():
    initial_rates = await get_rates('первичный рынок')
    logger.info(f'первичный рынок {initial_rates=}')
    secondary_rates = await get_rates('вторичный рынок')
    logger.info(f'вторичный рынок {secondary_rates=}')
    assert_rates(initial_rates)
    assert_rates(secondary_rates)


@pytest.mark.asyncio
async def test_main(caplog):
    with caplog.at_level(logging.INFO, logger='src.bank_api.common'):
        with patch('src.telegram_api.query_url', side_effect=_mock_query_url):
            await main()
            _assert_output(caplog)


async def _mock_query_url(url, headers=None, method='get', data=None, output='json'):
    text = data.get('text').decode('utf-8')
    logger.info(f'{url=}, {headers=}, {method=}, {text=}, {output=}')


def assert_rates(rates):
    assert 'Сбербанк' in rates[0]['bank_name']
    assert 'ВТБ' in rates[1]['bank_name']

    for rate in rates:
        assert rate['rate']['to'] > 0
        assert rate['rate']['from'] > 0


def _assert_output(caplog):
    logs = caplog.records
    assert '<b>Первичный рынок</b>' in logs[1].message
    assert '<b>Сбербанк</b> (domclick.ru):' in logs[3].message
    assert '<b>Среднерыночная Ставка:' in logs[5].message
    assert '<b>Вторичный рынок</b>' in logs[8].message
    assert '<b>Сбербанк</b> (domclick.ru):' in logs[10].message
    assert '<b>Среднерыночная Ставка:' in logs[12].message
