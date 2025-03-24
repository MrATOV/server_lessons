from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.database.config import settings

engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=True,
)

session = async_sessionmaker(bind=engine, expire_on_commit=False)