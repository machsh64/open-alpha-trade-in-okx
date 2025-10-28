"""
备用价格数据源 - 用于网络连接问题时的模拟价格
"""
import random
import time
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MockPriceProvider:
    """模拟价格提供商 - 用于测试和演示"""
    
    def __init__(self):
        # 基础价格（模拟真实市场价格）
        self.base_prices = {
            'BTC/USDT:USDT': 67500.0,
            'ETH/USDT:USDT': 2650.0,
            'SOL/USDT:USDT': 175.0,
            'DOGE/USDT:USDT': 0.15,
            'BNB/USDT:USDT': 585.0,
            'XRP/USDT:USDT': 0.52,
            'ADA/USDT:USDT': 0.35,
            'DOT/USDT:USDT': 4.2,
            'MATIC/USDT:USDT': 0.41,
            'AVAX/USDT:USDT': 27.5,
        }
        self.last_update = time.time()
        
    def get_price(self, symbol: str) -> Optional[float]:
        """获取模拟价格"""
        try:
            # 格式化符号
            if '/' not in symbol:
                symbol = f"{symbol.upper()}/USDT:USDT"
            elif ':' not in symbol:
                symbol = f"{symbol}:USDT"
            
            base_price = self.base_prices.get(symbol)
            if not base_price:
                # 如果没有预设价格，生成一个随机价格
                base_symbol = symbol.split('/')[0]
                if base_symbol in ['BTC', 'ETH']:
                    base_price = random.uniform(20000, 70000)
                elif base_symbol in ['SOL', 'BNB', 'DOT', 'AVAX']:
                    base_price = random.uniform(10, 600)
                else:
                    base_price = random.uniform(0.1, 10)
                self.base_prices[symbol] = base_price
            
            # 添加随机波动 (-2% 到 +2%)
            volatility = random.uniform(-0.02, 0.02)
            current_price = base_price * (1 + volatility)
            
            logger.info(f"Mock price for {symbol}: {current_price}")
            return current_price
            
        except Exception as e:
            logger.error(f"Error generating mock price for {symbol}: {e}")
            return None
    
    def get_kline_data(self, symbol: str, period: str = '1d', count: int = 100) -> List[Dict[str, Any]]:
        """生成模拟K线数据"""
        try:
            base_price = self.get_price(symbol)
            if not base_price:
                return []
            
            klines = []
            current_time = int(time.time())
            
            # 根据时间周期计算间隔
            period_seconds = {
                '1m': 60,
                '5m': 300,
                '15m': 900,
                '30m': 1800,
                '1h': 3600,
                '1d': 86400
            }.get(period, 86400)
            
            for i in range(count):
                timestamp = current_time - (count - i) * period_seconds
                
                # 生成OHLCV数据
                open_price = base_price * (1 + random.uniform(-0.05, 0.05))
                high_price = open_price * (1 + random.uniform(0, 0.03))
                low_price = open_price * (1 - random.uniform(0, 0.03))
                close_price = open_price * (1 + random.uniform(-0.02, 0.02))
                volume = random.uniform(1000, 50000)
                
                change = close_price - open_price
                percent = (change / open_price * 100) if open_price else 0
                
                klines.append({
                    'timestamp': timestamp,
                    'datetime_str': time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(timestamp)),
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': round(volume, 2),
                    'amount': round(volume * close_price, 2),
                    'change': round(change, 2),
                    'percent': round(percent, 2),
                })
                
                base_price = close_price  # 下一根K线的基础价格
            
            logger.info(f"Generated {len(klines)} mock klines for {symbol}")
            return klines
            
        except Exception as e:
            logger.error(f"Error generating mock klines for {symbol}: {e}")
            return []
    
    def get_symbols(self) -> List[str]:
        """获取支持的交易对列表"""
        return list(self.base_prices.keys())

# 全局模拟价格提供商实例
mock_provider = MockPriceProvider()


def get_mock_price(symbol: str) -> Optional[float]:
    """获取模拟价格"""
    return mock_provider.get_price(symbol)


def get_mock_kline_data(symbol: str, period: str = '1d', count: int = 100) -> List[Dict[str, Any]]:
    """获取模拟K线数据"""
    return mock_provider.get_kline_data(symbol, period, count)


def get_mock_symbols() -> List[str]:
    """获取模拟交易对列表"""
    return mock_provider.get_symbols()