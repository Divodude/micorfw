from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
)
from sqlalchemy.orm import sessionmaker

class Database:
    def __init__(self, url: str, echo: bool = False):
        self.url = url
        self.echo = echo
        self.engine = None
        self.SessionLocal = None

    async def connect(self):
        self.engine = create_async_engine(
            self.url,
            echo=self.echo,
            future=True,
        )
        self.SessionLocal = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def disconnect(self):
        if self.engine:
            await self.engine.dispose()

    async def session(self) -> AsyncSession:
        if self.SessionLocal is None:
            raise RuntimeError("Database not connected. Call connect() first or ensure startup hooks ran.")
        return self.SessionLocal()
