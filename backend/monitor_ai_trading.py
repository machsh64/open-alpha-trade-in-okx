"""
实时监控AI交易执行
查看最近的AI决策记录
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import SessionLocal
from database.models import AIDecisionLog
from sqlalchemy import desc
from datetime import datetime, timedelta

db = SessionLocal()

print("=" * 80)
print("📊 AI交易执行历史")
print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# 查询最近的AI决策记录
recent_decisions = db.query(AIDecisionLog).order_by(
    desc(AIDecisionLog.created_at)
).limit(10).all()

if not recent_decisions:
    print("\n❌ 没有找到任何AI决策记录!")
    print("\n可能原因:")
    print("  1. AI交易任务未启动")
    print("  2. 还没有到第一次执行时间")
    print("  3. AI账户配置有问题")
    print("\n检查步骤:")
    print("  1. 确认后端服务正在运行")
    print("  2. 查看后端启动日志，确认看到:")
    print("     'Automatic AI trading task started (X-minute interval)'")
    print("  3. 等待足够的时间（根据AI_TRADE_INTERVAL设置）")
else:
    print(f"\n✅ 找到 {len(recent_decisions)} 条最近的AI决策:\n")
    
    for i, decision in enumerate(recent_decisions, 1):
        time_ago = datetime.now() - decision.created_at
        minutes_ago = int(time_ago.total_seconds() / 60)
        
        print(f"{i}. {decision.created_at.strftime('%Y-%m-%d %H:%M:%S')} ({minutes_ago}分钟前)")
        print(f"   账户ID: {decision.account_id}")
        print(f"   操作: {decision.operation or 'N/A'}")
        print(f"   币种: {decision.symbol or 'N/A'}")
        print(f"   目标比例: {float(decision.target_portion or 0):.1%}")
        print(f"   执行状态: {'✅ 已执行' if decision.executed == 'true' else '❌ 未执行'}")
        print(f"   原因: {decision.reason[:80] if decision.reason else 'N/A'}...")
        print("-" * 80)
    
    # 计算最近一次决策距离现在的时间
    last_decision_time = recent_decisions[0].created_at
    time_since_last = datetime.now() - last_decision_time
    minutes_since_last = int(time_since_last.total_seconds() / 60)
    
    print(f"\n⏰ 距离上次AI决策: {minutes_since_last} 分钟")
    
    # 检查AI_TRADE_INTERVAL设置
    ai_interval = int(os.getenv('AI_TRADE_INTERVAL', '1800'))
    interval_minutes = ai_interval // 60
    print(f"⚙️  配置的执行间隔: {interval_minutes} 分钟 ({ai_interval} 秒)")
    
    if minutes_since_last >= interval_minutes:
        print(f"\n⚠️  警告: 已经超过配置的间隔时间，但没有新的决策记录")
        print("   可能原因:")
        print("   1. 后端服务重启了（调度器会重新开始计时）")
        print("   2. 调度器出现问题")
        print("   3. AI决策函数执行失败")
    else:
        remaining = interval_minutes - minutes_since_last
        print(f"\n✅ 正常运行中，预计 {remaining} 分钟后执行下一次AI决策")

db.close()

print("\n" + "=" * 80)
print("💡 提示:")
print(f"  - 当前配置: 每 {int(os.getenv('AI_TRADE_INTERVAL', '1800')) // 60} 分钟执行一次AI决策")
print("  - 可以在 backend/.env 中修改 AI_TRADE_INTERVAL 调整间隔")
print("  - 重新运行此脚本查看最新状态")
print("=" * 80)
