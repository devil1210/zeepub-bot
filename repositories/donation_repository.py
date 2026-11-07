# repositories/donation_repository.py

import logging
from typing import Any

from sqlalchemy import desc, func, or_, select

from core.db_manager_pg import pg_manager
from models.donation_models import DonationTransaction

logger = logging.getLogger(__name__)


class DonationRepository:
    """
    Repositorio para gestionar transacciones de donaciones y suscripciones (Ko-fi).
    """

    async def get_by_message_id(self, message_id: str) -> DonationTransaction | None:
        """Busca una transacción por su message_id único de Ko-fi (idempotencia)."""
        if not message_id:
            return None
        try:
            async with pg_manager.get_session() as session:
                stmt = select(DonationTransaction).where(
                    DonationTransaction.message_id == message_id
                )
                res = await session.execute(stmt)
                return res.scalar_one_or_none()
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error fetching donation by message_id {message_id}: {e}")
            return None

    async def get_by_transaction_id(self, tx_id: str) -> DonationTransaction | None:
        """Busca una transacción por kofi_transaction_id."""
        if not tx_id:
            return None
        try:
            async with pg_manager.get_session() as session:
                stmt = select(DonationTransaction).where(
                    DonationTransaction.kofi_transaction_id == tx_id
                )
                res = await session.execute(stmt)
                return res.scalar_one_or_none()
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error fetching donation by transaction_id {tx_id}: {e}")
            return None

    async def create_transaction(self, tx_data: dict[str, Any]) -> DonationTransaction:
        """Crea y persiste un nuevo registro de transacción de donación."""
        async with pg_manager.get_session() as session:
            tx = DonationTransaction(
                provider=tx_data.get("provider", "kofi"),
                message_id=tx_data["message_id"],
                kofi_transaction_id=tx_data.get("kofi_transaction_id"),
                timestamp=tx_data.get("timestamp"),
                payment_type=tx_data.get("payment_type", "Donation"),
                amount=tx_data.get("amount", 0.0),
                currency=tx_data.get("currency", "USD"),
                from_name=tx_data.get("from_name"),
                message=tx_data.get("message"),
                email=tx_data.get("email"),
                tier_name=tx_data.get("tier_name"),
                is_subscription=tx_data.get("is_subscription", False),
                is_first_subscription=tx_data.get("is_first_subscription", False),
                is_public=tx_data.get("is_public", True),
                telegram_id=tx_data.get("telegram_id"),
                user_display_name=tx_data.get("user_display_name"),
                tier_granted=tx_data.get("tier_granted"),
                duration_days=tx_data.get("duration_days"),
                status=tx_data.get("status", "processed"),
                raw_data=tx_data.get("raw_data"),
            )
            session.add(tx)
            await session.commit()
            await session.refresh(tx)
            return tx

    async def update_transaction(
        self, message_id: str, updates: dict[str, Any]
    ) -> bool:
        """Actualiza campos de una transacción existente."""
        try:
            async with pg_manager.get_session() as session:
                stmt = select(DonationTransaction).where(
                    DonationTransaction.message_id == message_id
                )
                res = await session.execute(stmt)
                tx = res.scalar_one_or_none()
                if not tx:
                    return False

                for key, val in updates.items():
                    if hasattr(tx, key):
                        setattr(tx, key, val)

                await session.commit()
                return True
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error updating donation {message_id}: {e}")
            return False

    async def get_recent_donations(self, limit: int = 50) -> list[DonationTransaction]:
        """Obtiene las donaciones más recientes."""
        try:
            async with pg_manager.get_session() as session:
                stmt = (
                    select(DonationTransaction)
                    .order_by(desc(DonationTransaction.created_at))
                    .limit(limit)
                )
                res = await session.execute(stmt)
                return list(res.scalars().all())
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error getting recent donations: {e}")
            return []

    async def get_unlinked_donations(
        self, limit: int = 50
    ) -> list[DonationTransaction]:
        """Obtiene donaciones pendientes de vincular a un usuario."""
        try:
            async with pg_manager.get_session() as session:
                stmt = (
                    select(DonationTransaction)
                    .where(DonationTransaction.status == "unlinked")
                    .order_by(desc(DonationTransaction.created_at))
                    .limit(limit)
                )
                res = await session.execute(stmt)
                return list(res.scalars().all())
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error getting unlinked donations: {e}")
            return []

    async def find_unlinked_by_query(self, query: str) -> list[DonationTransaction]:
        """Busca donaciones desvinculadas por email o transaction_id."""
        cleaned = query.strip()
        if not cleaned:
            return []
        try:
            async with pg_manager.get_session() as session:
                stmt = (
                    select(DonationTransaction)
                    .where(
                        DonationTransaction.status == "unlinked",
                        or_(
                            func.lower(DonationTransaction.email) == cleaned.lower(),
                            DonationTransaction.kofi_transaction_id == cleaned,
                            DonationTransaction.message_id == cleaned,
                            func.lower(DonationTransaction.from_name)
                            == cleaned.lower(),
                        ),
                    )
                    .order_by(desc(DonationTransaction.created_at))
                )
                res = await session.execute(stmt)
                return list(res.scalars().all())
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error finding unlinked donation with query {query}: {e}")
            return []


donation_repo = DonationRepository()
