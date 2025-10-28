"""
查看最近的 AI 决策日志和 prompt
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import SessionLocal
from database.models import AIDecisionLog, Account
from sqlalchemy import desc

db = SessionLocal()

print("=" * 80)
print("最近的 AI 决策日志（包含完整 prompt）")
print("=" * 80)

# 查询最近的决策
recent_decisions = db.query(AIDecisionLog).order_by(
    desc(AIDecisionLog.created_at)
).limit(3).all()

if not recent_decisions:
    print("\n没有找到 AI 决策记录")
else:
    for i, decision in enumerate(recent_decisions, 1):
        account = db.query(Account).filter(Account.id == decision.account_id).first()
        
        print(f"\n{'='*80}")
        print(f"决策 #{i}")
        print(f"{'='*80}")
        print(f"时间: {decision.created_at}")
        print(f"账户: {account.name if account else 'N/A'}")
        print(f"操作: {decision.operation}")
        print(f"币种: {decision.symbol or 'N/A'}")
        print(f"目标比例: {float(decision.target_portion):.2%}")
        print(f"杠杆: {decision.leverage}x" if hasattr(decision, 'leverage') and decision.leverage else "杠杆: 1x")
        print(f"执行状态: {'已执行' if decision.executed == 'true' else '未执行'}")
        print(f"原因: {decision.reason}")
        
        if decision.prompt:
            print(f"\n{'='*80}")
            print("完整 Prompt:")
            print(f"{'='*80}")
            print(decision.prompt)
            print(f"\nPrompt 长度: {len(decision.prompt)} 字符")
        else:
            print("\n[无 Prompt 数据]")

db.close()

print("\n" + "=" * 80)
print("提示：Prompt 现在会自动保存到数据库，不会打印到控制台")
print("=" * 80)
