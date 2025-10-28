"""
OKX market data service using CCXT
支持通过OKX API获取实时市场数据和执行交易
"""
import ccxt
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import time
from dotenv import load_dotenv
from .mock_price_provider import get_mock_price, get_mock_kline_data, get_mock_symbols

# 加载.env文件
load_dotenv()

logger = logging.getLogger(__name__)

class OKXClient:
    def __init__(self):
        self.public_exchange = None  # 公开API（获取行情）
        self.private_exchange = None  # 私有API（交易）
        self._initialize_exchange()
    
    def _initialize_exchange(self):
        """Initialize CCXT OKX exchange"""
        try:
            # 从环境变量获取API配置
            api_key = os.getenv('OKX_API_KEY')
            secret = os.getenv('OKX_SECRET')
            passphrase = os.getenv('OKX_PASSPHRASE')
            sandbox = os.getenv('OKX_SANDBOX', 'true').lower() == 'true'
            
            logger.info(f"Initializing OKX with sandbox={sandbox}")
            
            # 公开API - 无需认证，用于获取行情
            self.public_exchange = ccxt.okx({
                'sandbox': sandbox,
                'enableRateLimit': True,
                'timeout': 30000,
                'options': {
                    'defaultType': 'swap',
                },
                'proxies': {
                    'http': 'http://127.0.0.1:7890',
                    'https': 'http://127.0.0.1:7890'
                }
            })
            logger.info("OKX public API initialized")
            
            # 私有API - 需要认证，用于交易
            if api_key and secret and passphrase:
                self.private_exchange = ccxt.okx({
                    'apiKey': api_key,
                    'secret': secret,
                    'password': passphrase,
                    'sandbox': sandbox,
                    'enableRateLimit': True,
                    'timeout': 30000,
                    'options': {
                        'defaultType': 'swap',
                    },
                    'proxies': {
                        'http': 'http://127.0.0.1:7890',
                        'https': 'http://127.0.0.1:7890'
                    }
                })
                logger.info("OKX private API initialized")
            else:
                logger.warning("OKX API credentials not configured, trading disabled")
            
            logger.info(f"OKX exchange initialized successfully (sandbox: {sandbox})")
        except Exception as e:
            logger.error(f"Failed to initialize OKX exchange: {e}")
            raise

    def get_last_price(self, symbol: str) -> Optional[float]:
        """Get the last price for a symbol (with mock fallback)"""
        try:
            if not self.public_exchange:
                self._initialize_exchange()
            
            # Ensure symbol is in CCXT format (e.g., 'BTC/USDT:USDT' for perpetual)
            formatted_symbol = self._format_symbol(symbol)
            logger.info(f"Fetching price for {symbol} -> {formatted_symbol}")
            
            ticker = self.public_exchange.fetch_ticker(formatted_symbol)
            price = ticker['last']
            
            if price is None or price <= 0:
                logger.warning(f"Invalid price received for {formatted_symbol}: {price}")
                # 尝试使用其他价格字段
                price = ticker.get('close') or ticker.get('bid') or ticker.get('ask')
                if price is None or price <= 0:
                    logger.error(f"All price fields are invalid for {formatted_symbol}: {ticker}")
                    # 使用备用价格
                    mock_price = get_mock_price(symbol)
                    logger.info(f"Using mock price for {symbol}: {mock_price}")
                    return mock_price
            
            logger.info(f"Got price for {formatted_symbol}: {price}")
            return float(price)
            
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            # 网络连接失败时使用备用价格源
            try:
                logger.info(f"Using mock price for {symbol} due to error")
                mock_price = get_mock_price(symbol)
                if mock_price and mock_price > 0:
                    logger.info(f"Got mock price for {symbol}: {mock_price}")
                    return mock_price
            except Exception as mock_error:
                logger.error(f"Mock price fetch also failed for {symbol}: {mock_error}")
            
            return None

    def get_kline_data(self, symbol: str, period: str = '1d', count: int = 100) -> List[Dict[str, Any]]:
        """Get kline/candlestick data for a symbol"""
        try:
            if not self.public_exchange:
                self._initialize_exchange()
            
            formatted_symbol = self._format_symbol(symbol)
            
            # Map period to CCXT timeframe
            timeframe_map = {
                '1m': '1m',
                '5m': '5m', 
                '15m': '15m',
                '30m': '30m',
                '1h': '1h',
                '1d': '1d',
            }
            timeframe = timeframe_map.get(period, '1d')
            
            # Fetch OHLCV data
            ohlcv = self.public_exchange.fetch_ohlcv(formatted_symbol, timeframe, limit=count)
            
            # Convert to our format
            klines = []
            for candle in ohlcv:
                timestamp_ms = candle[0]
                open_price = candle[1]
                high_price = candle[2]
                low_price = candle[3]
                close_price = candle[4]
                volume = candle[5]
                
                # Calculate change
                change = close_price - open_price if open_price else 0
                percent = (change / open_price * 100) if open_price else 0
                
                klines.append({
                    'timestamp': int(timestamp_ms / 1000),  # Convert to seconds
                    'datetime_str': datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).isoformat(),
                    'open': float(open_price) if open_price else None,
                    'high': float(high_price) if high_price else None,
                    'low': float(low_price) if low_price else None,
                    'close': float(close_price) if close_price else None,
                    'volume': float(volume) if volume else None,
                    'amount': float(volume * close_price) if volume and close_price else None,
                    'change': float(change),
                    'percent': float(percent),
                })
            
            logger.info(f"Got {len(klines)} klines for {formatted_symbol}")
            return klines
            
        except Exception as e:
            logger.error(f"Error fetching klines for {symbol}: {e}")
            # 网络连接失败时使用备用价格源
            try:
                logger.info(f"Using mock kline data for {symbol} due to network issues")
                mock_klines = get_mock_kline_data(symbol, period, count)
                if mock_klines:
                    logger.info(f"Got {len(mock_klines)} mock klines for {symbol}")
                    return mock_klines
            except Exception as mock_error:
                logger.error(f"Mock kline data generation failed for {symbol}: {mock_error}")
            
            return []

    def get_market_status(self, symbol: str) -> Dict[str, Any]:
        """Get market status for a symbol"""
        try:
            if not self.public_exchange:
                self._initialize_exchange()
            
            formatted_symbol = self._format_symbol(symbol)
            
            # Check if the market exists
            markets = self.public_exchange.load_markets()
            market_exists = formatted_symbol in markets
            
            status = {
                'market_status': 'OPEN' if market_exists else 'CLOSED',
                'is_trading': market_exists,
                'symbol': formatted_symbol,
                'exchange': 'OKX',
                'market_type': 'perpetual_swap',  # 永续合约
            }
            
            if market_exists:
                market_info = markets[formatted_symbol]
                status.update({
                    'base_currency': market_info.get('base'),
                    'quote_currency': market_info.get('quote'),
                    'active': market_info.get('active', True),
                    'spot': market_info.get('spot', False),
                    'future': market_info.get('future', False),
                    'swap': market_info.get('swap', False),
                })
            
            logger.info(f"Market status for {formatted_symbol}: {status['market_status']}")
            return status
            
        except Exception as e:
            logger.error(f"Error getting market status for {symbol}: {e}")
            return {
                'market_status': 'ERROR',
                'is_trading': False,
                'error': str(e)
            }

    def get_all_symbols(self) -> List[str]:
        """Get all available trading symbols"""
        try:
            if not self.public_exchange:
                self._initialize_exchange()
            
            markets = self.public_exchange.load_markets()
            symbols = list(markets.keys())
            
            # 过滤USDT永续合约交易对
            usdt_swap_symbols = [s for s in symbols if '/USDT:USDT' in s]
            
            # 优先返回主流加密货币永续合约
            mainstream_cryptos = [s for s in usdt_swap_symbols if any(crypto in s for crypto in ['BTC/', 'ETH/', 'SOL/', 'DOGE/', 'BNB/', 'XRP/', 'ADA/', 'DOT/', 'MATIC/', 'AVAX/'])]
            other_symbols = [s for s in usdt_swap_symbols if s not in mainstream_cryptos]
            
            # 返回主流币种在前，其他币种随后（限制总数）
            result = mainstream_cryptos + other_symbols[:100]
            
            logger.info(f"Found {len(usdt_swap_symbols)} USDT perpetual swap pairs, returning {len(result)}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting symbols: {e}")
            # 网络连接失败时使用备用交易对列表
            try:
                logger.info("Using mock symbols due to network issues")
                mock_symbols = get_mock_symbols()
                logger.info(f"Got {len(mock_symbols)} mock trading pairs")
                return mock_symbols
            except Exception as mock_error:
                logger.error(f"Mock symbols generation failed: {mock_error}")
            
            return ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT']  # 永续合约默认交易对

    def _format_symbol(self, symbol: str) -> str:
        """
        Format symbol for CCXT
        Supports: BTC-USDT-SWAP, BTC/USDT:USDT, BTC/USDT, BTC
        Output: BTC/USDT:USDT (CCXT perpetual swap format)
        """
        # 如果已经是完整格式，直接返回
        if '/' in symbol and ':' in symbol:
            return symbol
        
        # 如果是OKX原生格式 (BTC-USDT-SWAP)，转换为CCXT格式
        if '-USDT-SWAP' in symbol.upper():
            base = symbol.upper().replace('-USDT-SWAP', '')
            return f"{base}/USDT:USDT"
        
        # 如果是 BTC/USDT 格式，转换为永续合约格式
        if '/' in symbol and not ':' in symbol:
            if symbol.endswith('/USDT'):
                return f"{symbol}:USDT"  # BTC/USDT -> BTC/USDT:USDT
            else:
                # 如果不是USDT交易对，转换为USDT永续合约
                base = symbol.split('/')[0]
                return f"{base}/USDT:USDT"
        
        # 单个币种符号，转换为USDT永续合约
        symbol_upper = symbol.upper()
        return f"{symbol_upper}/USDT:USDT"

    # Trading methods for live trading
    def create_market_order(self, symbol: str, side: str, amount: float, params: dict = None) -> dict:
        """Create a market order"""
        try:
            if not self.private_exchange:
                raise Exception("Private API not initialized - check OKX credentials")
            
            formatted_symbol = self._format_symbol(symbol)
            
            if params is None:
                params = {}
            
            # OKX永续合约需要指定posSide参数
            # buy = 开多仓(long), sell = 开空仓(short)
            if 'posSide' not in params:
                params['posSide'] = 'long' if side.lower() == 'buy' else 'short'
            
            # OKX永续合约需要指定交易模式 tdMode
            if 'tdMode' not in params:
                params['tdMode'] = 'cross'  # 使用全仓模式，也可以用 'isolated' 逐仓
            
            order = self.private_exchange.create_market_order(formatted_symbol, side, amount, None, params)
            logger.info(f"Created market {side} order for {formatted_symbol}: {amount} units (posSide={params['posSide']})")
            return order
            
        except Exception as e:
            logger.error(f"Error creating market order: {e}")
            raise

    def create_limit_order(self, symbol: str, side: str, amount: float, price: float, params: dict = None) -> dict:
        """Create a limit order"""
        try:
            if not self.private_exchange:
                raise Exception("Private API not initialized - check OKX credentials")
            
            formatted_symbol = self._format_symbol(symbol)
            
            if params is None:
                params = {}
            
            # OKX永续合约需要指定posSide参数
            # buy = 开多仓(long), sell = 开空仓(short)
            if 'posSide' not in params:
                params['posSide'] = 'long' if side.lower() == 'buy' else 'short'
            
            # OKX永续合约需要指定交易模式 tdMode
            if 'tdMode' not in params:
                params['tdMode'] = 'cross'  # 使用全仓模式，也可以用 'isolated' 逐仓
            
            order = self.private_exchange.create_limit_order(formatted_symbol, side, amount, price, params)
            logger.info(f"Created limit {side} order for {formatted_symbol}: {amount} units at {price} (posSide={params['posSide']})")
            return order
            
        except Exception as e:
            logger.error(f"Error creating limit order: {e}")
            raise

    def cancel_order(self, order_id: str, symbol: str, params: dict = None) -> dict:
        """Cancel an order"""
        try:
            if not self.private_exchange:
                raise Exception("Private API not initialized - check OKX credentials")
            
            formatted_symbol = self._format_symbol(symbol)
            
            if params is None:
                params = {}
            
            result = self.private_exchange.cancel_order(order_id, formatted_symbol, params)
            logger.info(f"Cancelled order {order_id} for {formatted_symbol}")
            return result
            
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            raise

    def fetch_order(self, order_id: str, symbol: str, params: dict = None) -> dict:
        """Fetch order details"""
        try:
            if not self.private_exchange:
                raise Exception("Private API not initialized - check OKX credentials")
            
            formatted_symbol = self._format_symbol(symbol)
            
            if params is None:
                params = {}
            
            order = self.private_exchange.fetch_order(order_id, formatted_symbol, params)
            return order
            
        except Exception as e:
            logger.error(f"Error fetching order: {e}")
            raise

    def fetch_balance(self, params: dict = None) -> dict:
        """Fetch account balance"""
        try:
            if not self.private_exchange:
                raise Exception("Private API not initialized - check OKX credentials")
            
            if params is None:
                params = {}
            
            balance = self.private_exchange.fetch_balance(params)
            return balance
            
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            raise

    def fetch_positions(self, symbol: str = None, params: dict = None) -> List[Dict[str, Any]]:
        """
        Fetch current positions from OKX
        
        Args:
            symbol: Optional symbol to filter positions (e.g., 'BTC/USDT:USDT')
            params: Additional parameters
            
        Returns:
            List of position dictionaries
        """
        try:
            if not self.private_exchange:
                raise Exception("Private API not initialized - check OKX credentials")
            
            if params is None:
                params = {}
            
            # OKX requires instType for positions
            if 'instType' not in params:
                params['instType'] = 'SWAP'  # 永续合约
            
            positions = self.private_exchange.fetch_positions(symbols=[symbol] if symbol else None, params=params)
            
            # 只返回有持仓的数据
            active_positions = [p for p in positions if float(p.get('contracts', 0)) > 0 or float(p.get('contractSize', 0)) > 0]
            
            logger.info(f"Fetched {len(active_positions)} active positions from OKX")
            return active_positions
            
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []

    def fetch_open_orders(self, symbol: str = None, params: dict = None) -> List[Dict[str, Any]]:
        """
        Fetch open orders from OKX
        
        Args:
            symbol: Optional symbol to filter orders
            params: Additional parameters
            
        Returns:
            List of open order dictionaries
        """
        try:
            if not self.private_exchange:
                raise Exception("Private API not initialized - check OKX credentials")
            
            if params is None:
                params = {}
            
            formatted_symbol = self._format_symbol(symbol) if symbol else None
            orders = self.private_exchange.fetch_open_orders(formatted_symbol, params=params)
            
            logger.info(f"Fetched {len(orders)} open orders from OKX")
            return orders
            
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return []

    def fetch_closed_orders(self, symbol: str = None, since: int = None, limit: int = 100, params: dict = None) -> List[Dict[str, Any]]:
        """
        Fetch closed orders (order history) from OKX
        
        Args:
            symbol: Optional symbol to filter orders
            since: Timestamp in milliseconds to fetch orders since
            limit: Maximum number of orders to return
            params: Additional parameters
            
        Returns:
            List of closed order dictionaries
        """
        try:
            if not self.private_exchange:
                raise Exception("Private API not initialized - check OKX credentials")
            
            if params is None:
                params = {}
            
            formatted_symbol = self._format_symbol(symbol) if symbol else None
            orders = self.private_exchange.fetch_closed_orders(formatted_symbol, since, limit, params)
            
            logger.info(f"Fetched {len(orders)} closed orders from OKX")
            return orders
            
        except Exception as e:
            logger.error(f"Error fetching closed orders: {e}")
            return []

    def fetch_my_trades(self, symbol: str = None, since: int = None, limit: int = 100, params: dict = None) -> List[Dict[str, Any]]:
        """
        Fetch trade history from OKX
        
        Args:
            symbol: Optional symbol to filter trades
            since: Timestamp in milliseconds to fetch trades since
            limit: Maximum number of trades to return
            params: Additional parameters
            
        Returns:
            List of trade dictionaries
        """
        try:
            if not self.private_exchange:
                raise Exception("Private API not initialized - check OKX credentials")
            
            if params is None:
                params = {}
            
            formatted_symbol = self._format_symbol(symbol) if symbol else None
            trades = self.private_exchange.fetch_my_trades(formatted_symbol, since, limit, params)
            
            logger.info(f"Fetched {len(trades)} trades from OKX")
            return trades
            
        except Exception as e:
            logger.error(f"Error fetching trades: {e}")
            return []


