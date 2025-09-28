"""
Job Logging Utility Module

This module provides comprehensive logging functionality for job processing,
including batch logging for performance optimization and structured logging
with different log levels.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import asyncpg
from dataclasses import dataclass
import json

from db.connection import get_pool

# Configure module logger
logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Enumeration of supported log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Data class representing a single log entry."""
    job_id: str
    log_level: LogLevel
    message: str
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.metadata is None:
            self.metadata = {}


class JobLogger:
    """
    Comprehensive job logging utility with batch processing capabilities.
    
    Features:
    - Batch logging for performance optimization
    - Structured logging with metadata support
    - Automatic retry on database failures
    - Memory-efficient buffering
    - Thread-safe operations
    """
    
    def __init__(self, batch_size: int = 50, flush_interval: float = 5.0):
        """
        Initialize the job logger.
        
        Args:
            batch_size: Maximum number of log entries to batch before flushing
            flush_interval: Time in seconds between automatic flushes
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._log_buffer: List[LogEntry] = []
        self._lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        self._shutdown = False
        
    async def start(self):
        """Start the background flush task."""
        if self._flush_task is None or self._flush_task.done():
            self._flush_task = asyncio.create_task(self._periodic_flush())
            logger.info("Job logger started with batch size %d and flush interval %.1fs", 
                       self.batch_size, self.flush_interval)
    
    async def stop(self):
        """Stop the background flush task and flush remaining logs."""
        self._shutdown = True
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Flush any remaining logs
        await self.flush()
        logger.info("Job logger stopped")
    
    async def log(self, job_id: str, level: LogLevel, message: str, 
                  metadata: Optional[Dict[str, Any]] = None):
        """
        Add a log entry to the buffer.
        
        Args:
            job_id: The job ID this log entry belongs to
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            metadata: Optional metadata dictionary
        """
        entry = LogEntry(
            job_id=job_id,
            log_level=level,
            message=message,
            metadata=metadata
        )
        
        async with self._lock:
            self._log_buffer.append(entry)
            
            # Flush if buffer is full
            if len(self._log_buffer) >= self.batch_size:
                await self._flush_buffer()
    
    async def log_job_started(self, job_id: str, task_type: str, 
                             payload: Optional[Dict[str, Any]] = None):
        """Log that a job has started processing."""
        metadata = {
            "task_type": task_type,
            "payload_size": len(json.dumps(payload or {})) if payload else 0
        }
        await self.log(job_id, LogLevel.INFO, f"Job started processing (task_type: {task_type})", metadata)
    
    async def log_job_completed(self, job_id: str, result: Optional[Dict[str, Any]] = None,
                               duration: Optional[float] = None):
        """Log that a job has completed successfully."""
        metadata = {
            "result_size": len(json.dumps(result or {})) if result else 0,
            "duration_seconds": duration
        }
        message = f"Job completed successfully"
        if duration is not None:
            message += f" in {duration:.2f}s"
        await self.log(job_id, LogLevel.INFO, message, metadata)
    
    async def log_job_failed(self, job_id: str, error: Union[str, Exception],
                            retry_count: int = 0, max_retries: int = 3):
        """Log that a job has failed."""
        error_message = str(error) if isinstance(error, Exception) else error
        metadata = {
            "error_type": type(error).__name__ if isinstance(error, Exception) else "Unknown",
            "retry_count": retry_count,
            "max_retries": max_retries
        }
        
        level = LogLevel.ERROR if retry_count < max_retries else LogLevel.CRITICAL
        message = f"Job failed: {error_message}"
        if retry_count > 0:
            message += f" (retry {retry_count}/{max_retries})"
        
        await self.log(job_id, level, message, metadata)
    
    async def log_job_retry(self, job_id: str, retry_count: int, reason: str):
        """Log that a job is being retried."""
        metadata = {"retry_count": retry_count, "reason": reason}
        await self.log(job_id, LogLevel.WARNING, f"Job retry #{retry_count}: {reason}", metadata)
    
    async def log_job_cancelled(self, job_id: str, reason: str = "User cancelled"):
        """Log that a job has been cancelled."""
        metadata = {"reason": reason}
        await self.log(job_id, LogLevel.WARNING, f"Job cancelled: {reason}", metadata)
    
    async def log_worker_event(self, job_id: str, event: str, details: Optional[Dict[str, Any]] = None):
        """Log worker-specific events."""
        metadata = details or {}
        await self.log(job_id, LogLevel.DEBUG, f"Worker event: {event}", metadata)
    
    async def log_callback_failed(self, job_id: str, callback_url: str, error: str, 
                                 retry_count: int = 0, max_retries: int = 3):
        """Log that a job's callback failed."""
        metadata = {
            "callback_url": callback_url,
            "error": error,
            "retry_count": retry_count,
            "max_retries": max_retries
        }
        message = f"Callback failed: {error}"
        if retry_count > 0:
            message += f" (retry {retry_count}/{max_retries})"
        
        level = LogLevel.ERROR if retry_count >= max_retries else LogLevel.WARNING
        await self.log(job_id, level, message, metadata)
    
    async def flush(self):
        """Manually flush all buffered log entries."""
        async with self._lock:
            await self._flush_buffer()
    
    async def _flush_buffer(self):
        """Flush the current buffer to the database."""
        if not self._log_buffer:
            return
        
        entries_to_flush = self._log_buffer.copy()
        self._log_buffer.clear()
        
        try:
            await self._insert_logs(entries_to_flush)
            logger.debug("Flushed %d log entries to database", len(entries_to_flush))
        except Exception as e:
            logger.error("Failed to flush log entries: %s", e)
            # Re-add entries to buffer for retry (but limit to prevent memory issues)
            if len(self._log_buffer) < self.batch_size * 2:
                self._log_buffer.extend(entries_to_flush)
    
    async def _insert_logs(self, entries: List[LogEntry]):
        """Insert log entries into the database."""
        if not entries:
            return
        
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Prepare batch insert data
            values = []
            for entry in entries:
                values.append((
                    entry.job_id,
                    entry.log_level.value,
                    entry.message,
                    entry.timestamp,
                    json.dumps(entry.metadata) if entry.metadata else None
                ))
            
            # Batch insert
            await conn.executemany(
                """
                INSERT INTO job_logs (job_id, log_level, message, timestamp, metadata)
                VALUES ($1, $2, $3, $4, $5)
                """,
                values
            )
    
    async def _periodic_flush(self):
        """Background task to periodically flush log buffer."""
        while not self._shutdown:
            try:
                await asyncio.sleep(self.flush_interval)
                await self.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in periodic flush: %s", e)


