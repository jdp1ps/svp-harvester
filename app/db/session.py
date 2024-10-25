from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import get_app_settings
from app.settings.app_env_types import AppEnvTypes

settings = get_app_settings()
SQLALCHEMY_DATABASE_URL = (
    f"{settings.db_engine}"
    f"://{settings.db_user}"
    f":{settings.db_password}"
    f"@{settings.db_host}"
    f":{settings.db_port}"
    f"/{settings.db_name}"
)
if settings.app_env == AppEnvTypes.TEST:
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        future=True,
        echo=False,
        poolclass=NullPool,  # use NullPool for testing
    )
else:  # pragma: no cover
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        future=True,
        echo=False,
        pool_size=settings.db_pool_size,
        max_overflow=settings.max_overflow,
        pool_timeout=60,
        pool_pre_ping=True,
        pool_recycle=900,
    )
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()
