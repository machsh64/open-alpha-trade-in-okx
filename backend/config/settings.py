from pydantic import BaseModel
from typing import Dict
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


class MarketConfig(BaseModel):
    market: str
    min_commission: float
    commission_rate: float
    exchange_rate: float
    min_order_quantity: int = 1
    lot_size: int = 1


class OKXConfig(BaseModel):
    """OKX交易所配置"""
    api_key: str = ""
    secret: str = ""
    passphrase: str = ""
    sandbox: bool = True  # 默认沙盒模式
    
    @classmethod
    def from_env(cls) -> "OKXConfig":
        """从环境变量加载OKX配置"""
        return cls(
            api_key=os.getenv('OKX_API_KEY', ''),
            secret=os.getenv('OKX_SECRET', ''),
            passphrase=os.getenv('OKX_PASSPHRASE', ''),
            sandbox=os.getenv('OKX_SANDBOX', 'true').lower() == 'true'
        )
    
    def is_valid(self) -> bool:
        """检查配置是否有效"""
        return bool(self.api_key and self.secret and self.passphrase)


# 全局OKX配置实例
OKX_CONFIG = OKXConfig.from_env()


class MarketConfig(BaseModel):
    market: str
    min_commission: float
    commission_rate: float
    exchange_rate: float
    min_order_quantity: int = 1
    lot_size: int = 1


#  default configs for CRYPTO markets (OKX focused)
DEFAULT_TRADING_CONFIGS: Dict[str, MarketConfig] = {
    "CRYPTO": MarketConfig(
        market="CRYPTO",
        min_commission=0.1,  # $0.1 minimum commission for crypto
        commission_rate=0.001,  # 0.1% commission rate (OKX typical rate)
        exchange_rate=1.0,  # USDT base
        min_order_quantity=1,  # Can trade fractional amounts
        lot_size=1,
    ),
}
