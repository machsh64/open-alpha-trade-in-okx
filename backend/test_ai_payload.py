"""
手动触发AI交易测试脚本
用于测试AI决策和payload打印
"""
import sys
import os

# 设置Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.trading_commands import place_ai_driven_crypto_order

if __name__ == "__main__":
    print("=" * 80)
    print("🤖 手动触发AI交易测试")
    print("=" * 80)
    print("\n开始执行AI交易决策...")
    print("注意: 请确保数据库中有配置了OpenAI API的AI账户\n")
    
    try:
        place_ai_driven_crypto_order()
        print("\n✅ AI交易测试完成!")
        print("请查看上面的日志，应该能看到完整的payload输出")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
