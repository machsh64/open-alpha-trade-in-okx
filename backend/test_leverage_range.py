"""
测试 AI 决策的杠杆范围
"""
import json

# 模拟 AI 响应测试
test_decisions = [
    {"leverage": 1, "desc": "最低杠杆"},
    {"leverage": 5, "desc": "保守杠杆"},
    {"leverage": 10, "desc": "中等杠杆"},
    {"leverage": 25, "desc": "激进杠杆"},
    {"leverage": 50, "desc": "最高杠杆"},
    {"leverage": 0, "desc": "无效杠杆（太低）"},
    {"leverage": 100, "desc": "无效杠杆（太高）"},
]

print("=" * 80)
print("AI 决策杠杆范围测试")
print("=" * 80)

for test in test_decisions:
    leverage = test["leverage"]
    
    # 验证逻辑（与代码中一致）
    if leverage < 1:
        validated_leverage = 1
    elif leverage > 50:
        validated_leverage = 50
    else:
        validated_leverage = leverage
    
    status = "✓ VALID" if leverage == validated_leverage else f"✗ ADJUSTED to {validated_leverage}x"
    
    print(f"\n{test['desc']}: {leverage}x")
    print(f"  验证后: {validated_leverage}x")
    print(f"  状态: {status}")

print("\n" + "=" * 80)
print("杠杆分级指南:")
print("=" * 80)
print("1-3x:    保守型 - 适合不确定市场或高波动")
print("4-10x:   稳健型 - 适合明确趋势且有确认信号")
print("11-25x:  激进型 - 需要很强的信念和多重确认信号")
print("26-50x:  极限型 - 仅用于特殊机会，有压倒性证据")
print("\n⚠️  警告：高杠杆会指数级放大盈亏！")
print("=" * 80)

# 模拟 AI JSON 响应
example_response = {
    "operation": "buy",
    "symbol": "BTC",
    "target_portion_of_balance": 0.3,
    "leverage": 20,
    "reason": "Strong bullish confluence: All timeframes positive (15m:+0.5%, 1h:+1.8%, 4h:+3.2%, 24h:+4.5%), RSI at 58 with room to grow, SMA7>SMA25>SMA99, volume 2.3x average, breakout above resistance at $67000. Using 20x leverage with 30% capital for high conviction setup."
}

print("\n示例 AI 决策（使用 20x 杠杆）:")
print(json.dumps(example_response, indent=2, ensure_ascii=False))
