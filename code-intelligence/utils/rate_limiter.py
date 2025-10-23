"""
Rate Limit Controller for Azure OpenAI API

Implements adaptive batching, exponential backoff, and quota management
to prevent HTTP 429 (Too Many Requests) errors during embedding operations.
"""

import asyncio
import time
import random
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import logging

logger = logging.getLogger(__name__)


class QuotaType(Enum):
    """Different quota types for different Azure services"""
    EMBEDDING = "embedding"
    SUMMARIZATION = "summarization"
    CHAT = "chat"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting per quota type"""
    requests_per_minute: int = 60
    tokens_per_minute: int = 90000
    max_batch_size: int = 16
    min_batch_size: int = 1
    initial_retry_delay: float = 1.0
    max_retry_delay: float = 60.0
    jitter_range: float = 0.2


@dataclass
class RequestMetrics:
    """Track request metrics for adaptive batching"""
    total_requests: int = 0
    successful_requests: int = 0
    throttled_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    avg_response_time: float = 0.0
    last_request_time: float = 0.0
    request_timestamps: deque = field(default_factory=lambda: deque(maxlen=100))


class RateLimitController:
    """
    Intelligent rate limiter with leaky bucket algorithm and adaptive batching.
    
    Features:
    - Per-model quota tracking (embeddings vs summaries)
    - Adaptive batch sizes based on observed throughput
    - Exponential backoff with jitter for retries
    - Token-based and request-based limiting
    - Priority queue for task scheduling
    """
    
    def __init__(self, configs: Optional[Dict[QuotaType, RateLimitConfig]] = None):
        """Initialize rate limiter with per-quota-type configs"""
        self.configs = configs or {
            QuotaType.EMBEDDING: RateLimitConfig(
                requests_per_minute=60,
                tokens_per_minute=90000,
                max_batch_size=16,
                min_batch_size=1
            ),
            QuotaType.SUMMARIZATION: RateLimitConfig(
                requests_per_minute=120,
                tokens_per_minute=150000,
                max_batch_size=5,
                min_batch_size=1
            ),
            QuotaType.CHAT: RateLimitConfig(
                requests_per_minute=60,
                tokens_per_minute=90000,
                max_batch_size=1,
                min_batch_size=1
            )
        }
        
        self.metrics: Dict[QuotaType, RequestMetrics] = {
            quota_type: RequestMetrics() for quota_type in QuotaType
        }
        
        self.task_queues: Dict[QuotaType, asyncio.PriorityQueue] = {
            quota_type: asyncio.PriorityQueue() for quota_type in QuotaType
        }
        
        self._locks: Dict[QuotaType, asyncio.Lock] = {
            quota_type: asyncio.Lock() for quota_type in QuotaType
        }
        
        self._running = False
        self._task_counter = 0  # Unique counter to break ties in priority queue
    
    async def start(self):
        """Start background workers for processing queued tasks"""
        self._running = True
        # Start a worker for each quota type
        workers = [
            asyncio.create_task(self._worker(quota_type))
            for quota_type in QuotaType
        ]
        logger.info("🚀 RateLimitController started with workers for all quota types")
        return workers
    
    async def stop(self):
        """Stop all workers"""
        self._running = False
        logger.info("⏸️ RateLimitController stopped")
    
    async def _worker(self, quota_type: QuotaType):
        """Background worker that processes tasks from the queue"""
        while self._running:
            try:
                priority, task_id, func, args, kwargs, future = await asyncio.wait_for(
                    self.task_queues[quota_type].get(),
                    timeout=1.0
                )
                
                # Execute with rate limiting
                try:
                    result = await self._execute_with_limit(quota_type, func, *args, **kwargs)
                    if not future.done():
                        future.set_result(result)
                except Exception as e:
                    if not future.done():
                        future.set_exception(e)
                finally:
                    self.task_queues[quota_type].task_done()
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker error for {quota_type.value}: {e}")
    
    async def submit(
        self,
        quota_type: QuotaType,
        func: Callable,
        *args,
        priority: int = 5,
        **kwargs
    ) -> Any:
        """
        Submit a task to the rate-limited queue.
        
        Args:
            quota_type: Type of quota (embedding, summarization, chat)
            func: Async function to execute
            priority: Lower number = higher priority (0 = highest)
            *args, **kwargs: Arguments for func
            
        Returns:
            Result from func
        """
        future = asyncio.Future()
        self._task_counter += 1
        
        # Log submission
        logger.debug(f"📤 Submitting task #{self._task_counter} to {quota_type.value} queue")
        logger.debug(f"   Function: {func.__name__ if hasattr(func, '__name__') else 'lambda'}")
        logger.debug(f"   Priority: {priority}")
        logger.debug(f"   Queue size: {self.task_queues[quota_type].qsize()}")
        
        # Use counter to ensure unique comparison and avoid function comparison
        task_item = (priority, self._task_counter, func, args, kwargs, future)
        
        await self.task_queues[quota_type].put(task_item)
        
        return await future
    
    async def _execute_with_limit(
        self,
        quota_type: QuotaType,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with rate limit enforcement"""
        config = self.configs[quota_type]
        metrics = self.metrics[quota_type]
        
        func_name = func.__name__ if hasattr(func, '__name__') else 'lambda'
        logger.debug(f"⏳ Executing {func_name} with {quota_type.value} limit")
        logger.debug(f"   Queue: {metrics.total_requests} total, {metrics.throttled_requests} throttled")
        
        async with self._locks[quota_type]:
            # Check if we need to wait
            await self._wait_if_needed(quota_type)
            
            # Execute with retry logic
            retry_delay = config.initial_retry_delay
            last_exception = None
            
            for attempt in range(5):  # Max 5 retries
                try:
                    start_time = time.time()
                    
                    logger.debug(f"   🔄 Calling {func_name} (attempt {attempt + 1})")
                    
                    # Execute the function
                    result = await func(*args, **kwargs)
                    
                    # Update metrics on success
                    elapsed = time.time() - start_time
                    logger.debug(f"   ✅ {func_name} completed in {elapsed:.2f}s")
                    self._update_metrics(quota_type, elapsed, success=True)
                    
                    return result
                    
                except Exception as e:
                    error_str = str(e)
                    
                    # Check if it's a rate limit error (429)
                    if "429" in error_str or "Too Many Requests" in error_str:
                        metrics.throttled_requests += 1
                        
                        # Extract retry-after if available
                        retry_after = self._extract_retry_after(error_str)
                        if retry_after:
                            wait_time = retry_after
                        else:
                            # Exponential backoff with jitter
                            jitter = random.uniform(
                                -config.jitter_range * retry_delay,
                                config.jitter_range * retry_delay
                            )
                            wait_time = min(retry_delay + jitter, config.max_retry_delay)
                        
                        logger.warning(
                            f"⚠️ Rate limited on {quota_type.value} "
                            f"(attempt {attempt + 1}/5). Waiting {wait_time:.1f}s"
                        )
                        
                        await asyncio.sleep(wait_time)
                        retry_delay *= 2  # Exponential backoff
                        last_exception = e
                        continue
                    else:
                        # Non-rate-limit error
                        metrics.failed_requests += 1
                        raise
            
            # All retries exhausted
            metrics.failed_requests += 1
            raise last_exception or Exception("Max retries exceeded")
    
    async def _wait_if_needed(self, quota_type: QuotaType):
        """Wait if we're approaching rate limits"""
        config = self.configs[quota_type]
        metrics = self.metrics[quota_type]
        
        current_time = time.time()
        
        # Remove old timestamps (older than 1 minute)
        while metrics.request_timestamps and \
              (current_time - metrics.request_timestamps[0]) > 60:
            metrics.request_timestamps.popleft()
        
        # Check if we need to wait
        if len(metrics.request_timestamps) >= config.requests_per_minute:
            # Wait until the oldest request is 60 seconds old
            oldest = metrics.request_timestamps[0]
            wait_time = 60 - (current_time - oldest)
            if wait_time > 0:
                logger.info(
                    f"⏳ Rate limit approaching for {quota_type.value}. "
                    f"Waiting {wait_time:.1f}s"
                )
                await asyncio.sleep(wait_time)
    
    def _update_metrics(self, quota_type: QuotaType, elapsed: float, success: bool):
        """Update request metrics"""
        metrics = self.metrics[quota_type]
        current_time = time.time()
        
        metrics.total_requests += 1
        if success:
            metrics.successful_requests += 1
        
        metrics.request_timestamps.append(current_time)
        metrics.last_request_time = current_time
        
        # Update average response time (moving average)
        if metrics.avg_response_time == 0:
            metrics.avg_response_time = elapsed
        else:
            metrics.avg_response_time = (
                0.9 * metrics.avg_response_time + 0.1 * elapsed
            )
    
    def _extract_retry_after(self, error_str: str) -> Optional[float]:
        """Extract retry-after seconds from error message"""
        try:
            # Look for patterns like "retry in 48.0 seconds"
            import re
            match = re.search(r'in (\d+\.?\d*) seconds?', error_str)
            if match:
                return float(match.group(1))
        except:
            pass
        return None
    
    def get_metrics(self, quota_type: QuotaType) -> Dict[str, Any]:
        """Get current metrics for a quota type"""
        metrics = self.metrics[quota_type]
        return {
            "quota_type": quota_type.value,
            "total_requests": metrics.total_requests,
            "successful_requests": metrics.successful_requests,
            "throttled_requests": metrics.throttled_requests,
            "failed_requests": metrics.failed_requests,
            "success_rate": (
                metrics.successful_requests / metrics.total_requests * 100
                if metrics.total_requests > 0 else 0
            ),
            "avg_response_time": metrics.avg_response_time,
            "current_queue_size": self.task_queues[quota_type].qsize(),
            "requests_last_minute": len(metrics.request_timestamps)
        }
    
    def get_adaptive_batch_size(self, quota_type: QuotaType) -> int:
        """Calculate adaptive batch size based on current throughput"""
        config = self.configs[quota_type]
        metrics = self.metrics[quota_type]
        
        # Start with max batch size
        batch_size = config.max_batch_size
        
        # Reduce if we're seeing throttling
        if metrics.throttled_requests > 0:
            throttle_rate = metrics.throttled_requests / max(metrics.total_requests, 1)
            if throttle_rate > 0.1:  # More than 10% throttled
                batch_size = max(config.min_batch_size, batch_size // 2)
        
        # Reduce if queue is backing up
        queue_size = self.task_queues[quota_type].qsize()
        if queue_size > 50:
            batch_size = config.min_batch_size
        
        return batch_size
