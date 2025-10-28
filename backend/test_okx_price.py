"""
Test OKX Price Fetching
验证OKX价格获取功能
"""
import os
import asyncio
from dotenv import load_dotenv
from services.okx_market_data import OKXClient

# 加载环境变量
load_dotenv()

async def test_price_fetching():
    """测试价格获取"""
    print("="*60)
    print("OKX Price Fetching Test")
    print("="*60)
    
    # 创建OKX客户端
    client = OKXClient()
    
    # 测试的交易对
    test_symbols = ['BTC', 'ETH', 'SOL', 'BNB', 'DOGE', 'XRP']
    
    print("\n测试价格获取（公开API，无需认证）:")
    print("-"*60)
    
    for symbol in test_symbols:
        try:
            price = client.get_last_price(symbol)
            if price:
                print(f"✅ {symbol:6s} : ${price:,.2f}")
            else:
                print(f"❌ {symbol:6s} : 获取失败")
        except Exception as e:
            print(f"❌ {symbol:6s} : 错误 - {e}")
    
    print("\n"+"="*60)
    print("测试完成!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_price_fetching())
