"""
Test OKX Account Data Fetching
测试OKX账户数据获取：余额、持仓、订单、交易记录
"""
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from services.okx_market_data import (
    fetch_balance_okx,
    fetch_positions_okx,
    fetch_open_orders_okx,
    fetch_closed_orders_okx,
    fetch_my_trades_okx
)
from services.okx_trading_executor import is_okx_trading_enabled

def print_section(title):
    """打印分节标题"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_okx_account_data():
    """测试OKX账户数据获取"""
    print_section("OKX Account Data Test")
    
    # 检查API是否配置
    if not is_okx_trading_enabled():
        print("\n❌ OKX API未配置，请检查.env文件中的OKX_API_KEY、OKX_SECRET和OKX_PASSPHRASE")
        return
    
    print("\n✅ OKX API已配置")
    
    # 1. 获取余额
    print_section("1. 账户余额 (Balance)")
    try:
        balance = fetch_balance_okx()
        print("\n可用余额 (Free):")
        for currency, amount in balance.get('free', {}).items():
            if float(amount) > 0:
                print(f"  {currency}: {float(amount):.8f}")
        
        print("\n冻结余额 (Used):")
        for currency, amount in balance.get('used', {}).items():
            if float(amount) > 0:
                print(f"  {currency}: {float(amount):.8f}")
        
        print("\n总余额 (Total):")
        for currency, amount in balance.get('total', {}).items():
            if float(amount) > 0:
                print(f"  {currency}: {float(amount):.8f}")
        
        if not any(float(v) > 0 for v in balance.get('total', {}).values()):
            print("  (暂无余额)")
            
    except Exception as e:
        print(f"\n❌ 获取余额失败: {e}")
    
    # 2. 获取持仓
    print_section("2. 当前持仓 (Positions)")
    try:
        positions = fetch_positions_okx()
        
        if positions:
            for pos in positions:
                print(f"\n  交易对: {pos.get('symbol')}")
                print(f"  方向: {pos.get('side')} ({'多' if pos.get('side') == 'long' else '空'})")
                print(f"  数量: {pos.get('contracts')} 张")
                print(f"  价值: ${pos.get('notional', 0):.2f}")
                print(f"  杠杆: {pos.get('leverage')}x")
                print(f"  开仓价: ${pos.get('entryPrice', 0):.4f}")
                print(f"  标记价: ${pos.get('markPrice', 0):.4f}")
                print(f"  未实现盈亏: ${pos.get('unrealizedPnl', 0):.4f} ({pos.get('percentage', 0):.2f}%)")
        else:
            print("\n  (暂无持仓)")
            
    except Exception as e:
        print(f"\n❌ 获取持仓失败: {e}")
    
    # 3. 获取未完成订单
    print_section("3. 未完成订单 (Open Orders)")
    try:
        open_orders = fetch_open_orders_okx()
        
        if open_orders:
            for order in open_orders:
                print(f"\n  订单ID: {order.get('id')}")
                print(f"  交易对: {order.get('symbol')}")
                print(f"  类型: {order.get('type')} / {order.get('side')}")
                print(f"  价格: ${order.get('price', 0):.4f}")
                print(f"  数量: {order.get('amount')}")
                print(f"  已成交: {order.get('filled')} / 剩余: {order.get('remaining')}")
                print(f"  状态: {order.get('status')}")
                print(f"  时间: {order.get('datetime')}")
        else:
            print("\n  (暂无未完成订单)")
            
    except Exception as e:
        print(f"\n❌ 获取未完成订单失败: {e}")
    
    # 4. 获取历史订单
    print_section("4. 历史订单 (最近10条)")
    try:
        closed_orders = fetch_closed_orders_okx(limit=10)
        
        if closed_orders:
            for order in closed_orders:
                print(f"\n  订单ID: {order.get('id')}")
                print(f"  交易对: {order.get('symbol')}")
                print(f"  类型: {order.get('type')} / {order.get('side')}")
                print(f"  价格: ${order.get('price', 0):.4f}")
                print(f"  数量: {order.get('amount')}")
                print(f"  已成交: {order.get('filled')}")
                print(f"  成交均价: ${order.get('average', 0):.4f}")
                print(f"  成交额: ${order.get('cost', 0):.4f}")
                print(f"  状态: {order.get('status')}")
                print(f"  时间: {order.get('datetime')}")
        else:
            print("\n  (暂无历史订单)")
            
    except Exception as e:
        print(f"\n❌ 获取历史订单失败: {e}")
    
    # 5. 获取交易记录
    print_section("5. 交易记录 (最近10条)")
    try:
        trades = fetch_my_trades_okx(limit=10)
        
        if trades:
            for trade in trades:
                print(f"\n  交易ID: {trade.get('id')}")
                print(f"  订单ID: {trade.get('order')}")
                print(f"  交易对: {trade.get('symbol')}")
                print(f"  类型: {trade.get('side')}")
                print(f"  价格: ${trade.get('price', 0):.4f}")
                print(f"  数量: {trade.get('amount')}")
                print(f"  成交额: ${trade.get('cost', 0):.4f}")
                if trade.get('fee'):
                    print(f"  手续费: {trade['fee'].get('cost')} {trade['fee'].get('currency')}")
                print(f"  时间: {trade.get('datetime')}")
        else:
            print("\n  (暂无交易记录)")
            
    except Exception as e:
        print(f"\n❌ 获取交易记录失败: {e}")
    
    print_section("测试完成")
    print("\n提示: 如果显示'暂无数据'，说明您的OKX账户还没有进行过交易。")
    print("      您可以通过API接口 /api/okx-account/* 来访问这些数据。\n")

if __name__ == "__main__":
    test_okx_account_data()
