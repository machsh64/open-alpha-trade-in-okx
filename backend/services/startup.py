"""Application startup initialization service"""

import logging
import threading

from services.auto_trader import (
    place_ai_driven_crypto_order,
    place_random_crypto_order,
    AUTO_TRADE_JOB_ID,
    AI_TRADE_JOB_ID
)
from services.scheduler import start_scheduler, setup_market_tasks, task_scheduler

logger = logging.getLogger(__name__)


def initialize_services():
    """Initialize all services"""
    try:
        # Start the scheduler
        start_scheduler()
        logger.info("Scheduler service started")
        
        # Set up market-related scheduled tasks
        setup_market_tasks()
        logger.info("Market scheduled tasks have been set up")

        # Start automatic AI trading task
        # 默认每30分钟检查一次（而不是5分钟），AI可以决定是否真的交易
        # 可以通过环境变量 AI_TRADE_INTERVAL 来调整（单位：秒）
        import os
        ai_interval = int(os.getenv('AI_TRADE_INTERVAL', '1800'))  # 默认30分钟
        print(f"\n{'='*60}")
        print(f"[STARTUP] Starting AI Trading Scheduler")
        print(f"[STARTUP] AI_TRADE_INTERVAL = {ai_interval} seconds ({ai_interval // 60} minutes)")
        print(f"{'='*60}\n")
        schedule_auto_trading(interval_seconds=ai_interval)
        logger.info(f"Automatic AI trading task started ({ai_interval // 60}-minute interval)")
        print(f"[STARTUP] AI Trading task scheduled successfully!\n")
        
        # Add price cache cleanup task (every 2 minutes)
        from services.price_cache import clear_expired_prices
        task_scheduler.add_interval_task(
            task_func=clear_expired_prices,
            interval_seconds=120,  # Clean every 2 minutes
            task_id="price_cache_cleanup"
        )
        logger.info("Price cache cleanup task started (2-minute interval)")
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        raise


def shutdown_services():
    """Shut down all services"""
    try:
        from services.scheduler import stop_scheduler
        stop_scheduler()
        logger.info("All services have been shut down")
        
    except Exception as e:
        logger.error(f"Failed to shut down services: {e}")


async def startup_event():
    """FastAPI application startup event"""
    initialize_services()


async def shutdown_event():
    """FastAPI application shutdown event"""
    await shutdown_services()


def schedule_auto_trading(interval_seconds: int = 300, max_ratio: float = 0.2, use_ai: bool = True) -> None:
    """Schedule automatic trading tasks
    
    Args:
        interval_seconds: Interval between trading attempts
        max_ratio: Maximum portion of portfolio to use per trade
        use_ai: If True, use AI-driven trading; if False, use random trading
    """
    from services.auto_trader import (
        place_ai_driven_crypto_order,
        place_random_crypto_order,
        AUTO_TRADE_JOB_ID,
        AI_TRADE_JOB_ID
    )

    if use_ai:
        task_func = place_ai_driven_crypto_order
        job_id = AI_TRADE_JOB_ID
        logger.info("Scheduling AI-driven crypto trading")
    else:
        task_func = place_random_crypto_order
        job_id = AUTO_TRADE_JOB_ID
        logger.info("Scheduling random crypto trading")

    # Check if the job already exists to prevent duplicate scheduling
    if task_scheduler.scheduler and task_scheduler.scheduler.get_job(job_id):
        logger.warning(f"Trading job {job_id} already exists, skipping duplicate scheduling")
        return

    # Schedule the recurring task with replace_existing=True to prevent duplicates
    task_scheduler.add_interval_task(
        task_func=task_func,
        interval_seconds=interval_seconds,
        task_id=job_id,
        max_ratio=max_ratio,
    )
    
    logger.info(f"Auto trading job {job_id} scheduled successfully (interval: {interval_seconds}s)")