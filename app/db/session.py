from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import Config

engine = create_async_engine(
    Config.DATABASE_URL, 
    # SQLite requires special check_same_thread handling for async
    connect_args={"check_same_thread": False} if "sqlite" in Config.DATABASE_URL else {}
)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

class Base(DeclarativeBase):
    """Base class for SQLAlchemy models using 2.0 style declarative mapping."""
    pass

async def get_db():
    async with SessionLocal() as db:
        yield db