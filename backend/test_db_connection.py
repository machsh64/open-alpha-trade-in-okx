"""
测试PostgreSQL数据库连接
"""
from database.connection import engine, DATABASE_URL
from sqlalchemy import text

def test_connection():
    print(f"📡 Testing connection to: {DATABASE_URL}")
    print("=" * 60)
    
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connection successful!")
            print(f"📊 PostgreSQL version: {version}")
            
            # Test database name
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            print(f"🗄️  Current database: {db_name}")
            
            # List tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = result.fetchall()
            
            if tables:
                print(f"\n📋 Existing tables ({len(tables)}):")
                for table in tables:
                    print(f"   - {table[0]}")
            else:
                print("\n⚠️  No tables found. Run postgresql_schema.sql to create tables.")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check if PostgreSQL is running on 192.168.188.3")
        print("   2. Verify credentials in backend/.env file")
        print("   3. Ensure database 'ai-trade' exists")
        print("   4. Check firewall settings")
        return False
    
    return True

if __name__ == "__main__":
    test_connection()
