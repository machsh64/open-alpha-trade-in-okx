from typing import Dict, List, Any
import logging
from .okx_market_data import (
    get_last_price_from_okx,
    get_kline_data_from_okx,
    get_market_status_from_okx,
    get_all_symbols_from_okx,
    okx_client,
)

logger = logging.getLogger(__name__)


def get_last_price(symbol: str, market: str = "CRYPTO") -> float:
    key = f"{symbol}.{market}"
    
    # Check cache first
    from .price_cache import get_cached_price, cache_price
    cached_price = get_cached_price(symbol, market)
    if cached_price is not None:
        logger.debug(f"Using cached price for {key}: {cached_price}")
        return cached_price
    
    logger.info(f"Getting real-time price for {key} from API...")

    try:
        price = get_last_price_from_okx(symbol)
        if price and price > 0:
            logger.info(f"Got real-time price for {key} from OKX: {price}")
            # Cache the price
            cache_price(symbol, market, price)
            return price
        raise Exception(f"OKX returned invalid price: {price}")
    except Exception as okx_err:
        logger.error(f"Failed to get price from OKX: {okx_err}")
        raise Exception(f"Unable to get real-time price for {key}: {okx_err}")


def get_kline_data(symbol: str, market: str = "CRYPTO", period: str = "1d", count: int = 100) -> List[Dict[str, Any]]:
    key = f"{symbol}.{market}"

    try:
        data = get_kline_data_from_okx(symbol, period, count)
        if data:
            logger.info(f"Got K-line data for {key} from OKX, total {len(data)} items")
            return data
        raise Exception("OKX returned empty K-line data")
    except Exception as okx_err:
        logger.error(f"Failed to get K-line data from OKX: {okx_err}")
        raise Exception(f"Unable to get K-line data for {key}: {okx_err}")


def get_market_status(symbol: str, market: str = "CRYPTO") -> Dict[str, Any]:
    key = f"{symbol}.{market}"

    try:
        status = get_market_status_from_okx(symbol)
        logger.info(f"Retrieved market status for {key} from OKX: {status.get('market_status')}")
        return status
    except Exception as okx_err:
        logger.error(f"Failed to get market status: {okx_err}")
        raise Exception(f"Unable to get market status for {key}: {okx_err}")


def get_all_symbols() -> List[str]:
    """Get all available trading pairs"""
    try:
        symbols = get_all_symbols_from_okx()
        logger.info(f"Got {len(symbols)} trading pairs from OKX")
        return symbols
    except Exception as okx_err:
        logger.error(f"Failed to get trading pairs list: {okx_err}")
        return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']  # default trading pairs
