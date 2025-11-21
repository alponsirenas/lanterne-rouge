"""Background refresh service for data connections."""
import asyncio
import logging
from datetime import datetime, timezone


from sqlalchemy.orm import Session

from lanterne_rouge.backend.db.session import SessionLocal
from lanterne_rouge.backend.models.connection import DataConnection
from lanterne_rouge.backend.services.data_connections import (
    get_strava_service,
    get_oura_service,
)

logger = logging.getLogger(__name__)


class BackgroundRefreshScheduler:
    """Scheduler for background data refresh jobs."""

    def __init__(self, interval_minutes: int = 60):
        """
        Initialize the scheduler.

        Args:
            interval_minutes: How often to run refresh (default: 60 minutes)
        """
        self.interval_minutes = interval_minutes
        self.is_running = False
        self.task = None

    async def start(self):
        """Start the background refresh scheduler."""
        if self.is_running:
            logger.warning("Background refresh scheduler is already running")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._run_scheduler())
        logger.info(
            f"Background refresh scheduler started (interval: {
                self.interval_minutes} minutes)")

    async def stop(self):
        """Stop the background refresh scheduler."""
        if not self.is_running:
            return

        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("Background refresh scheduler stopped")

    async def _run_scheduler(self):
        """Run the scheduler loop."""
        while self.is_running:
            try:
                await self._refresh_all_connections()
            except Exception as e:
                logger.error(f"Error in background refresh: {str(e)}")

            # Wait for next interval
            await asyncio.sleep(self.interval_minutes * 60)

    async def _refresh_all_connections(self):
        """Refresh all active data connections."""
        logger.info("Starting background refresh for all connections")

        db = SessionLocal()
        try:
            # Get all connected data sources
            connections = db.query(DataConnection).filter(
                DataConnection.status == "connected"
            ).all()

            success_count = 0
            error_count = 0

            for conn in connections:
                try:
                    if conn.connection_type == "strava":
                        await self._refresh_strava(conn, db)
                        success_count += 1
                    elif conn.connection_type == "oura":
                        await self._refresh_oura(conn, db)
                        success_count += 1
                    # Apple Health doesn't have background refresh (upload only)
                except Exception as e:
                    error_count += 1
                    logger.error(
                        f"Failed to refresh {
                            conn.connection_type} for user {
                            conn.user_id}: {
                            str(e)}")

                    # Update connection with error (but don't log sensitive data)
                    conn.error_message = f"Refresh failed: {type(e).__name__}"
                    conn.updated_at = datetime.now(timezone.utc)
                    db.commit()

            logger.info(
                f"Background refresh completed: {success_count} succeeded, {error_count} failed"
            )

        finally:
            db.close()

    async def _refresh_strava(self, connection: DataConnection, db: Session):
        """Refresh Strava data for a connection."""
        strava_service = get_strava_service()

        count = strava_service.refresh_activities(
            connection.user_id,
            connection,
            db
        )

        # Update connection status
        connection.last_refresh_at = datetime.now(timezone.utc)
        connection.last_refresh_status = f"Success: {count} activities"
        connection.error_message = None
        connection.updated_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            f"Strava refresh successful for user {connection.user_id}: {count} activities"
        )

    async def _refresh_oura(self, connection: DataConnection, db: Session):
        """Refresh Oura data for a connection."""
        oura_service = get_oura_service()

        count = oura_service.refresh_readiness_data(
            connection.user_id,
            connection,
            db
        )

        # Update connection status
        connection.last_refresh_at = datetime.now(timezone.utc)
        connection.last_refresh_status = f"Success: {count} records"
        connection.error_message = None
        connection.updated_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            f"Oura refresh successful for user {connection.user_id}: {count} records"
        )


# Global scheduler instance
_refresh_scheduler = None


def get_refresh_scheduler(interval_minutes: int = 60) -> BackgroundRefreshScheduler:
    """Get or create the background refresh scheduler."""
    global _refresh_scheduler
    if _refresh_scheduler is None:
        _refresh_scheduler = BackgroundRefreshScheduler(interval_minutes)
    return _refresh_scheduler
