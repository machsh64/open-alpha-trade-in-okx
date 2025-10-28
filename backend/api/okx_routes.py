"""
OKX Trading API routes
提供OKX交易相关的API接口
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from services.okx_trading_executor import (
    is_okx_trading_enabled,
    get_okx_balance,
    okx_trading_executor
)
from config.settings import OKX_CONFIG

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/okx", tags=["okx_trading"])


@router.get("/status")
async def get_okx_status() -> Dict[str, Any]:
    """
    获取OKX交易状态
    
    Returns:
        OKX配置和连接状态信息
    """
    try:
        is_enabled = is_okx_trading_enabled()
        
        status = {
            "trading_enabled": is_enabled,
            "sandbox_mode": OKX_CONFIG.sandbox,
            "api_configured": OKX_CONFIG.is_valid(),
            "exchange": "OKX",
            "supported_features": [
                "market_data",
                "spot_trading",
                "real_time_execution"
            ]
        }
        
        if is_enabled:
            status["status"] = "Ready for trading"
            status["message"] = "OKX API configured and ready"
        else:
            status["status"] = "Configuration required"
            status["message"] = "Please configure OKX API credentials in .env file"
            status["setup_instructions"] = [
                "1. Copy .env.example to .env",
                "2. Get API credentials from OKX exchange",
                "3. Fill in OKX_API_KEY, OKX_SECRET, OKX_PASSPHRASE",
                "4. Set OKX_SANDBOX=true for testing",
                "5. Restart the application"
            ]
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get OKX status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get OKX status: {str(e)}")


@router.get("/balance")
async def get_balance() -> Dict[str, Any]:
    """
    获取OKX账户余额
    
    Returns:
        账户余额信息
    """
    try:
        if not is_okx_trading_enabled():
            raise HTTPException(
                status_code=400, 
                detail="OKX trading not enabled. Please configure API credentials."
            )
        
        balance_result = get_okx_balance()
        
        if balance_result.get('success'):
            return {
                "success": True,
                "balances": balance_result.get('total', {}),
                "available": balance_result.get('free', {}),
                "locked": balance_result.get('used', {}),
                "timestamp": balance_result.get('timestamp'),
                "exchange": "OKX"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch balance: {balance_result.get('error')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get balance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get balance: {str(e)}")


@router.get("/config")
async def get_config() -> Dict[str, Any]:
    """
    获取OKX配置信息（隐藏敏感信息）
    
    Returns:
        配置信息
    """
    try:
        config_info = {
            "sandbox_mode": OKX_CONFIG.sandbox,
            "api_key_configured": bool(OKX_CONFIG.api_key),
            "secret_configured": bool(OKX_CONFIG.secret),
            "passphrase_configured": bool(OKX_CONFIG.passphrase),
            "exchange": "OKX",
            "base_currency": "USDT",
            "supported_markets": ["spot", "future", "swap"],
            "commission_rate": "0.1%",
        }
        
        if OKX_CONFIG.api_key:
            # 只显示API密钥的前4位和后4位
            masked_key = f"{OKX_CONFIG.api_key[:4]}...{OKX_CONFIG.api_key[-4:]}"
            config_info["api_key_preview"] = masked_key
        
        return config_info
        
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@router.post("/test-connection")
async def test_connection() -> Dict[str, Any]:
    """
    测试OKX连接
    
    Returns:
        连接测试结果
    """
    try:
        if not is_okx_trading_enabled():
            return {
                "success": False,
                "message": "OKX API credentials not configured",
                "exchange": "OKX"
            }
        
        # 尝试获取余额来测试连接
        balance_result = get_okx_balance()
        
        if balance_result.get('success'):
            return {
                "success": True,
                "message": "OKX connection successful",
                "exchange": "OKX",
                "sandbox_mode": OKX_CONFIG.sandbox,
                "timestamp": balance_result.get('timestamp')
            }
        else:
            return {
                "success": False,
                "message": f"OKX connection failed: {balance_result.get('error')}",
                "exchange": "OKX"
            }
            
    except Exception as e:
        logger.error(f"OKX connection test failed: {e}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "exchange": "OKX"
        }