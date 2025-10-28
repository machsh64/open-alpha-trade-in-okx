"""
测试OKX数据获取
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.okx_market_data import fetch_balance_okx, fetch_positions_okx
import json

print("=" * 80)
print("📊 测试OKX账户数据获取")
print("=" * 80)

try:
    print("\n1️⃣ 获取OKX余额...")
    balance = fetch_balance_okx()
    print(f"Balance data type: {type(balance)}")
    print(f"Balance keys: {balance.keys() if isinstance(balance, dict) else 'N/A'}")
    print("\nBalance data:")
    print(json.dumps(balance, indent=2, default=str))
    
    print("\n" + "=" * 80)
    print("\n2️⃣ 获取OKX持仓...")
    positions = fetch_positions_okx()
    print(f"Positions data type: {type(positions)}")
    print(f"Positions count: {len(positions) if isinstance(positions, list) else 'N/A'}")
    if positions:
        print("\nFirst position:")
        print(json.dumps(positions[0], indent=2, default=str))
    else:
        print("No positions found")
    
    print("\n" + "=" * 80)
    print("\n✅ 测试完成！")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
