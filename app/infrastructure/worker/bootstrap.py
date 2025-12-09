# import asyncio
# import logging
# import signal
# from datetime import datetime, timezone

# from app.application.use_cases import (
#     ProcessDueSettlementsUseCase,
# )
# from app.infrastructure.sqlalchemy.session import get_async_session
# from app.domain.repositories import ITransactionRepository
# from app.infrastructure.worker.container import build_worker_container

# logger = logging.getLogger(__name__)


import asyncio
import signal
import logging
from logging.handlers import RotatingFileHandler
import sys
import contextlib
from .container import WorkerContainer, build_di_container, DIContainer
from .tasks import ProcessDueTransactionTaskWorker

# Use the root logger so all modules inherit this configuration
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Remove any pre-existing handlers to avoid duplicate logs
if logger.hasHandlers():
    logger.handlers.clear()

# File handler
file_handler = RotatingFileHandler("workers.log", maxBytes=10_000_000, backupCount=5)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
# Console handler (stdout)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)

# Attach handlers to root logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger = logging.getLogger(__name__)


async def run_worker_system(container: WorkerContainer) -> None:
    logger.info("Resolving workers...")

    workers = container.resolve_all()

    # Start all workers concurrently
    logger.info("Starting %d workers...", len(workers))
    tasks = [asyncio.create_task(w.start()) for w in workers]

    stop_event = asyncio.Event()

    def _handle_shutdown(*_: object) -> None:
        logger.warning("Shutdown signal received.")
        stop_event.set()

    # Listen to termination signals
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, _handle_shutdown)
    loop.add_signal_handler(signal.SIGINT, _handle_shutdown)
    logger.info("Signal handlers installed.")

    # Wait until shutdown requested
    logger.info("Worker system running. Awaiting shutdown...")
    await stop_event.wait()

    # Gracefully stop all workers
    logger.info("Stopping workers gracefully...")
    for w in workers:
        logger.info("Stopping %s", w.__class__.__name__)
        await w.shutdown()

    # Cancel running tasks
    logger.info("Cancelling worker tasks...")
    for t in tasks:
        t.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await t

    logger.info("Workers stopped. Worker system shutdown complete.")


async def main():
    logger.info("Initializing DI container...")
    await DIContainer.init()
    logger.info("DI initialized.")

    # Build DI and container
    di = build_di_container()
    container = WorkerContainer(di)

    # Register workers
    container.register(ProcessDueTransactionTaskWorker)

    # Run worker system
    await run_worker_system(container)

    logger.info("Shutting down DI container...")
    await DIContainer.shutdown()
    logger.info("System shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
