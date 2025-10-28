"""
Trading Commands Service - Handles order execution and trading logic
使用OKX真实交易API执行订单
"""
import logging
import random
from decimal import Decimal
from typing import Dict, Optional, Tuple, List
from datetime import datetime

from sqlalchemy.orm import Session

from database.connection import SessionLocal
from database.models import Position, Account, Order, Trade
from services.asset_calculator import calc_positions_value
from services.market_data import get_last_price
from services.okx_trading_executor import create_okx_order  # 使用OKX真实交易
from services.ai_decision_service import (
    call_ai_for_decision, 
    save_ai_decision, 
    get_active_ai_accounts, 
    _get_portfolio_data,
    SUPPORTED_SYMBOLS
)


logger = logging.getLogger(__name__)

AI_TRADING_SYMBOLS: List[str] = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE"]


async def _notify_account_update(account_id: int):
    """
    通知WebSocket客户端账户数据已更新
    在AI交易完成后触发快照更新
    """
    try:
        from api.ws import manager, _send_snapshot
        db = SessionLocal()
        try:
            await _send_snapshot(db, account_id)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to send WebSocket update for account {account_id}: {e}")


def _save_okx_order_to_db(
    db: Session,
    account: Account,
    okx_result: Dict,
    symbol: str,
    name: str,
    side: str,
    quantity: float,
    order_type: str = "market",
    price: Optional[float] = None
) -> Optional[Tuple[Order, Trade]]:
    """
    保存OKX订单到本地数据库，以便前端显示
    
    Args:
        db: 数据库会话
        account: 账户对象
        okx_result: OKX API返回的结果
        symbol: 交易对符号 (e.g., "BTC-USDT-SWAP")
        name: 币种名称 (e.g., "Bitcoin")
        side: 'buy' or 'sell'
        quantity: 数量
        order_type: 'market' or 'limit'
        price: 价格（如果是限价单）
    
    Returns:
        (Order, Trade) 元组，如果保存失败则返回None
    """
    try:
        # 生成唯一订单号
        import uuid
        order_no = f"OKX-{uuid.uuid4().hex[:16].upper()}"
        
        # 从OKX结果中提取信息
        okx_order_id = okx_result.get('order_id')
        okx_price = okx_result.get('price')  # OKX返回的实际成交价
        
        # 如果OKX返回了价格，使用OKX的价格；否则查询市场价
        if okx_price:
            execution_price = float(okx_price)
        else:
            # 查询当前市场价（去掉-USDT-SWAP后缀）
            base_symbol = symbol.split('-')[0]
            try:
                execution_price = get_last_price(base_symbol, "CRYPTO")
            except:
                # 如果价格查询失败，使用传入的价格或默认值
                execution_price = price if price else 0.0
        
        # 创建订单记录
        order = Order(
            account_id=account.id,
            order_no=order_no,
            symbol=symbol,
            name=name,
            market="CRYPTO",
            side=side.upper(),
            order_type=order_type.upper(),
            price=Decimal(str(execution_price)) if execution_price else None,
            quantity=Decimal(str(quantity)),
            filled_quantity=Decimal(str(quantity)),  # 市价单立即完全成交
            status="FILLED",  # OKX成功返回表示已成交
            created_at=datetime.now()
        )
        db.add(order)
        db.flush()  # 刷新以获取order.id
        
        # 创建成交记录
        commission = Decimal(str(quantity * execution_price * 0.0005))  # 假设手续费率0.05%
        trade = Trade(
            order_id=order.id,
            account_id=account.id,
            symbol=symbol,
            name=name,
            market="CRYPTO",
            side=side.upper(),
            price=Decimal(str(execution_price)),
            quantity=Decimal(str(quantity)),
            commission=commission,
            trade_time=datetime.now()
        )
        db.add(trade)
        db.commit()
        
        logger.info(
            f"✅ Saved OKX order to database: order_id={order.id}, "
            f"trade_id={trade.id}, okx_order_id={okx_order_id}"
        )
        
        return (order, trade)
        
    except Exception as e:
        logger.error(f"Failed to save OKX order to database: {e}", exc_info=True)
        db.rollback()
        return None


def _get_market_prices(symbols: List[str]) -> Dict[str, float]:
    """Get latest prices for given symbols"""
    prices = {}
    for symbol in symbols:
        try:
            price = float(get_last_price(symbol, "CRYPTO"))
            if price > 0:
                prices[symbol] = price
        except Exception as err:
            logger.warning(f"Failed to get price for {symbol}: {err}")
    return prices


