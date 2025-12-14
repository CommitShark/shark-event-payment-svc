import asyncio
import logging
from datetime import datetime, timezone
from app.infrastructure.sqlalchemy.session import get_async_session
from app.application.use_cases import ProcessDueSettlementsUseCase
from app.shared.errors import AppError
from ..container import DIContainer
from ..base import IWorker

logger = logging.getLogger("[ProcessDueTransactionTaskWorker]")


class ProcessDueTransactionTaskWorker(IWorker):
    """
    Long-running worker process that periodically checks for
    transactions whose delayed_settlement_until timestamp has passed.
    """

    def __init__(self, di: DIContainer):
        self.di = di
        self._running = True

    async def start(self) -> None:
        while self._running:
            try:
                process_due_settlements = self.di.resolve(ProcessDueSettlementsUseCase)

                now = datetime.now(timezone.utc)
                logger.debug(f"[Worker] Checking for due settlements at {now}")

                async with get_async_session() as session:
                    await process_due_settlements.execute(session)
            except AppError as e:
                logger.exception(f"[Worker] Error processing settlements: {e.message}")
            except Exception as e:
                logger.exception(f"[Worker] Error processing settlements: {e}")

            await asyncio.sleep(60)

    async def shutdown(self) -> None:
        print("CleanupWorker shutting down...")
        self._running = False
