from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integration_config import IntegrationConfig


class IntegrationConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_type(self, type_: str) -> IntegrationConfig | None:
        stmt = select(IntegrationConfig).where(IntegrationConfig.type == type_)
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def upsert(
        self,
        type_: str,
        name: str,
        config_bytes: bytes,
        enabled: bool,
    ) -> IntegrationConfig:
        now = datetime.now(tz=UTC)
        existing = await self.get_by_type(type_)
        if existing is not None:
            await self._s.execute(
                update(IntegrationConfig)
                .where(IntegrationConfig.type == type_)
                .values(name=name, config=config_bytes, enabled=enabled, updated_at=now)
            )
            await self._s.flush()
            await self._s.refresh(existing)
            return existing
        row = IntegrationConfig(
            type=type_,
            name=name,
            config=config_bytes,
            enabled=enabled,
        )
        self._s.add(row)
        await self._s.flush()
        await self._s.refresh(row)
        return row

    async def delete_by_type(self, type_: str) -> bool:
        result = await self._s.execute(
            delete(IntegrationConfig).where(IntegrationConfig.type == type_)
        )
        await self._s.flush()
        return result.rowcount > 0  # type: ignore[attr-defined]

    async def update_test_result(self, type_: str, ok: bool) -> None:
        now = datetime.now(tz=UTC)
        await self._s.execute(
            update(IntegrationConfig)
            .where(IntegrationConfig.type == type_)
            .values(last_test_at=now, last_test_ok=ok, updated_at=now)
        )
        await self._s.flush()
