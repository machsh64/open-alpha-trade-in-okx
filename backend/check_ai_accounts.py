"""
检查AI账户配置
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import SessionLocal
from database.models import Account

db = SessionLocal()

print("=" * 80)
print("📊 检查数据库中的账户配置")
print("=" * 80)

accounts = db.query(Account).all()

if not accounts:
    print("\n❌ 数据库中没有任何账户!")
    print("   请先创建账户")
else:
    print(f"\n找到 {len(accounts)} 个账户:\n")
    for acc in accounts:
        print(f"ID: {acc.id}")
        print(f"  名称: {acc.name}")
        print(f"  类型: {acc.account_type}")
        print(f"  激活: {acc.is_active}")
        print(f"  API Key: {acc.api_key[:20] if acc.api_key else 'None'}...")
        print(f"  Model: {acc.model}")
        print(f"  Base URL: {acc.base_url}")
        print(f"  余额: {acc.current_cash}")
        print("-" * 80)

print("\nAI交易条件检查:")
ai_accounts = [acc for acc in accounts if acc.account_type == "AI" and acc.is_active == "true"]
print(f"  ✅ AI类型账户数量: {len(ai_accounts)}")

valid_ai_accounts = [acc for acc in ai_accounts if acc.api_key and acc.api_key not in ["default-key-please-update-in-settings", "default", ""]]
print(f"  ✅ 有效API密钥的账户: {len(valid_ai_accounts)}")

if valid_ai_accounts:
    print("\n✅ 有有效的AI账户，AI交易应该会执行")
    for acc in valid_ai_accounts:
        print(f"   - {acc.name} (余额: ${acc.current_cash})")
else:
    print("\n❌ 没有有效的AI账户!")
    print("   请在数据库中配置:")
    print("   1. account_type = 'AI'")
    print("   2. is_active = 'true'")
    print("   3. api_key = '你的OpenAI API密钥'")
    print("   4. model = 'gpt-4' 或其他模型")
    print("   5. base_url = 'https://api.openai.com/v1'")

db.close()
