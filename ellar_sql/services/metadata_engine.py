from __future__ import annotations

import dataclasses

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncEngine


@dataclasses.dataclass
class MetaDataEngine:
    metadata: sa.MetaData
    engine: sa.Engine

    def is_async(self) -> bool:
        return self.engine.dialect.is_async

    def create_all(self) -> None:
        self.metadata.create_all(bind=self.engine)

    async def create_all_async(self) -> None:
        engine = AsyncEngine(self.engine)
        async with engine.begin() as conn:
            await conn.run_sync(self.metadata.create_all)

    def drop_all(self) -> None:
        self.metadata.drop_all(bind=self.engine)

    async def drop_all_async(self) -> None:
        engine = AsyncEngine(self.engine)
        async with engine.begin() as conn:
            await conn.run_sync(self.metadata.drop_all)

    def reflect(self) -> None:
        self.metadata.reflect(bind=self.engine)

    async def reflect_async(self) -> None:
        engine = AsyncEngine(self.engine)
        async with engine.begin() as conn:
            await conn.run_sync(self.metadata.reflect)
