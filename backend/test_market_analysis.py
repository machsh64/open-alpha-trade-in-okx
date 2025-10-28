"""
测试市场分析功能
展示增强后的AI决策数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.okx_market_data import get_market_analysis
import json

print("=" * 80)
print("市场技术分析测试")
print("=" * 80)

# 测试 BTC 的市场分析
symbol = "BTC"
print(f"\n正在获取 {symbol} 的市场分析数据（过去7天的小时线）...\n")

analysis = get_market_analysis(symbol, period="1h", count=168)

if "error" in analysis:
    print(f"错误: {analysis['error']}")
else:
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 80)
    print("分析摘要:")
    print("=" * 80)
    print(f"当前价格: ${analysis['current_price']}")
    print(f"24小时变化: {analysis['price_changes']['24h_percent']}%")
    print(f"7天变化: {analysis['price_changes']['7d_percent']}%")
    print(f"\n移动平均线:")
    print(f"  SMA(7):  ${analysis['moving_averages']['sma_7']}")
    print(f"  SMA(25): ${analysis['moving_averages']['sma_25']}")
    print(f"  SMA(99): ${analysis['moving_averages']['sma_99']}")
    print(f"\n技术指标:")
    print(f"  RSI(14): {analysis['technical_indicators']['rsi_14']}", end="")
    rsi = analysis['technical_indicators']['rsi_14']
    if rsi:
        if rsi > 70:
            print(" (超买)")
        elif rsi < 30:
            print(" (超卖)")
        else:
            print(" (中性)")
    print(f"  趋势: {analysis['technical_indicators']['trend']}")
    print(f"  波动率: {analysis['technical_indicators']['volatility_24h']}%")
    print(f"\n支撑/阻力位:")
    print(f"  24小时最高: ${analysis['support_resistance']['recent_high_24h']}")
    print(f"  24小时最低: ${analysis['support_resistance']['recent_low_24h']}")
    print(f"  距离最高: {analysis['support_resistance']['distance_from_high']}%")
    print(f"  距离最低: {analysis['support_resistance']['distance_from_low']}%")
    print(f"\n成交量分析:")
    print(f"  当前成交量: {analysis['volume_analysis']['current_volume']:.2f}")
    print(f"  24小时平均: {analysis['volume_analysis']['avg_volume_24h']:.2f}")
    print(f"  成交量比: {analysis['volume_analysis']['volume_ratio']:.2f}x")
    
    print(f"\n最近趋势 (最后5根K线):")
    for candle in analysis['recent_candles'][-5:]:
        direction = "↑" if candle['change'] > 0 else "↓"
        print(f"  {candle['time']}: ${candle['close']} ({direction} {candle['change']:+.2f}%)")

print("\n" + "=" * 80)
print("这些数据现在会被发送给AI，帮助它做出更明智的交易决策！")
print("=" * 80)
