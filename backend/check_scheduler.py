"""
检查AI交易调度器状态
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.scheduler import task_scheduler
from datetime import datetime

print("=" * 80)
print("📅 检查AI交易调度器状态")
print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

try:
    # 获取所有任务
    tasks = task_scheduler.list_tasks()
    
    if not tasks:
        print("\n❌ 没有发现任何调度任务!")
        print("   可能原因:")
        print("   1. 后端服务未启动")
        print("   2. 启动时出错，调度器初始化失败")
    else:
        print(f"\n✅ 找到 {len(tasks)} 个调度任务:\n")
        for i, task in enumerate(tasks, 1):
            print(f"{i}. 任务ID: {task.get('id', 'N/A')}")
            print(f"   下次运行: {task.get('next_run_time', 'N/A')}")
            print(f"   触发器: {task.get('trigger', 'N/A')}")
            print("-" * 80)
    
    # 检查环境变量
    print("\n环境变量检查:")
    ai_interval = os.getenv('AI_TRADE_INTERVAL', '未设置')
    print(f"  AI_TRADE_INTERVAL = {ai_interval}")
    if ai_interval != '未设置':
        print(f"  换算为分钟: {int(ai_interval) / 60:.1f} 分钟")
    
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    
print("\n" + "=" * 80)
print("💡 提示:")
print("  如果没有看到任务，请确保:")
print("  1. 后端服务正在运行 (pnpm run dev:backend)")
print("  2. 检查后端启动日志是否有错误")
print("  3. .env 文件配置正确")
print("=" * 80)
