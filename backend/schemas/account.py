from pydantic import BaseModel
from typing import Optional


class AccountCreate(BaseModel):
    """Create a new AI Trading Account"""
    name: str  # Display name (e.g., "GPT Trader", "Claude Analyst")
    model: str = "gpt-4-turbo"
    base_url: str = "https://api.openai.com/v1"
    api_key: str
    
    # OKX Configuration
    okx_api_key: Optional[str] = None
    okx_secret: Optional[str] = None
    okx_passphrase: Optional[str] = None
    okx_sandbox: str = "true"
    
    initial_capital: float = 10000.0
    account_type: str = "AI"  # "AI" or "MANUAL"


class AccountUpdate(BaseModel):
    """Update AI Trading Account"""
    name: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    
    # OKX Configuration
    okx_api_key: Optional[str] = None
    okx_secret: Optional[str] = None
    okx_passphrase: Optional[str] = None
    okx_sandbox: Optional[str] = None


class AccountOut(BaseModel):
    """AI Trading Account output"""
    id: int
    user_id: int
    name: str
    model: str
    base_url: str
    api_key: str  # Will be masked in API responses
    
    # OKX Configuration
    okx_api_key: Optional[str] = None  # Will be masked in API responses
    okx_secret: Optional[str] = None  # Will be masked in API responses
    okx_passphrase: Optional[str] = None  # Will be masked in API responses
    okx_sandbox: str = "true"
    
    # Balance fields - optional because OKX accounts fetch real-time data
    initial_capital: Optional[float] = 0.0
    current_cash: Optional[float] = 0.0
    frozen_cash: Optional[float] = 0.0
    
    account_type: str
    is_active: bool

    class Config:
        from_attributes = True


class AccountOverview(BaseModel):
    """Account overview with portfolio information"""
    account: AccountOut
    total_assets: float  # Total assets in USD
    positions_value: float  # Total positions value in USD