# Global client instance
okx_client = OKXClient()


def get_last_price_from_okx(symbol: str) -> Optional[float]:
    """Get last price from OKX"""
    return okx_client.get_last_price(symbol)


def get_kline_data_from_okx(symbol: str, period: str = '1d', count: int = 100) -> List[Dict[str, Any]]:
    """Get kline data from OKX"""
    return okx_client.get_kline_data(symbol, period, count)


def get_market_status_from_okx(symbol: str) -> Dict[str, Any]:
    """Get market status from OKX"""
    return okx_client.get_market_status(symbol)


def get_all_symbols_from_okx() -> List[str]:
    """Get all available symbols from OKX"""
    return okx_client.get_all_symbols()


# Trading functions
def create_market_order_okx(symbol: str, side: str, amount: float, params: dict = None) -> dict:
    """Create market order on OKX"""
    return okx_client.create_market_order(symbol, side, amount, params)


def create_limit_order_okx(symbol: str, side: str, amount: float, price: float, params: dict = None) -> dict:
    """Create limit order on OKX"""
    return okx_client.create_limit_order(symbol, side, amount, price, params)


def cancel_order_okx(order_id: str, symbol: str, params: dict = None) -> dict:
    """Cancel order on OKX"""
    return okx_client.cancel_order(order_id, symbol, params)


