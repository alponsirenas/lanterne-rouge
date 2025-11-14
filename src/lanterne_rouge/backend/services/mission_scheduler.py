"""Mission transition background scheduler."""
from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from lanterne_rouge.backend.db.session import SessionLocal
from lanterne_rouge.backend.services.mission_lifecycle import MissionLifecycleService

logger = logging.getLogger(__name__)


class MissionTransitionScheduler:
    """Background scheduler that periodically updates mission states."""

    def __init__(self, interval_minutes: int):
        self.interval_seconds = max(5, interval_minutes) * 60
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    async def start(self):
        """Start the scheduler loop."""
        if self._task is not None and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Mission transition scheduler started (interval=%ss)", self.interval_seconds)

    async def stop(self):
        """Stop the scheduler loop."""
        if self._task is None:
            return
        self._stop_event.set()
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None
        logger.info("Mission transition scheduler stopped")

    async def _run_loop(self):
        """Scheduler loop that runs until stopped."""
        # Run immediately on startup to catch up missions
        await self._run_once()

        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval_seconds)
            except asyncio.TimeoutError:
                await self._run_once()

    async def _run_once(self):
        """Execute a single transition check."""
        db = SessionLocal()
        try:
            transitions = MissionLifecycleService.check_automatic_transitions(db)
            if transitions:
                logger.info(
                    "Mission scheduler performed %s transition(s): %s",
                    len(transitions),
                    [t["mission_id"] for t in transitions]
                )
        except Exception as exc:  # pragma: no cover
            # We need to catch broad exceptions to prevent scheduler from crashing
            logger.exception("Mission scheduler error: %s", exc)
        finally:
            db.close()
