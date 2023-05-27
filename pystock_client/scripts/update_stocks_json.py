import json
import locale
from pathlib import Path
from typing import List
import asyncio
from pystock_client import config
from pystock_client.utils import (Stock, timeit)
from pystock_client.scraper.stocks_scraper import (
    get_stocks_list_from_market_watch_init_page,
    get_stocks_list_from_stocks_list_page,
    get_stock_ids_with_symbol
)


def write_stocks_to_json(
    stocks_list: List[Stock], filename: str, path: str
) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)
    with open(f"{path}/{filename}", "w", encoding="utf8") as file:
        data = {
            obj.symbol: {
                "current_id": obj.current_id,
                "instrument_id": obj.instrument_id,
                "name": obj.name,
                "old_ids": obj.old_ids,
            }
            for obj in stocks_list
        }
        json.dump(data, file, ensure_ascii=False, indent=2)


def get_stocks_list() -> List[Stock]:
    stocks_list = []
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    stocks_list = loop.run_until_complete(_get_stocks_list())
    loop.close()
    return stocks_list


async def _get_stocks_list() -> List[Stock]:
    stocks_list = []
    results_list = await asyncio.gather(
        get_stocks_list_from_market_watch_init_page(),
        get_stocks_list_from_stocks_list_page(),
        return_exceptions=True)
    stocks_set = set(stock for result in results_list if isinstance(
        result, list) for stock in result)
    add_old_indexes_task = []
    for stock in stocks_set:
        add_old_indexes_task.append(get_stock_ids_with_symbol(stock))
    results_list = await asyncio.gather(*add_old_indexes_task, return_exceptions=True)
    for result in results_list:
        if isinstance(result, Stock):
            stocks_list.append(result)
    if len(stocks_list) != len(stocks_set):
        print("Stocks_list Not Complete")
    return stocks_list


@timeit
def main():
    locale.setlocale(locale.LC_COLLATE, "fa_IR.UTF-8")
    stocks_list = list(get_stocks_list())
    sorted_stocks_list = sorted(stocks_list)
    write_stocks_to_json(
        sorted_stocks_list, "stocks_list.json", f"{config.pystock_dir}/data"
    )


if __name__ == "__main__":
    main()
