"""
OKX Account API Routes
显示OKX账户的真实数据：余额、持仓、订单、交易记录
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from services.okx_market_data import (
    fetch_balance_okx,
    fetch_positions_okx,
    fetch_open_orders_okx,
    fetch_closed_orders_okx,
    fetch_my_trades_okx
)
from services.okx_trading_executor import (
    is_okx_trading_enabled,
    create_okx_order
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/okx-account", tags=["okx-account"])


class OKXOrderRequest(BaseModel):
    """OKX订单请求模型"""
    symbol: str  # 例如: BTC-USDT-SWAP
    side: str  # buy 或 sell
    order_type: str = 'market'  # market 或 limit
    quantity: float  # 数量
    price: Optional[float] = None  # 限价单价格


@router.get("/status")
async def get_okx_status():
    """检查OKX API是否已配置"""
    is_enabled = is_okx_trading_enabled()
    return {
        "okx_enabled": is_enabled,
        "message": "OKX API is configured and ready" if is_enabled else "OKX API credentials not configured",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/balance")
async def get_okx_balance():
    """
    获取OKX账户余额
    
    Returns:
        余额信息，包括可用余额、冻结余额、总余额
    """
    if not is_okx_trading_enabled():
        raise HTTPException(status_code=400, detail="OKX API not configured")
    
    try:
        balance = fetch_balance_okx()
        
        # 提取有余额的币种
        assets = []
        for currency in balance.get('total', {}).keys():
            total = float(balance['total'].get(currency, 0))
            free = float(balance['free'].get(currency, 0))
            used = float(balance['used'].get(currency, 0))
            
            if total > 0:
                assets.append({
                    'currency': currency,
                    'total': total,
                    'free': free,
                    'used': used
                })
        
        return {
            "success": True,
            "assets": assets,
            "timestamp": datetime.utcnow().isoformat(),
            "raw_balance": balance.get('info', {})
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch OKX balance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch balance: {str(e)}")


@router.get("/positions")
async def get_okx_positions(symbol: Optional[str] = None):
    """
    获取OKX持仓信息
    
    Args:
        symbol: 可选，指定交易对（如BTC）
        
    Returns:
        持仓列表
    """
    if not is_okx_trading_enabled():
        raise HTTPException(status_code=400, detail="OKX API not configured")
    
    try:
        positions = fetch_positions_okx(symbol)
        
        # 格式化持仓数据
        formatted_positions = []
        for pos in positions:
            # 安全的float转换函数，处理None值
            def safe_float(value, default=0):
                try:
                    return float(value) if value is not None else default
                except (ValueError, TypeError):
                    return default
            
            formatted_positions.append({
                'symbol': pos.get('symbol'),
                'side': pos.get('side'),  # 'long' or 'short'
                'contracts': safe_float(pos.get('contracts'), 0),
                'contractSize': safe_float(pos.get('contractSize'), 1),
                'notional': safe_float(pos.get('notional'), 0),
                'leverage': safe_float(pos.get('leverage'), 1),
                'unrealizedPnl': safe_float(pos.get('unrealizedPnl'), 0),
                'percentage': safe_float(pos.get('percentage'), 0),
                'entryPrice': safe_float(pos.get('entryPrice'), 0),
                'markPrice': safe_float(pos.get('markPrice'), 0),
                'liquidationPrice': safe_float(pos.get('liquidationPrice'), 0),
                'marginMode': pos.get('marginMode'),
                'timestamp': pos.get('timestamp'),
                'datetime': pos.get('datetime')
            })
        
        return {
            "success": True,
            "positions": formatted_positions,
            "count": len(formatted_positions),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch OKX positions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch positions: {str(e)}")


@router.get("/orders/open")
async def get_okx_open_orders(symbol: Optional[str] = None):
    """
    获取OKX未完成订单
    
    Args:
        symbol: 可选，指定交易对（如BTC）
        
    Returns:
        未完成订单列表
    """
    if not is_okx_trading_enabled():
        raise HTTPException(status_code=400, detail="OKX API not configured")
    
    try:
        orders = fetch_open_orders_okx(symbol)
        
        # 格式化订单数据
        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                'id': order.get('id'),
                'clientOrderId': order.get('clientOrderId'),
                'symbol': order.get('symbol'),
                'type': order.get('type'),  # 'market', 'limit'
                'side': order.get('side'),  # 'buy', 'sell'
                'price': float(order.get('price', 0)),
                'amount': float(order.get('amount', 0)),
                'filled': float(order.get('filled', 0)),
                'remaining': float(order.get('remaining', 0)),
                'status': order.get('status'),
                'timestamp': order.get('timestamp'),
                'datetime': order.get('datetime')
            })
        
        return {
            "success": True,
            "orders": formatted_orders,
            "count": len(formatted_orders),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch OKX open orders: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch open orders: {str(e)}")


@router.get("/orders/history")
async def get_okx_order_history(
    symbol: Optional[str] = None,
    limit: int = 100,
    days: int = 7
):
    """
    获取OKX历史订单
    
    Args:
        symbol: 可选，指定交易对（如BTC）
        limit: 返回数量限制
        days: 查询最近N天的订单
        
    Returns:
        历史订单列表
    """
    if not is_okx_trading_enabled():
        raise HTTPException(status_code=400, detail="OKX API not configured")
    
    try:
        # 计算起始时间戳（毫秒）
        since = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
        
        orders = fetch_closed_orders_okx(symbol, since, limit)
        
        # 格式化订单数据
        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                'id': order.get('id'),
                'clientOrderId': order.get('clientOrderId'),
                'symbol': order.get('symbol'),
                'type': order.get('type'),
                'side': order.get('side'),
                'price': float(order.get('price', 0)),
                'amount': float(order.get('amount', 0)),
                'filled': float(order.get('filled', 0)),
                'remaining': float(order.get('remaining', 0)),
                'cost': float(order.get('cost', 0)),
                'average': float(order.get('average', 0)),
                'status': order.get('status'),
                'fee': order.get('fee'),
                'timestamp': order.get('timestamp'),
                'datetime': order.get('datetime')
            })
        
        return {
            "success": True,
            "orders": formatted_orders,
            "count": len(formatted_orders),
            "days": days,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch OKX order history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch order history: {str(e)}")


@router.get("/trades")
async def get_okx_trades(
    symbol: Optional[str] = None,
    limit: int = 100,
    days: int = 7
):
    """
    获取OKX交易记录
    
    Args:
        symbol: 可选，指定交易对（如BTC）
        limit: 返回数量限制
        days: 查询最近N天的交易
        
    Returns:
        交易记录列表
    """
    if not is_okx_trading_enabled():
        raise HTTPException(status_code=400, detail="OKX API not configured")
    
    try:
        # 计算起始时间戳（毫秒）
        since = int((datetime.utcnow() - timedelta(days=days)).timestamp() * 1000)
        
        trades = fetch_my_trades_okx(symbol, since, limit)
        
        # 格式化交易数据
        formatted_trades = []
        for trade in trades:
            formatted_trades.append({
                'id': trade.get('id'),
                'order': trade.get('order'),
                'symbol': trade.get('symbol'),
                'type': trade.get('type'),
                'side': trade.get('side'),
                'price': float(trade.get('price', 0)),
                'amount': float(trade.get('amount', 0)),
                'cost': float(trade.get('cost', 0)),
                'fee': trade.get('fee'),
                'timestamp': trade.get('timestamp'),
                'datetime': trade.get('datetime')
            })
        
        return {
            "success": True,
            "trades": formatted_trades,
            "count": len(formatted_trades),
            "days": days,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch OKX trades: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch trades: {str(e)}")


@router.get("/summary")
async def get_okx_account_summary():
    """
    获取OKX账户概览
    
    Returns:
        账户概览，包括余额、持仓、订单统计
    """
    if not is_okx_trading_enabled():
        raise HTTPException(status_code=400, detail="OKX API not configured")
    
    try:
        # 获取余额
        balance = fetch_balance_okx()
        
        # 获取持仓
        positions = fetch_positions_okx()
        
        # 获取未完成订单
        open_orders = fetch_open_orders_okx()
        
        # 计算总资产（USDT计价）
        total_usdt = float(balance['total'].get('USDT', 0))
        
        # 计算持仓价值
        positions_value = sum(float(p.get('notional', 0)) for p in positions)
        
        # 计算未实现盈亏
        unrealized_pnl = sum(float(p.get('unrealizedPnl', 0)) for p in positions)
        
        return {
            "success": True,
            "summary": {
                "total_balance_usdt": total_usdt,
                "positions_value": positions_value,
                "unrealized_pnl": unrealized_pnl,
                "positions_count": len(positions),
                "open_orders_count": len(open_orders),
                "free_usdt": float(balance['free'].get('USDT', 0)),
                "used_usdt": float(balance['used'].get('USDT', 0))
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch OKX account summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch account summary: {str(e)}")


@router.post("/order")
async def place_okx_order(order_request: OKXOrderRequest):
    """
    在OKX上下单
    
    Args:
        order_request: 订单请求参数
        
    Returns:
        订单结果
    """
    if not is_okx_trading_enabled():
        raise HTTPException(status_code=400, detail="OKX API not configured")
    
    try:
        # 验证参数
        if order_request.side.lower() not in ['buy', 'sell']:
            raise HTTPException(status_code=400, detail="Invalid side, must be 'buy' or 'sell'")
        
        if order_request.order_type.lower() not in ['market', 'limit']:
            raise HTTPException(status_code=400, detail="Invalid order_type, must be 'market' or 'limit'")
        
        if order_request.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")
        
        if order_request.order_type.lower() == 'limit' and (not order_request.price or order_request.price <= 0):
            raise HTTPException(status_code=400, detail="Limit order requires valid price")
        
        logger.info(f"Placing OKX order: {order_request.side} {order_request.quantity} {order_request.symbol} @ {order_request.order_type}")
        
        # 调用OKX交易执行器
        result = create_okx_order(
            symbol=order_request.symbol,
            side=order_request.side.lower(),
            order_type=order_request.order_type.lower(),
            amount=order_request.quantity,
            price=order_request.price
        )
        
        if result.get('success'):
            logger.info(f"OKX order placed successfully: {result.get('order_id')}")
            return {
                "success": True,
                "order_id": result.get('order_id'),
                "order": result.get('order'),
                "message": "Order placed successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            logger.error(f"OKX order failed: {result.get('error')}")
            return {
                "success": False,
                "error": result.get('error'),
                "message": "Failed to place order",
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Failed to place OKX order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to place order: {str(e)}")