def _select_side(db: Session, account: Account, symbol: str, max_value: float) -> Optional[Tuple[str, int]]:
    """Select random trading side and quantity for legacy random trading"""
    market = "CRYPTO"
    try:
        price = float(get_last_price(symbol, market))
    except Exception as err:
        logger.warning("Cannot get price for %s: %s", symbol, err)
        return None

    if price <= 0:
        logger.debug("%s returned non-positive price %s", symbol, price)
        return None

    max_quantity_by_value = int(Decimal(str(max_value)) // Decimal(str(price)))
    position = (
        db.query(Position)
        .filter(Position.account_id == account.id, Position.symbol == symbol, Position.market == market)
        .first()
    )
    available_quantity = int(position.available_quantity) if position else 0

    choices = []

    if float(account.current_cash) >= price and max_quantity_by_value >= 1:
        choices.append(("BUY", max_quantity_by_value))

    if available_quantity > 0:
        max_sell_quantity = min(available_quantity, max_quantity_by_value if max_quantity_by_value >= 1 else available_quantity)
        if max_sell_quantity >= 1:
            choices.append(("SELL", max_sell_quantity))

    if not choices:
        return None

    side, max_qty = random.choice(choices)
    quantity = random.randint(1, max_qty)
    return side, quantity


def place_ai_driven_crypto_order(max_ratio: float = 0.2) -> None:
    """Place crypto order based on AI model decision for all active accounts"""
    db = SessionLocal()
    try:
        accounts = get_active_ai_accounts(db)
        if not accounts:
            logger.debug("No available accounts, skipping AI trading")
            return

        # Get latest market prices once for all accounts
        prices = _get_market_prices(AI_TRADING_SYMBOLS)
        if not prices:
            logger.warning("Failed to fetch market prices, skipping AI trading")
            return

        # Iterate through all active accounts
        for account in accounts:
            try:
                logger.info(f"Processing AI trading for account: {account.name}")
                
                # Get portfolio data for this account
                portfolio = _get_portfolio_data(db, account)
                
                if portfolio['total_assets'] <= 0:
                    logger.debug(f"Account {account.name} has non-positive total assets, skipping")
                    continue

                # Call AI for trading decision
                decision = call_ai_for_decision(account, portfolio, prices)
                if not decision or not isinstance(decision, dict):
                    logger.warning(f"Failed to get AI decision for {account.name}, skipping")
                    continue

                operation = decision.get("operation", "").lower() if decision.get("operation") else ""
                symbol = decision.get("symbol", "").upper() if decision.get("symbol") else ""
                target_portion = float(decision.get("target_portion_of_balance", 0)) if decision.get("target_portion_of_balance") is not None else 0
                reason = decision.get("reason", "No reason provided")

                logger.info(f"AI decision for {account.name}: {operation} {symbol} (portion: {target_portion:.2%}) - {reason}")

                # Validate decision
                if operation not in ["buy", "sell", "hold"]:
                    logger.warning(f"Invalid operation '{operation}' from AI for {account.name}, skipping")
                    # Save invalid decision for debugging
                    save_ai_decision(db, account, decision, portfolio, executed=False)
                    continue
                
                if operation == "hold":
                    logger.info(f"AI decided to HOLD for {account.name}")
                    # Save hold decision
                    save_ai_decision(db, account, decision, portfolio, executed=True)
                    continue

                if symbol not in SUPPORTED_SYMBOLS:
                    logger.warning(f"Invalid symbol '{symbol}' from AI for {account.name}, skipping")
                    # Save invalid decision for debugging
                    save_ai_decision(db, account, decision, portfolio, executed=False)
                    continue

                if target_portion <= 0 or target_portion > 1:
                    logger.warning(f"Invalid target_portion {target_portion} from AI for {account.name}, skipping")
                    # Save invalid decision for debugging
                    save_ai_decision(db, account, decision, portfolio, executed=False)
                    continue

                # Get current price
                price = prices.get(symbol)
                if not price or price <= 0:
                    logger.warning(f"Invalid price for {symbol} for {account.name}, skipping")
                    # Save decision with execution failure
                    save_ai_decision(db, account, decision, portfolio, executed=False)
                    continue

                # Calculate quantity based on operation
                if operation == "buy":
                    # Calculate quantity based on available cash and target portion
                    available_cash = float(account.current_cash)
                    order_value = available_cash * target_portion
                    # For crypto, support fractional quantities - use float instead of int
                    quantity = float(Decimal(str(order_value)) / Decimal(str(price)))
                    
                    # Round to reasonable precision (6 decimal places for crypto)
                    quantity = round(quantity, 6)
                    
                    if quantity <= 0:
                        logger.info(f"Calculated BUY quantity <= 0 for {symbol} for {account.name}, skipping")
                        # Save decision with execution failure
                        save_ai_decision(db, account, decision, portfolio, executed=False)
                        continue
                    
                    side = "BUY"

                elif operation == "sell":
                    # Calculate quantity based on position and target portion
                    position = (
                        db.query(Position)
                        .filter(Position.account_id == account.id, Position.symbol == symbol, Position.market == "CRYPTO")
                        .first()
                    )
                    
                    if not position or float(position.available_quantity) <= 0:
                        logger.info(f"No position available to SELL for {symbol} for {account.name}, skipping")
                        # Save decision with execution failure
                        save_ai_decision(db, account, decision, portfolio, executed=False)
                        continue
                    
                    available_quantity = int(position.available_quantity)
                    quantity = max(1, int(available_quantity * target_portion))
                    
                    if quantity > available_quantity:
                        quantity = available_quantity
                    
                    side = "SELL"
                
                else:
                    continue

                # 从AI决策中获取杠杆倍数
                leverage = int(decision.get("leverage", 3))  # 默认3倍杠杆
                if leverage < 1:
                    leverage = 1
                elif leverage > 125:
                    leverage = 125
                
                # 直接通过OKX API执行订单（真实交易）
                name = SUPPORTED_SYMBOLS[symbol]
                okx_symbol = f"{symbol}-USDT-SWAP"  # OKX永续合约格式
                ccxt_symbol = f"{symbol}/USDT:USDT"  # CCXT格式
                
                logger.info(f"Executing OKX order: {side} {quantity} {okx_symbol} with {leverage}x leverage")
                
                # 在下单前设置杠杆
                from services.okx_market_data import set_leverage_okx
                leverage_result = set_leverage_okx(
                    symbol=ccxt_symbol,
                    leverage=leverage,
                    margin_mode='cross'  # 使用全仓模式
                )
                
                if not leverage_result.get('success'):
                    logger.warning(f"Failed to set leverage for {symbol}: {leverage_result.get('error')}")
                    # 继续执行订单，即使杠杆设置失败
                else:
                    logger.info(f"Successfully set {leverage}x leverage for {symbol}")
                
                # 调用OKX API下单
                result = create_okx_order(
                    symbol=okx_symbol,
                    side=side.lower(),
                    amount=quantity,
                    order_type="market",  # AI交易使用市价单
                    price=None
                )
                
                if result.get('success'):
                    logger.info(
                        f"✅ OKX AI order executed: {side} {quantity} {symbol} @ {leverage}x leverage "
                        f"order_id={result.get('order_id')} reason='{reason}'"
                    )
                    
                    # 保存订单到本地数据库，以便前端显示
                    saved = _save_okx_order_to_db(
                        db=db,
                        account=account,
                        okx_result=result,
                        symbol=okx_symbol,
                        name=name,
                        side=side.lower(),
                        quantity=quantity,
                        order_type="market"
                    )
                    
                    # 保存AI决策记录（executed=True）
                    order_id = saved[0].id if saved else None
                    save_ai_decision(db, account, decision, portfolio, executed=True, order_id=order_id)
                    
                    # 触发WebSocket通知，让前端实时更新
                    if saved:
                        try:
                            from api.ws import manager
                            import asyncio
                            # 检查是否有运行的事件循环
                            try:
                                loop = asyncio.get_running_loop()
                                # 在运行的事件循环中创建任务
                                asyncio.create_task(_notify_account_update(account.id))
                            except RuntimeError:
                                # 没有运行的事件循环，使用 run_coroutine_threadsafe
                                try:
                                    loop = asyncio.get_event_loop()
                                    if loop.is_running():
                                        asyncio.run_coroutine_threadsafe(_notify_account_update(account.id), loop)
                                    else:
                                        # 事件循环未运行，跳过 WebSocket 通知
                                        logger.debug("Event loop not running, skipping WebSocket notification")
                                except Exception:
                                    logger.debug("No event loop available, skipping WebSocket notification")
                        except Exception as notify_err:
                            logger.debug(f"WebSocket notification skipped: {notify_err}")
                    
                else:
                    logger.error(
                        f"❌ OKX AI order failed: {side} {quantity} {symbol} "
                        f"error={result.get('error')}"
                    )
                    # 保存失败的决策
                    save_ai_decision(db, account, decision, portfolio, executed=False, order_id=None)

            except Exception as account_err:
                logger.error(f"AI-driven order placement failed for account {account.name}: {account_err}", exc_info=True)
                # Continue with next account even if one fails

    except Exception as err:
        logger.error(f"AI-driven order placement failed: {err}", exc_info=True)
        db.rollback()
    finally:
        db.close()


def place_random_crypto_order(max_ratio: float = 0.2) -> None:
    """
    Legacy random order placement - DEPRECATED
    已废弃：现在所有交易都通过OKX真实API执行，不再支持随机模拟交易
    """
    logger.warning("place_random_crypto_order is deprecated. All trading now uses OKX API via AI decisions.")
    pass  # 不再执行随机模拟交易


AUTO_TRADE_JOB_ID = "auto_crypto_trade"
AI_TRADE_JOB_ID = "ai_crypto_trade"