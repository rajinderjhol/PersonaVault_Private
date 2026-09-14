from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from app.config import Config

is_sqlite = Config.DATABASE_URL.startswith("sqlite")

engine_kwargs = {"echo": False}

if is_sqlite:
    engine_kwargs["poolclass"] = NullPool
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 3600

engine = create_async_engine(Config.DATABASE_URL, **engine_kwargs)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

class Base(DeclarativeBase):
    """Base class for SQLAlchemy models using 2.0 style declarative mapping."""
    pass

async def get_db():
    async with SessionLocal() as db:
        yield db