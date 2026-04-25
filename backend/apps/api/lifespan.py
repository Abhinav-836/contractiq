# apps/api/lifespan.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from db.session import init_db, close_db
from core.logger import get_logger, setup_logging
from core.config import settings
from sqlalchemy import select, func

logger = get_logger(__name__)


async def ensure_default_user():
    """Create a default test user if no users exist"""
    try:
        from db.session import AsyncSessionLocal
        from modules.users.models import User
        from modules.users.repository import UserRepository
        
        async with AsyncSessionLocal() as db:
            # Check if any users exist
            result = await db.execute(select(func.count()).select_from(User))
            count = result.scalar()
            
            if count == 0:
                logger.warning("No users found in database. Creating default test user...")
                repo = UserRepository(db)
                
                # Create test user
                test_user = await repo.create(
                    email="test@example.com",
                    name="Test User",
                    password="test123"
                )
                await db.commit()
                
                logger.info(f"✅ Created default test user: test@example.com / test123")
                print("\n" + "=" * 60)
                print("🔐 DEFAULT TEST USER CREATED:")
                print(f"   Email: test@example.com")
                print(f"   Password: test123")
                print("=" * 60 + "\n")
                
                # Also create an admin user if needed
                if settings.APP_ENV == "production":
                    admin_user = await repo.create(
                        email="admin@contractiq.com",
                        name="Admin User",
                        password="Admin123!"
                    )
                    await db.commit()
                    print("👑 Created admin user: admin@contractiq.com / Admin123!")
                    
            else:
                logger.info(f"Database already has {count} user(s)")
                
    except Exception as e:
        logger.error(f"Failed to ensure default user: {str(e)}")


async def validate_database_connection():
    """Validate database connection on startup"""
    try:
        from db.session import AsyncSessionLocal
        from sqlalchemy import text
        
        async with AsyncSessionLocal() as db:
            # Fix: Use text() for raw SQL
            await db.execute(text("SELECT 1"))
            logger.info("database.connection_verified")
            return True
    except Exception as e:
        logger.error(f"database.connection_failed: {str(e)}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info("startup.begin", env=settings.APP_ENV, provider=settings.effective_llm_provider)

    # Validate database connection
    await validate_database_connection()
    
    # Initialize database
    await init_db()
    logger.info("startup.db_ready")
    
    # Create default user if database is empty
    await ensure_default_user()

    # Show startup banner
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    ContractIQ Backend v1.0.0                  ║
╠══════════════════════════════════════════════════════════════╣
║  Environment:  {settings.APP_ENV:<46}║
║  API Docs:     /docs{40: <46}║
║  Health:       /api/v1/health{40: <46}║
║  LLM Provider: {settings.effective_llm_provider:<46}║
║  Database:     {'PostgreSQL' if 'postgresql' in settings.DATABASE_URL else 'SQLite':<46}║
║  CORS Origins: {len(settings.allowed_origins_list)} origins configured{40: <46}║
╚══════════════════════════════════════════════════════════════╝
""")

    yield

    # Shutdown
    await close_db()
    logger.info("shutdown.complete")