def fetch_order_okx(order_id: str, symbol: str, params: dict = None) -> dict:
    """Fetch order details from OKX"""
    return okx_client.fetch_order(order_id, symbol, params)


def fetch_balance_okx(params: dict = None) -> dict:
    """Fetch balance from OKX"""
    return okx_client.fetch_balance(params)


def fetch_positions_okx(symbol: str = None, params: dict = None) -> List[Dict[str, Any]]:
    """Fetch positions from OKX"""
    return okx_client.fetch_positions(symbol, params)


def fetch_open_orders_okx(symbol: str = None, params: dict = None) -> List[Dict[str, Any]]:
    """Fetch open orders from OKX"""
    return okx_client.fetch_open_orders(symbol, params)


def fetch_closed_orders_okx(symbol: str = None, since: int = None, limit: int = 100, params: dict = None) -> List[Dict[str, Any]]:
    """Fetch closed orders from OKX"""
    return okx_client.fetch_closed_orders(symbol, since, limit, params)


def fetch_my_trades_okx(symbol: str = None, since: int = None, limit: int = 100, params: dict = None) -> List[Dict[str, Any]]:
    """Fetch trade history from OKX"""
    return okx_client.fetch_my_trades(symbol, since, limit, params)


def get_market_analysis(symbol: str, period: str = "1h", count: int = 168) -> Dict[str, Any]:
    """
    获取市场分析数据，包括历史价格和技术指标
    
    Args:
        symbol: 交易对符号，如 'BTC', 'ETH'
        period: K线周期，默认1小时
        count: 获取的K线数量，默认168（1周的小时线）
        
    Returns:
        包含价格历史、技术指标和市场统计的字典
    """
    try:
        # 获取K线数据
        klines = okx_client.get_kline_data(symbol, period, count)
        
        if not klines or len(klines) < 2:
            return {
                "symbol": symbol,
                "error": "Insufficient data",
                "period": period
            }
        
        # 提取价格数据
        closes = [k['close'] for k in klines if k['close'] is not None]
        highs = [k['high'] for k in klines if k['high'] is not None]
        lows = [k['low'] for k in klines if k['low'] is not None]
        volumes = [k['volume'] for k in klines if k['volume'] is not None]
        
        if not closes:
            return {
                "symbol": symbol,
                "error": "No valid price data",
                "period": period
            }
        
        current_price = closes[-1]
        
        # 计算简单技术指标
        # 1. 价格变化（多个时间段）
        price_15m_ago = closes[-15] if len(closes) >= 15 else closes[0]  # 15分钟前
        price_1h_ago = closes[-60] if len(closes) >= 60 else closes[-1] if len(closes) >= 1 else closes[0]  # 1小时前
        price_4h_ago = closes[-240] if len(closes) >= 240 else closes[0]  # 4小时前（240分钟）
        price_24h_ago = closes[-24] if len(closes) >= 24 else closes[0]  # 24小时前（24个1小时K线）
        price_7d_ago = closes[0]  # 7天前
        
        change_15m = ((current_price - price_15m_ago) / price_15m_ago * 100) if price_15m_ago else 0
        change_1h = ((current_price - price_1h_ago) / price_1h_ago * 100) if price_1h_ago else 0
        change_4h = ((current_price - price_4h_ago) / price_4h_ago * 100) if price_4h_ago else 0
        change_24h = ((current_price - price_24h_ago) / price_24h_ago * 100) if price_24h_ago else 0
        change_7d = ((current_price - price_7d_ago) / price_7d_ago * 100) if price_7d_ago else 0
        
        # 2. 简单移动平均线 (SMA)
        def calculate_sma(data, period):
            if len(data) < period:
                return None
            return sum(data[-period:]) / period
        
        sma_7 = calculate_sma(closes, 7)    # 7周期
        sma_25 = calculate_sma(closes, 25)  # 25周期
        sma_99 = calculate_sma(closes, 99)  # 99周期
        
        # 3. 波动率 (最近24小时的价格标准差)
        recent_closes = closes[-24:] if len(closes) >= 24 else closes
        avg_price = sum(recent_closes) / len(recent_closes)
        variance = sum((x - avg_price) ** 2 for x in recent_closes) / len(recent_closes)
        volatility = (variance ** 0.5) / avg_price * 100  # 百分比形式
        
        # 4. 相对强弱指标 RSI (简化版，14周期)
        def calculate_rsi(prices, period=14):
            if len(prices) < period + 1:
                return None
            
            gains = []
            losses = []
            for i in range(1, len(prices)):
                change = prices[i] - prices[i-1]
                gains.append(max(change, 0))
                losses.append(max(-change, 0))
            
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            
            if avg_loss == 0:
                return 100
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        rsi = calculate_rsi(closes, 14)
        
        # 5. 支撑位和阻力位（最近的最高和最低价）
        recent_high = max(highs[-24:]) if len(highs) >= 24 else max(highs)
        recent_low = min(lows[-24:]) if len(lows) >= 24 else min(lows)
        
        # 6. 成交量分析
        avg_volume = sum(volumes[-24:]) / len(volumes[-24:]) if len(volumes) >= 24 else sum(volumes) / len(volumes)
        current_volume = volumes[-1] if volumes else 0
        volume_ratio = (current_volume / avg_volume) if avg_volume > 0 else 1.0
        
        # 7. 趋势判断
        trend = "NEUTRAL"
        if sma_7 and sma_25:
            if sma_7 > sma_25 * 1.02:  # 7日均线显著高于25日均线
                trend = "BULLISH"
            elif sma_7 < sma_25 * 0.98:  # 7日均线显著低于25日均线
                trend = "BEARISH"
        
        # 构建分析结果
        analysis = {
            "symbol": symbol,
            "period": period,
            "data_points": len(klines),
            "current_price": round(current_price, 2),
            
            "price_changes": {
                "15m_percent": round(change_15m, 2),
                "1h_percent": round(change_1h, 2),
                "4h_percent": round(change_4h, 2),
                "24h_percent": round(change_24h, 2),
                "7d_percent": round(change_7d, 2),
                "15m_price": round(price_15m_ago, 2),
                "1h_price": round(price_1h_ago, 2),
                "4h_price": round(price_4h_ago, 2),
                "24h_price": round(price_24h_ago, 2),
                "7d_price": round(price_7d_ago, 2)
            },
            
            "moving_averages": {
                "sma_7": round(sma_7, 2) if sma_7 else None,
                "sma_25": round(sma_25, 2) if sma_25 else None,
                "sma_99": round(sma_99, 2) if sma_99 else None
            },
            
            "technical_indicators": {
                "rsi_14": round(rsi, 2) if rsi else None,
                "volatility_24h": round(volatility, 2),
                "trend": trend
            },
            
            "support_resistance": {
                "recent_high_24h": round(recent_high, 2),
                "recent_low_24h": round(recent_low, 2),
                "distance_from_high": round((current_price - recent_high) / recent_high * 100, 2),
                "distance_from_low": round((current_price - recent_low) / recent_low * 100, 2)
            },
            
            "volume_analysis": {
                "current_volume": round(current_volume, 2) if current_volume else 0,
                "avg_volume_24h": round(avg_volume, 2),
                "volume_ratio": round(volume_ratio, 2)
            },
            
            # 最近10个K线的摘要（给AI看趋势）
            "recent_candles": [
                {
                    "time": k['datetime_str'][-14:-3],  # 只保留日期时间部分
                    "open": round(k['open'], 2),
                    "high": round(k['high'], 2),
                    "low": round(k['low'], 2),
                    "close": round(k['close'], 2),
                    "change": round(k['percent'], 2)
                }
                for k in klines[-10:]  # 最近10根K线
            ]
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error getting market analysis for {symbol}: {e}")
        return {
            "symbol": symbol,
            "error": str(e),
            "period": period
        }