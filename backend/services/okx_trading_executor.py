"""
OKX Trading Executor Service
处理OKX真实交易订单执行
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from .okx_market_data import (
    okx_client,
    create_market_order_okx,
    create_limit_order_okx,
    cancel_order_okx,
    fetch_order_okx,
    fetch_balance_okx
)
from config.settings import OKX_CONFIG

logger = logging.getLogger(__name__)


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OKXTradingExecutor:
    """OKX交易执行器"""
    
    def __init__(self):
        self.client = okx_client
        self.config = OKX_CONFIG
        
        if not self.config.is_valid():
            logger.warning("OKX API credentials not configured. Trading will not be available.")
    
    def is_trading_enabled(self) -> bool:
        """检查是否可以进行交易"""
        return self.config.is_valid()
    
    def create_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        order_type: str = "market",
        price: Optional[float] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        创建订单
        
        Args:
            symbol: 交易对 (e.g., 'BTC/USDT')
            side: 'buy' or 'sell'
            amount: 数量
            order_type: 'market' or 'limit'
            price: 限价单价格 (限价单必需)
            params: 额外参数
        
        Returns:
            订单信息字典
        """
        if not self.is_trading_enabled():
            raise Exception("OKX trading not enabled. Please configure API credentials.")
        
        try:
            if params is None:
                params = {}
            
            # 记录订单创建
            logger.info(f"Creating {order_type} {side} order: {amount} {symbol} at {price if price else 'market price'}")
            
            if order_type.lower() == "market":
                order = create_market_order_okx(symbol, side, amount, params)
            elif order_type.lower() == "limit":
                if price is None:
                    raise ValueError("Price is required for limit orders")
                order = create_limit_order_okx(symbol, side, amount, price, params)
            else:
                raise ValueError(f"Unsupported order type: {order_type}")
            
            logger.info(f"Order created successfully: {order.get('id')}")
            return {
                'success': True,
                'order_id': order.get('id'),
                'symbol': order.get('symbol'),
                'side': order.get('side'),
                'amount': order.get('amount'),
                'price': order.get('price'),
                'type': order.get('type'),
                'status': order.get('status'),
                'timestamp': order.get('timestamp'),
                'raw_order': order
            }
            
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            return {
                'success': False,
                'error': str(e),
                'symbol': symbol,
                'side': side,
                'amount': amount,
                'type': order_type
            }
    
    def cancel_order(self, order_id: str, symbol: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        取消订单
        
        Args:
            order_id: 订单ID
            symbol: 交易对
            params: 额外参数
        
        Returns:
            取消结果字典
        """
        if not self.is_trading_enabled():
            raise Exception("OKX trading not enabled. Please configure API credentials.")
        
        try:
            if params is None:
                params = {}
            
            logger.info(f"Cancelling order {order_id} for {symbol}")
            result = cancel_order_okx(order_id, symbol, params)
            
            logger.info(f"Order {order_id} cancelled successfully")
            return {
                'success': True,
                'order_id': order_id,
                'symbol': symbol,
                'cancelled_at': datetime.utcnow().isoformat(),
                'raw_result': result
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'order_id': order_id,
                'symbol': symbol
            }
    
    def get_order_status(self, order_id: str, symbol: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        查询订单状态
        
        Args:
            order_id: 订单ID
            symbol: 交易对
            params: 额外参数
        
        Returns:
            订单状态字典
        """
        if not self.is_trading_enabled():
            raise Exception("OKX trading not enabled. Please configure API credentials.")
        
        try:
            if params is None:
                params = {}
            
            logger.debug(f"Fetching order status for {order_id}")
            order = fetch_order_okx(order_id, symbol, params)
            
            return {
                'success': True,
                'order_id': order.get('id'),
                'symbol': order.get('symbol'),
                'side': order.get('side'),
                'amount': order.get('amount'),
                'filled': order.get('filled', 0),
                'remaining': order.get('remaining', 0),
                'price': order.get('price'),
                'average_price': order.get('average'),
                'status': order.get('status'),
                'type': order.get('type'),
                'timestamp': order.get('timestamp'),
                'raw_order': order
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch order status for {order_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'order_id': order_id,
                'symbol': symbol
            }
    
    def get_account_balance(self, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        获取账户余额
        
        Args:
            params: 额外参数
        
        Returns:
            余额信息字典
        """
        if not self.is_trading_enabled():
            raise Exception("OKX trading not enabled. Please configure API credentials.")
        
        try:
            if params is None:
                params = {}
            
            logger.debug("Fetching account balance")
            balance = fetch_balance_okx(params)
            
            # 处理余额数据，只返回有余额的资产
            free_balances = {}
            used_balances = {}
            total_balances = {}
            
            for currency, amounts in balance.get('free', {}).items():
                if amounts and float(amounts) > 0:
                    free_balances[currency] = float(amounts)
            
            for currency, amounts in balance.get('used', {}).items():
                if amounts and float(amounts) > 0:
                    used_balances[currency] = float(amounts)
            
            for currency, amounts in balance.get('total', {}).items():
                if amounts and float(amounts) > 0:
                    total_balances[currency] = float(amounts)
            
            return {
                'success': True,
                'free': free_balances,
                'used': used_balances,
                'total': total_balances,
                'timestamp': datetime.utcnow().isoformat(),
                'raw_balance': balance
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch account balance: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def buy_market(self, symbol: str, amount: float, params: Optional[Dict] = None) -> Dict[str, Any]:
        """市价买入"""
        return self.create_order(symbol, "buy", amount, "market", params=params)
    
    def sell_market(self, symbol: str, amount: float, params: Optional[Dict] = None) -> Dict[str, Any]:
        """市价卖出"""
        return self.create_order(symbol, "sell", amount, "market", params=params)
    
    def buy_limit(self, symbol: str, amount: float, price: float, params: Optional[Dict] = None) -> Dict[str, Any]:
        """限价买入"""
        return self.create_order(symbol, "buy", amount, "limit", price, params)
    
    def sell_limit(self, symbol: str, amount: float, price: float, params: Optional[Dict] = None) -> Dict[str, Any]:
        """限价卖出"""
        return self.create_order(symbol, "sell", amount, "limit", price, params)


# 全局交易执行器实例
okx_trading_executor = OKXTradingExecutor()


# 便捷函数
def create_okx_order(symbol: str, side: str, amount: float, order_type: str = "market", 
                     price: Optional[float] = None, params: Optional[Dict] = None, account=None) -> Dict[str, Any]:
    """创建OKX订单 (支持传入account使用其配置)"""
    # 如果传入account，使用account的OKX配置
    if account:
        from .okx_market_data import create_market_order_okx, create_limit_order_okx
        try:
            logger.info(f"Creating {order_type} {side} order for account {account.name}: {amount} {symbol}")
            
            if order_type.lower() == "market":
                order = create_market_order_okx(symbol, side, amount, params, account=account)
            elif order_type.lower() == "limit":
                if price is None:
                    raise ValueError("Price is required for limit orders")
                order = create_limit_order_okx(symbol, side, amount, price, params, account=account)
            else:
                raise ValueError(f"Unsupported order type: {order_type}")
            
            logger.info(f"Order created successfully: {order.get('id')}")
            return {
                'success': True,
                'order_id': order.get('id'),
                'symbol': order.get('symbol'),
                'side': order.get('side'),
                'amount': order.get('amount'),
                'price': order.get('price'),
                'type': order.get('type'),
                'status': order.get('status'),
                'timestamp': order.get('timestamp'),
                'raw_order': order
            }
        except Exception as e:
            logger.error(f"Failed to create order for account {account.name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    else:
        # 回退到全局执行器（使用.env配置）
        return okx_trading_executor.create_order(symbol, side, amount, order_type, price, params)


def cancel_okx_order(order_id: str, symbol: str, params: Optional[Dict] = None, account=None) -> Dict[str, Any]:
    """取消OKX订单"""
    if account:
        from .okx_market_data import cancel_order_okx
        try:
            result = cancel_order_okx(order_id, symbol, params, account=account)
            return {'success': True, 'result': result}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    else:
        return okx_trading_executor.cancel_order(order_id, symbol, params)


def get_okx_order_status(order_id: str, symbol: str, params: Optional[Dict] = None, account=None) -> Dict[str, Any]:
    """获取OKX订单状态"""
    if account:
        from .okx_market_data import fetch_order_okx
        try:
            order = fetch_order_okx(order_id, symbol, params, account=account)
            return {'success': True, 'order': order}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    else:
        return okx_trading_executor.get_order_status(order_id, symbol, params)


def get_okx_balance(params: Optional[Dict] = None) -> Dict[str, Any]:
    """获取OKX账户余额"""
    return okx_trading_executor.get_account_balance(params)


def is_okx_trading_enabled() -> bool:
    """检查OKX交易是否启用"""
    return okx_trading_executor.is_trading_enabled()