"""
测试交易对格式转换
"""
import sys
sys.path.append('.')

from services.okx_market_data import OKXClient

def test_symbol_format():
    client = OKXClient()
    
    test_cases = [
        ("BTC-USDT-SWAP", "BTC/USDT:USDT"),
        ("ETH-USDT-SWAP", "ETH/USDT:USDT"),
        ("BTC/USDT:USDT", "BTC/USDT:USDT"),
        ("BTC/USDT", "BTC/USDT:USDT"),
        ("BTC", "BTC/USDT:USDT"),
        ("eth-usdt-swap", "ETH/USDT:USDT"),  # 小写也会转换为大写
    ]
    
    print("Testing symbol format conversion:")
    print("=" * 60)
    
    all_passed = True
    for input_symbol, expected_output in test_cases:
        result = client._format_symbol(input_symbol)
        status = "✅" if result == expected_output else "❌"
        if result != expected_output:
            all_passed = False
        print(f"{status} {input_symbol:20} -> {result:20} (expected: {expected_output})")
    
    print("=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return all_passed

if __name__ == "__main__":
    test_symbol_format()