# Global job logger instance
_job_logger: Optional[JobLogger] = None


async def get_job_logger() -> JobLogger:
    """Get the global job logger instance."""
    global _job_logger
    if _job_logger is None:
        _job_logger = JobLogger()
        await _job_logger.start()
    return _job_logger


async def shutdown_job_logger():
    """Shutdown the global job logger."""
    global _job_logger
    if _job_logger is not None:
        await _job_logger.stop()
        _job_logger = None


# Convenience functions for common logging operations
async def log_job_started(job_id: str, task_type: str, payload: Optional[Dict[str, Any]] = None):
    """Convenience function to log job start."""
    logger = await get_job_logger()
    await logger.log_job_started(job_id, task_type, payload)


async def log_job_completed(job_id: str, result: Optional[Dict[str, Any]] = None, 
                           duration: Optional[float] = None):
    """Convenience function to log job completion."""
    logger = await get_job_logger()
    await logger.log_job_completed(job_id, result, duration)


async def log_job_failed(job_id: str, error: Union[str, Exception], 
                        retry_count: int = 0, max_retries: int = 3):
    """Convenience function to log job failure."""
    logger = await get_job_logger()
    await logger.log_job_failed(job_id, error, retry_count, max_retries)


async def log_job_retry(job_id: str, retry_count: int, reason: str):
    """Convenience function to log job retry."""
    logger = await get_job_logger()
    await logger.log_job_retry(job_id, retry_count, reason)


async def log_job_cancelled(job_id: str, reason: str = "User cancelled"):
    """Convenience function to log job cancellation."""
    logger = await get_job_logger()
    await logger.log_job_cancelled(job_id, reason)


async def log_worker_event(job_id: str, event: str, details: Optional[Dict[str, Any]] = None):
    """Convenience function to log worker events."""
    logger = await get_job_logger()
    await logger.log_worker_event(job_id, event, details)


async def log_callback_failed(job_id: str, callback_url: str, error: str, 
                             retry_count: int = 0, max_retries: int = 3):
    """Convenience function to log callback failures."""
    logger = await get_job_logger()
    await logger.log_callback_failed(job_id, callback_url, error, retry_count, max_retries)
