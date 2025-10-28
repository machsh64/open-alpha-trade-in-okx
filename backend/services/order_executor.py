import uuid
import os
from decimal import Decimal
from sqlalchemy.orm import Session
from database.models import Order, Position, Trade, User, US_MIN_COMMISSION, US_COMMISSION_RATE, US_MIN_ORDER_QUANTITY, US_LOT_SIZE
from .market_data import get_last_price
from .okx_trading_executor import (
    is_okx_trading_enabled,
    create_okx_order,
    get_okx_order_status
)
import logging

logger = logging.getLogger(__name__)


def _calc_commission(notional: Decimal) -> Decimal:
    pct_fee = notional * Decimal(str(US_COMMISSION_RATE))
    min_fee = Decimal(str(US_MIN_COMMISSION))
    return max(pct_fee, min_fee)

def place_and_execute(db: Session, user: User, symbol: str, name: str, market: str, side: str, order_type: str, price: float | None, quantity: int) -> Order:
    # 支持CRYPTO市场（OKX）和US市场（模拟交易）
    if market not in ["US", "CRYPTO"]:
        raise ValueError("Only US and CRYPTO markets are supported")

    # 检查是否启用真实交易
    use_real_trading = market == "CRYPTO" and is_okx_trading_enabled()
    
    # 获取市场配置
    if market == "CRYPTO":
        min_commission = 0.1
        commission_rate = 0.001  # 0.1%
        min_order_quantity = 1
        lot_size = 1
    else:  # US market
        min_commission = US_MIN_COMMISSION
        commission_rate = US_COMMISSION_RATE
        min_order_quantity = US_MIN_ORDER_QUANTITY
        lot_size = US_LOT_SIZE

    # Adjust quantity to lot size
    if quantity % lot_size != 0:
        raise ValueError(f"quantity must be a multiple of lot_size={lot_size}")
    if quantity < min_order_quantity:
        raise ValueError(f"quantity must be >= min_order_quantity={min_order_quantity}")

    # 创建订单记录
    order = Order(
        version="v1",
        user_id=user.id,
        order_no=uuid.uuid4().hex[:16],
        symbol=symbol,
        name=name,
        market=market,
        side=side,
        order_type=order_type,
        price=price,
        quantity=quantity,
        filled_quantity=0,
        status="PENDING",
    )
    db.add(order)
    db.flush()

    try:
        if use_real_trading:
            # 使用OKX真实交易
            logger.info(f"Executing real trade on OKX: {side} {quantity} {symbol}")
            
            # 转换订单类型
            okx_order_type = "market" if order_type == "MARKET" else "limit"
            okx_side = side.lower()
            
            # 执行OKX订单
            okx_result = create_okx_order(
                symbol=symbol,
                side=okx_side,
                amount=float(quantity),
                order_type=okx_order_type,
                price=price if order_type == "LIMIT" else None
            )
            
            if okx_result.get('success'):
                # 获取实际执行价格
                okx_order_id = okx_result.get('order_id')
                order_status = get_okx_order_status(okx_order_id, symbol)
                
                if order_status.get('success'):
                    exec_price = Decimal(str(order_status.get('average_price') or order_status.get('price') or price))
                    filled_qty = int(order_status.get('filled', 0))
                    
                    order.status = "FILLED" if filled_qty == quantity else "PARTIALLY_FILLED"
                    order.filled_quantity = filled_qty
                    order.price = float(exec_price)
                    order.external_order_id = okx_order_id
                    
                    logger.info(f"OKX order executed: {okx_order_id}, price: {exec_price}, filled: {filled_qty}")
                else:
                    logger.error(f"Failed to get OKX order status: {order_status.get('error')}")
                    order.status = "UNKNOWN"
            else:
                logger.error(f"OKX order failed: {okx_result.get('error')}")
                order.status = "FAILED"
                db.commit()
                raise ValueError(f"OKX order execution failed: {okx_result.get('error')}")
                
        else:
            # 模拟交易执行
            exec_price = Decimal(str(price if (order_type == "LIMIT" and price) else get_last_price(symbol, market)))
            order.price = float(exec_price)
            order.filled_quantity = quantity
            order.status = "FILLED"
            logger.info(f"Simulated trade executed: {side} {quantity} {symbol} at {exec_price}")

        # 计算手续费和更新资金/持仓
        exec_price = Decimal(str(order.price))
        filled_qty = order.filled_quantity
        
        if filled_qty > 0:
            notional = exec_price * Decimal(filled_qty)
            commission = max(notional * Decimal(str(commission_rate)), Decimal(str(min_commission)))

            if side == "BUY":
                cash_needed = notional + commission
                if Decimal(str(user.current_cash)) < cash_needed:
                    if not use_real_trading:  # 只有模拟交易才检查虚拟资金
                        raise ValueError("Insufficient USD cash")
                
                user.current_cash = float(Decimal(str(user.current_cash)) - cash_needed)
                
                # 更新持仓
                pos = (
                    db.query(Position)
                    .filter(Position.user_id == user.id, Position.symbol == symbol, Position.market == market)
                    .first()
                )
                if not pos:
                    pos = Position(
                        version="v1",
                        user_id=user.id,
                        symbol=symbol,
                        name=name,
                        market=market,
                        quantity=0,
                        available_quantity=0,
                        avg_cost=0,
                    )
                    db.add(pos)
                    db.flush()
                
                new_qty = int(pos.quantity) + filled_qty
                new_cost = (Decimal(str(pos.avg_cost)) * Decimal(int(pos.quantity)) + notional) / Decimal(new_qty)
                pos.quantity = new_qty
                pos.available_quantity = int(pos.available_quantity) + filled_qty
                pos.avg_cost = float(new_cost)
                
            else:  # SELL
                pos = (
                    db.query(Position)
                    .filter(Position.user_id == user.id, Position.symbol == symbol, Position.market == market)
                    .first()
                )
                if not use_real_trading and (not pos or int(pos.available_quantity) < filled_qty):
                    raise ValueError("Insufficient position to sell")
                
                if pos:
                    pos.quantity = max(0, int(pos.quantity) - filled_qty)
                    pos.available_quantity = max(0, int(pos.available_quantity) - filled_qty)
                
                cash_gain = notional - commission
                user.current_cash = float(Decimal(str(user.current_cash)) + cash_gain)

            # 创建交易记录
            trade = Trade(
                order_id=order.id,
                user_id=user.id,
                symbol=symbol,
                name=name,
                market=market,
                side=side,
                price=float(exec_price),
                quantity=filled_qty,
                commission=float(commission),
            )
            db.add(trade)

    except Exception as e:
        order.status = "FAILED"
        db.commit()
        logger.error(f"Order execution failed: {e}")
        raise

    db.commit()
    db.refresh(order)
    return order
