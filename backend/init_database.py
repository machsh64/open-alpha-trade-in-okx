"""
Database initialization script
Run this after creating tables to initialize database with default data
"""
from database.connection import engine, SessionLocal
from database.models import Base, User, Account, TradingConfig
from decimal import Decimal

def init_database():
    """Initialize database with tables and default data"""
    
    print("Creating database tables...")
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")
    
    db = SessionLocal()
    try:
        # Check if default user exists
        existing_user = db.query(User).filter(User.username == "default").first()
        
        if not existing_user:
            print("\nCreating default user and account...")
            
            # Create default user
            default_user = User(
                username="default",
                email="default@aitrade.com",
                is_active="true"
            )
            db.add(default_user)
            db.flush()
            
            # Create default AI account
            default_account = Account(
                user_id=default_user.id,
                name="default AI Trader",
                account_type="AI",
                is_active="true",
                model="gpt-4",
                base_url="https://api.openai.com/v1",
                initial_capital=Decimal("100000.00"),
                current_cash=Decimal("100000.00"),
                frozen_cash=Decimal("0.00")
            )
            db.add(default_account)
            
            db.commit()
            print(f"✅ Created default user (id={default_user.id}) and account (id={default_account.id})")
        else:
            print(f"\n✅ Default user already exists (id={existing_user.id})")
        
        # Check trading config
        crypto_config = db.query(TradingConfig).filter(
            TradingConfig.market == "CRYPTO",
            TradingConfig.version == "v1"
        ).first()
        
        if not crypto_config:
            print("\nCreating default trading config...")
            crypto_config = TradingConfig(
                market="CRYPTO",
                version="v1",
                min_commission=0.1,
                commission_rate=0.001,
                exchange_rate=1.0,
                min_order_quantity=1,
                lot_size=1
            )
            db.add(crypto_config)
            db.commit()
            print("✅ Created CRYPTO trading config")
        else:
            print(f"\n✅ CRYPTO trading config already exists (id={crypto_config.id})")
        
        print("\n" + "="*50)
        print("Database initialization completed successfully!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
