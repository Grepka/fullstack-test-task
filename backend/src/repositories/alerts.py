from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Alert


async def list_alerts(session: AsyncSession) -> list[Alert]:
    result = await session.execute(select(Alert).order_by(Alert.created_at.desc()))
    return list(result.scalars().all())


def add_alert(session: AsyncSession, alert: Alert) -> None:
    session.add(alert)


async def get_matching_alert(session: AsyncSession, alert: Alert) -> Alert | None:
    result = await session.execute(
        select(Alert).where(
            Alert.file_id == alert.file_id,
            Alert.level == alert.level,
            Alert.message == alert.message,
        )
    )
    return result.scalar_one_or_none()


async def add_alert_once(session: AsyncSession, alert: Alert) -> Alert:
    existing_alert = await get_matching_alert(session, alert)
    if existing_alert:
        return existing_alert
    session.add(alert)
    return alert


async def delete_alerts_by_file_id(session: AsyncSession, file_id: str) -> None:
    await session.execute(delete(Alert).where(Alert.file_id == file_id))
