import re
from typing import (Dict,
                    List,)

from bs4 import (BeautifulSoup,
                 PageElement)

from pystock_client import tsetmc_settings

from pystock_client.utils import (custom_logger,
                                  Stock,
                                  replace_arabic,
                                  get_request,
                                  get_html_table_header_and_rows)

_logger = custom_logger.main_logger


async def get_stock_ids_with_symbol(stock: Stock):
    """
    get stock ids from tse symbol search page
    """
    _logger.info("scraping indexes information for %s", stock.symbol)
    url = tsetmc_settings.TSETMC_SEARCH_WITH_SYMBOL_URL.format(
        stock.symbol.strip())
    response = await get_request(url)
    assert response is not None
    symbols = response.split(';')
    current_id = None
    old_ids = []
    for symbol_full_info in symbols:
        if symbol_full_info.strip() == "":
            continue
        symbol_full_info = symbol_full_info.split(',')
        if replace_arabic(symbol_full_info[0]) == stock.symbol:
            if symbol_full_info[7] == '1':
                current_id = symbol_full_info[2]  # active stock id
            else:
                old_ids.append(symbol_full_info[2])  # old stock id
    stock.current_id = current_id or stock.current_id
    stock.old_ids = old_ids
    _logger.info("scrape indexes information %s success", stock.symbol)
    return stock


async def get_stocks_list_from_stocks_list_page() -> List[Stock]:
    """
    uses STOCKS_LIST_URL and scrapes stocks information from the page
    :return: list of all stocks
    :rtype: List[StockDataClass]
    """
    _logger.info("scraping stocks information from symbols list page")
    stocks_list = []
    url = tsetmc_settings.STOCKS_LIST_URL
    response = await get_request(url)
    assert response is not None
    soup = BeautifulSoup(response, 'html.parser')
    table = soup.find("table")
    if not isinstance(table, PageElement):
        return stocks_list
    _, table_rows = get_html_table_header_and_rows(table)
    for row_data in table_rows:
        # escape old symbols
        if row_data[7].a.text.startswith('حذف-'):
            continue
        if row_data[6].a.text.isdigit():
            continue
        stocks_list.append(
            Stock(
                instrument_id=row_data[0].text,
                symbol=replace_arabic(row_data[6].a.text),
                name=replace_arabic(row_data[7].a.text),
                current_id=row_data[6].a.get('href').partition('inscode=')[2],
            )
        )
    _logger.info("scrape stocks information from symbols list page success")
    return stocks_list


async def get_stocks_list_from_market_watch_init_page() -> List[Stock] | Dict:
    """
    get stocks information from market watch page
    :return: list of stock
    :rtype: List[StockDataClass]
    """
    _logger.info("scraping stocks information from market watch page")
    stocks_list = []
    url = tsetmc_settings.MARKET_WATCH_INIT_URL
    response = await get_request(url)
    assert response is not None, "error"
    response_groups = response.split("@")
    if len(response_groups) < 3:
        _logger.error(
            "stocks information from market watch page is not valid",
            extra={"response": response}
        )
        return stocks_list
    symbols_data = response_groups[2].split(";")
    for symbol_data in symbols_data:
        data = symbol_data.split(",")
        # if symbol name ends with number it's some kind of symbol
        # like 'اختیار خرید و فروش،اوراق مشارکت،امتیاز تسهیلات' and we don't want it
        symbol_name_ends_with_number = re.search(r'\d+$', data[2])
        if symbol_name_ends_with_number:
            continue
        if "گواهی" in replace_arabic(data[3]):
            # if name contains 'گواهی' it's some kind of symbol
            # like 'گواهی شیشه' and we don't want it
            continue
        if data[2].isdigit():
            # if symbol name is number it's some kind of symbol
            continue
        stocks_list.append(
            Stock(
                instrument_id=replace_arabic(data[1]),
                symbol=replace_arabic(data[2]),
                current_id=replace_arabic(data[0]),
                name=replace_arabic(data[3]),
            )
        )
    _logger.info("scrape stocks information from market watch page success")
    return stocks_list
