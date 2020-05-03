import logging
import asyncio, aiohttp

credit_params = {"prepaid": 3000000, "full_price": 7000000, "months_qty": 120}
TIME_OUT = 10


def calculate_average_rate(short_bank_data: list) -> float:
    return round(sum(float(bank['rate']['median']) for bank in short_bank_data)
                 / len(short_bank_data), 2)


def calculate_weighted_average_rate(short_bank_data: list) -> float:
    sber = short_bank_data[0]
    vtb = short_bank_data[1]
    others = sum(
        float(bank['rate']['median']) for bank in short_bank_data[2:]
    ) / len(short_bank_data[2:])

    sber_weighted_avg = sber['rate']['median'] * 0.56
    vtb_weighted_avg = vtb['rate']['median'] * 0.256
    others_weighted_avg = others * 0.184
    total_weighted_avg = round(
        sber_weighted_avg + vtb_weighted_avg + others_weighted_avg,
        2
    )

    return total_weighted_avg


def conf_logger(level):
    logger = logging.getLogger(__name__)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    formatter = logging.Formatter(
        '[%(asctime)s - %(name)s - %(levelname)s - module:%(filename)s#%(lineno)d '
        '- func: "%(funcName)s"] message: "%(message)s"'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.setLevel(level)

    return logger


logger = conf_logger(logging.DEBUG)


async def query_url(url, headers=None, method='get', data=None):
    async with aiohttp.ClientSession() as session:
        async with getattr(session, method.lower())(
                url=url, headers=headers, timeout=TIME_OUT, data=data
        ) as response:
            return await response.json()


async def gather_tasks(coros: dict, result_getter: callable = None):
    tasks = _wrap_coros(coros)

    done, pending = await asyncio.wait(
        tasks, timeout=TIME_OUT, return_when=asyncio.ALL_COMPLETED
    )
    return _process_tasks(done, pending, result_getter)


def _wrap_coros(coros: dict):
    tasks = []

    for name, coro in coros.items():
        task = asyncio.create_task(coro)
        task.set_name(name)
        tasks.append(task)

    return tasks


def _process_tasks(done, pending, result_getter):
    raw_result = {task.get_name(): task.result() for task in done}

    if pending:
        raise RuntimeError(f"Some tasks are incomplete: {pending}")
    elif result_getter:
        return result_getter(raw_result)
    else:
        return raw_result
